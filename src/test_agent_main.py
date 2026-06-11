# filepath: /home/mushfiqur/Documents/Testing-Agent/src/test_agent_main.py
import os
import sys
import json
import re
import signal
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

# Load API keys from env/.env automatically
_ENV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "env", ".env"
)
load_dotenv(_ENV_FILE)

# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.test_agent import TestAgent
from src.agent.core_utils.logging_utils import debug_logger
from src.agent.planning_agent.traversal_planner import TraversalPlanner
from src.agent.planning_agent.adaptive_planner import AdaptivePlanner


def _sigalrm_handler(signum, frame):
    """Raised in the main thread when a per-test wall-clock timeout fires."""
    raise TimeoutError("Test case wall-clock timeout")


def _slugify(text: str) -> str:
    """Convert a string to a safe directory/file name slug."""
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text.strip())
    return text[:60]


class TestAgentMain:
    """
    Main orchestrator that runs the full multi-agent testing pipeline.

    Uses a SINGLE persistent TestAgent (one browser, one LLM) across all
    test cases in the run. Between test cases the AdaptivePlanner checks
    whether the next TC's prerequisites are still satisfied and proposes
    recovery if the session has drifted.
    """

    def __init__(self, model: str = "openai/gpt-5-mini", provider: str = None,
                 max_actions: int = 15, debug: bool = False, headless: bool = True,
                 analyzer_model: str = None, analyzer_provider: str = None,
                 test_timeout: int = 300):
        self.model = model
        self.provider = provider
        self.max_actions = max_actions
        self.debug = debug
        self.headless = headless
        # Analyzer uses same model (vision-capable) — no separate cheap model
        self.analyzer_model = analyzer_model or model
        self.analyzer_provider = analyzer_provider or provider
        self.test_timeout = test_timeout

        self._shared_agent: TestAgent = None
        self._adaptive_planner: AdaptivePlanner = None

        self._run_summary: Dict[str, Any] = {
            "run_id":       debug_logger.get_run_dir().name,
            "started_at":   datetime.now().isoformat(),
            "model":        model,
            "provider":     provider,
            "total":        0,
            "passed":       0,
            "failed":       0,
            "error":        0,
            "skipped":      0,
            "test_cases":   [],
        }

    # ── Run summary helpers ──────────────────────────────────────────────────

    def _record_result(
        self,
        test_name: str,
        result: str,
        analysis: Dict[str, Any],
        task_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append the result of one test case to the run summary and save it.

        result: "PASSED" | "FAILED" | "ERROR" | "SKIPPED"
        """
        entry: Dict[str, Any] = {
            "test_name":   test_name,
            "result":      result,
            "finished_at": datetime.now().isoformat(),
        }

        if result == "SKIPPED":
            entry["skip_reason"] = (
                task_metadata.get("drop_reason", "") if task_metadata else "dropped=true"
            )
        else:
            llm = analysis.get("llm_analysis", {})
            entry["llm_verdict"] = llm.get("test_result", result)
            entry["summary"]     = llm.get("summary", "")
            entry["errors"]      = llm.get("errors", "")

        # Flag TCs whose steps were adjusted during Phase 3 verification
        if task_metadata and task_metadata.get("verdict") == "invalid_steps":
            entry["phase3_note"] = (
                "⚠ Steps were adjusted during Phase 3 verification (verdict: invalid_steps). "
                "Execution used the adjusted steps."
            )

        self._run_summary["test_cases"].append(entry)
        self._run_summary["total"] += 1

        if result == "PASSED":
            self._run_summary["passed"] += 1
        elif result == "FAILED":
            self._run_summary["failed"] += 1
        elif result == "SKIPPED":
            self._run_summary["skipped"] += 1
        else:
            self._run_summary["error"] += 1

        self._run_summary["finished_at"] = datetime.now().isoformat()
        self._save_run_summary()

    def _save_run_summary(self) -> None:
        """Write the run summary JSON to the run-level directory."""
        summary_path = debug_logger.get_run_dir() / "test_run_summary.json"
        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(self._run_summary, f, indent=2)
        except Exception as e:
            print(f"  [warn] Could not write run summary: {e}")

    # ── Test case loading ────────────────────────────────────────────────────

    # Required fields for the new enriched format
    _ENRICHED_REQUIRED = {"tc_id", "module", "title", "steps", "expected_result"}

    def load_test_cases(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Load test cases from a JSON file.

        Supports two formats:
          • New enriched format: {"test_cases": [...]}   (from AutoTestGenX Phase 3)
          • Legacy format:       [...]                   (backward compat)

        For enriched format:
          - Filters dropped=true TCs (recorded as SKIPPED in the run summary)
          - Validates required fields
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Test cases file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            raw = json.load(f)

        # ── Format detection ──────────────────────────────────────────────────
        if isinstance(raw, dict) and "test_cases" in raw:
            # New enriched format
            all_tcs = raw["test_cases"]
            active, dropped = [], []
            for tc in all_tcs:
                if tc.get("dropped", False):
                    dropped.append(tc)
                else:
                    active.append(tc)

            if dropped:
                print(f"  ⏭  {len(dropped)} test case(s) skipped (dropped=true):")
                for tc in dropped:
                    print(f"     [{tc.get('module','?')} / {tc.get('tc_id','?')}] "
                          f"{tc.get('title','')[:60]}")
                    # Record SKIPPED entries in the run summary immediately
                    self._record_result(
                        test_name=_slugify(
                            f"{tc.get('module','unknown')}_{tc.get('tc_id','unknown')}"
                        ),
                        result="SKIPPED",
                        analysis={},
                        task_metadata=tc,
                    )

            # Validate enriched TCs
            for i, tc in enumerate(active):
                missing = self._ENRICHED_REQUIRED - set(tc.keys())
                if missing:
                    raise ValueError(
                        f"enriched test_cases[{i}] is missing required fields: {missing}"
                    )

            format_label = "enriched"
            test_cases = active

        elif isinstance(raw, list):
            # Legacy flat format — validate old schema
            _LEGACY_REQUIRED = {"test_name", "steps_or_input", "expected_outcome"}
            for i, tc in enumerate(raw):
                missing = _LEGACY_REQUIRED - set(tc.keys())
                if missing:
                    raise ValueError(
                        f"test_cases[{i}] is missing required fields: {missing}. "
                        f"Got keys: {set(tc.keys())}"
                    )
            format_label = "legacy"
            test_cases = raw
        else:
            raise ValueError(
                f"Unrecognised test case file format in {filepath}. "
                "Expected either a JSON object with 'test_cases' key or a JSON array."
            )

        print(f"  📂 Loaded {len(test_cases)} test case(s) from {filepath} [{format_label} format]")
        return test_cases

    # ── Goal block composer (enriched format only) ───────────────────────────

    @staticmethod
    def _build_goal_block(tc: Dict[str, Any]) -> str:
        """
        Compose a structured goal block from all enriched test case fields.
        This is the user_goal string sent to the InteractionAgent.
        """
        steps_text = "\n".join(
            f"  {s}" for s in tc.get("steps", [])
        )
        test_data = tc.get("test_data", {})
        test_data_text = (
            json.dumps(test_data, indent=2) if test_data else "(no test data)"
        )

        return (
            f"[Module: {tc.get('module','?')} | {tc.get('tc_id','?')} "
            f"| Type: {tc.get('type','?')} | Priority: {tc.get('priority','?')}]\n"
            f"Title: {tc.get('title','')}\n\n"
            f"▶ Start URL:    {tc.get('direct_link','(not specified)')}\n"
            f"▶ Requires Auth: {'Yes' if tc.get('requires_auth') else 'No'}\n"
            f"▶ Test Data:\n{test_data_text}\n\n"
            f"Preconditions:\n  {tc.get('preconditions','(none)')}\n\n"
            f"Steps to Execute:\n{steps_text}\n\n"
            f"Expected Result (what must be true AFTER execution):\n"
            f"  {tc.get('expected_result','')}\n\n"
            f"Notes from prior verification:\n"
            f"  {tc.get('notes','(none)')}"
        )

    # ── Single test case execution ───────────────────────────────────────────

    def execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test case using the shared TestAgent.
        Supports both enriched and legacy formats.
        """
        is_enriched = "tc_id" in test_case

        if is_enriched:
            test_name     = _slugify(f"{test_case.get('module','unknown')}_{test_case.get('tc_id','tc')}")
            user_goal     = self._build_goal_block(test_case)
            expected_outcome = test_case.get("expected_result", "")
            task_metadata = test_case
        else:
            # Legacy format
            test_name        = test_case.get("test_name", "test_case")
            steps_or_input   = test_case.get("steps_or_input", "")
            expected_outcome = test_case.get("expected_outcome", "")
            user_goal = (
                steps_or_input
                + "\n DETERMINE whether this test can be successfully executed given the "
                "current requirements and implementation, or if there are any errors, "
                "inconsistencies, or missing validations in the requirements or the form itself."
            )
            task_metadata = None

        analysis:    Dict[str, Any] = {}
        result_str = "ERROR"

        try:
            analysis = self._shared_agent.execute_plan(
                user_goal,
                expected_outcome,
                test_case_name=test_name,
                task_metadata=task_metadata,
            )

            verdict    = analysis.get("llm_analysis", {}).get("test_result", "").upper()
            result_str = "PASSED" if verdict == "PASSED" else "FAILED"

            status_icon = "✅" if result_str == "PASSED" else "❌"
            print(f"\n  {status_icon} [{test_name}]: {result_str}")
            return analysis

        except Exception as e:
            print(f"\n  ❌ [{test_name}] raised an exception: {e}")
            analysis = {"llm_analysis": {"error": str(e)}}
            raise

        finally:
            self._record_result(test_name, result_str, analysis, task_metadata)

    # ── Full run orchestration ───────────────────────────────────────────────

    def execute_all_test_cases(self, test_cases: List[Dict[str, Any]]) -> None:
        """
        Execute all test cases sequentially with a single shared browser session.

        Pipeline:
          1. TraversalPlanner orders TCs (public → auth → destructive)
          2. For each TC:
             a. AdaptivePlanner checks prerequisites; performs recovery if needed
             b. Agent executes the structured goal block
             c. Results recorded in run summary
        """
        if not test_cases:
            print("No test cases to execute.")
            return

        is_enriched = "tc_id" in test_cases[0]

        # ── TraversalPlanner (enriched format only) ────────────────────────
        if is_enriched:
            planner = TraversalPlanner()
            test_cases = planner.plan(test_cases)

        first_name = (
            _slugify(f"{test_cases[0].get('module','unknown')}_{test_cases[0].get('tc_id','tc')}")
            if is_enriched
            else test_cases[0].get("test_name", "test_case")
        )

        self._shared_agent = TestAgent(
            model=self.model,
            provider=self.provider,
            max_actions=self.max_actions,
            debug=self.debug,
            headless=self.headless,
            test_case_name=first_name,
            analyzer_model=self.analyzer_model,
            analyzer_provider=self.analyzer_provider,
        )
        self._shared_agent.initialize()

        # AdaptivePlanner uses the same LLM as the main agent
        self._adaptive_planner = AdaptivePlanner(self._shared_agent.llm)

        print(f"  🌐 Browser session started (shared across all {len(test_cases)} test cases)")

        total = len(test_cases)
        try:
            for i, test_case in enumerate(test_cases, 1):
                name = (
                    _slugify(f"{test_case.get('module','unknown')}_{test_case.get('tc_id','tc')}")
                    if is_enriched
                    else test_case.get("test_name", f"test_{i}")
                )
                print(f"\n{'─' * 60}")
                print(f"  Executing Test Case {i}/{total}: {name}")
                if is_enriched:
                    print(f"  [{test_case.get('priority','?')}] "
                          f"{test_case.get('module','?')} / {test_case.get('tc_id','?')} — "
                          f"{test_case.get('title','')[:55]}")
                print(f"{'─' * 60}")

                # ── AdaptivePlanner inter-test check ───────────────────────
                if i > 1 and is_enriched:
                    prior_summary  = self._build_prior_context()
                    current_url    = ""
                    current_dom    = ""
                    try:
                        page = self._shared_agent.browser_controller.browser_context.get_current_page()
                        if page:
                            current_url = page.url
                        current_dom = (
                            self._shared_agent.browser_controller.browser_context
                            .get_selector_map_string(refresh=False) or ""
                        )
                    except Exception:
                        pass

                    eval_result = self._adaptive_planner.evaluate_next(
                        next_tc=test_case,
                        current_url=current_url,
                        current_dom_summary=current_dom[:600],
                        prior_results=self._run_summary["test_cases"],
                    )

                    note = eval_result.get("note", "")
                    if note:
                        print(f"  🧭 AdaptivePlanner: {note}")

                    # Perform recovery navigation if needed
                    if eval_result.get("replan_needed") and eval_result.get("recovery_url"):
                        recovery_url = eval_result["recovery_url"]
                        print(f"  🔄 Recovering: navigating to {recovery_url}")
                        try:
                            self._shared_agent.browser_controller.navigate_to(recovery_url)
                        except Exception as nav_err:
                            print(f"  [warn] Recovery navigation failed: {nav_err}")

                    # Add planning note to next TC's memory
                    self._shared_agent.agent.prepare_for_next_task(name, prior_summary)
                    if note:
                        self._shared_agent.agent.memory.add_compliance_note(note)

                elif i > 1:
                    # Legacy format — simple soft reset
                    prior_summary = self._build_prior_context()
                    self._shared_agent.prepare_for_next_task(name, prior_summary)

                # ── Execute test case ──────────────────────────────────────
                try:
                    if self.test_timeout > 0:
                        old_handler = signal.signal(signal.SIGALRM, _sigalrm_handler)
                        signal.alarm(self.test_timeout)
                        try:
                            self.execute_test_case(test_case)
                        except TimeoutError:
                            print(f"  ⏰ [{name}] timed out after {self.test_timeout}s.")
                            self._record_result(name, "ERROR",
                                                {"llm_analysis": {"error": "Timeout"}},
                                                test_case if is_enriched else None)
                        finally:
                            signal.alarm(0)
                            signal.signal(signal.SIGALRM, old_handler)
                    else:
                        self.execute_test_case(test_case)
                except Exception:
                    pass  # Error recorded in _record_result; continue with next

        finally:
            self._shared_agent.cleanup()
            print("  🛑 Browser session closed.")

        # Final summary
        s = self._run_summary
        print(f"\n{'═' * 60}")
        print(f"  Run complete:")
        print(f"    ✅ Passed:  {s['passed']}")
        print(f"    ❌ Failed:  {s['failed']}")
        print(f"    💥 Error:   {s['error']}")
        print(f"    ⏭  Skipped: {s['skipped']}")
        print(f"    Total:    {s['total']}")
        print(f"  Summary → {debug_logger.get_run_dir() / 'test_run_summary.json'}")
        print(f"{'═' * 60}")

    def _build_prior_context(self) -> str:
        """Build a human-readable summary of completed test cases for the LLM."""
        lines = []
        for entry in self._run_summary["test_cases"]:
            if entry.get("result") == "SKIPPED":
                continue
            verdict = entry.get("result", "UNKNOWN")
            name    = entry["test_name"]
            summary = entry.get("summary", "")[:200]
            lines.append(f"- [{verdict}] {name}: {summary}")
        return "\n".join(lines) if lines else ""


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Testing Agent — AI-powered browser test automation (multi-agent pipeline)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  # Run enriched SwagLabs dataset
  python -m src.test_agent_main --dataset dataset/enriched_test_cases_swaglab.json \\
    --model gemini-2.0-flash --provider gemini

  # Run enriched ParaBank dataset
  python -m src.test_agent_main --dataset dataset/enriched_test_cases_parabank.json \\
    --model gpt-4o --provider openai

  # Legacy format (backward compat)
  python -m src.test_agent_main --test-file test_cases/test_cases.json
        """,
    )
    parser.add_argument(
        "--model", type=str, default="openai/gpt-5-mini",
        help="LiteLLM model string, e.g. openai/gpt-5-mini, anthropic/claude-sonnet-4-5, "
             "gemini/gemini-2.0-flash, openrouter/meta-llama/llama-3.1-8b-instruct "
             "(default: openai/gpt-5-mini)",
    )
    parser.add_argument(
        "--provider", type=str, default=None,
        help="Optional provider prefix (e.g. openai, anthropic, gemini). "
             "Only needed if --model does not already contain a provider prefix.",
    )
    parser.add_argument(
        "--max-actions", type=int, default=15,
        help="Maximum browser actions per test case (default: 15)",
    )
    parser.add_argument(
        "--dataset", type=str, default=None,
        help="Path to an enriched test case JSON file (new format). "
             "Default: dataset/enriched_test_cases_swaglab.json",
    )
    parser.add_argument(
        "--test-file", type=str, default=None,
        help="Path to a legacy test_cases.json (old flat format). "
             "Takes precedence over --dataset if both specified.",
    )
    parser.add_argument(
        "--no-headless", dest="headless", action="store_false", default=True,
        help="Show the browser window (default: headless / invisible)",
    )
    parser.add_argument(
        "--debug", action="store_true", default=True,
        help="Enable debug logging (default: True)",
    )
    parser.add_argument(
        "--test-timeout", type=int, default=300,
        help="Max seconds per test case before it is killed (0 = no limit, default: 300)",
    )
    return parser.parse_args()


def main():
    """Entry point — parses CLI args and runs the multi-agent pipeline."""
    args = parse_args()

    # Resolve test file path — --test-file (legacy) takes precedence over --dataset
    if args.test_file:
        test_cases_file = args.test_file
    elif args.dataset:
        test_cases_file = args.dataset
    else:
        # Default to enriched SwagLabs dataset
        test_cases_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "dataset", "enriched_test_cases_swaglab.json",
        )

    print(f"🤖 Testing Agent — Multi-Agent Pipeline")
    print(f"   Provider : {args.provider}")
    print(f"   Model    : {args.model}")
    print(f"   Headless : {args.headless}")
    print(f"   Test file: {test_cases_file}")
    print()

    main_agent = TestAgentMain(
        model=args.model,
        provider=args.provider,
        max_actions=args.max_actions,
        debug=args.debug,
        headless=args.headless,
        test_timeout=args.test_timeout,
    )

    try:
        test_cases = main_agent.load_test_cases(test_cases_file)
        main_agent.execute_all_test_cases(test_cases)
    except Exception:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()