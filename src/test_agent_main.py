# filepath: /home/mushfiqur/Documents/Testing-Agent/src/test_agent_main.py
import os
import sys
import json
import signal
import argparse
from datetime import datetime
from typing import List, Dict, Any
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


def _sigalrm_handler(signum, frame):
    """Raised in the main thread when a per-test wall-clock timeout fires."""
    raise TimeoutError("Test case wall-clock timeout")


class TestAgentMain:
    """
    Main agent class that orchestrates test execution.
    Uses a SINGLE persistent TestAgent (one browser, one LLM client) across
    all test cases in the run.
    """

    def __init__(self, model: str = "gemini-2.0-flash", provider: str = "gemini",
                 max_actions: int = 15, debug: bool = False, headless: bool = True,
                 analyzer_model: str = None, analyzer_provider: str = None,
                 test_timeout: int = 300):
        self.model = model
        self.provider = provider
        self.max_actions = max_actions
        self.debug = debug
        self.headless = headless
        self.analyzer_model = analyzer_model
        self.analyzer_provider = analyzer_provider
        self.test_timeout = test_timeout  # seconds per test case (0 = no limit)

        # The shared agent — initialized lazily in execute_all_test_cases
        self._shared_agent: TestAgent = None

        # Cumulative run summary — persisted to disk after every test case
        self._run_summary: Dict[str, Any] = {
            "run_id": debug_logger.get_run_dir().name,
            "started_at": datetime.now().isoformat(),
            "model": model,
            "provider": provider,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "error": 0,
            "test_cases": [],
        }

    # ------------------------------------------------------------------
    # Run summary helpers
    # ------------------------------------------------------------------
    def _record_result(self, test_name: str, result: str, analysis: Dict[str, Any]) -> None:
        """
        Append the result of one test case to the run summary and save it.

        result: "PASSED" | "FAILED" | "ERROR"
        """
        entry = {
            "test_name": test_name,
            "result": result,
            "finished_at": datetime.now().isoformat(),
            "llm_verdict": analysis.get("llm_analysis", {}).get("test_result", result),
            "summary": analysis.get("llm_analysis", {}).get("summary", ""),
            "errors": analysis.get("llm_analysis", {}).get("errors", ""),
        }
        self._run_summary["test_cases"].append(entry)
        self._run_summary["total"] += 1
        if result == "PASSED":
            self._run_summary["passed"] += 1
        elif result == "FAILED":
            self._run_summary["failed"] += 1
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

    # ------------------------------------------------------------------
    def generate_test_cases(self, test_case_description: str) -> List[Dict[str, Any]]:
        """
        Wrap a single test description as a single test case, ready for execution.
        No LLM expansion — the description is used as-is.
        """
        if not test_case_description.strip():
            raise ValueError("Test case description cannot be empty")

        return [
            {
                "test_name": "test_case_1",
                "steps_or_input": test_case_description.strip(),
                "expected_outcome": "",
                "reason_for_failure": "",
            }
        ]

    # Required fields every test case must have
    _REQUIRED_FIELDS = {"test_name", "steps_or_input", "expected_outcome"}

    def load_test_cases(self, filepath: str) -> List[Dict[str, Any]]:
        """Load and validate test cases from a JSON file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Test cases file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)

        if not isinstance(test_cases, list):
            raise ValueError(f"Expected a JSON array in {filepath}")

        # Schema validation — fail early with a clear message
        for i, tc in enumerate(test_cases):
            missing = self._REQUIRED_FIELDS - set(tc.keys())
            if missing:
                raise ValueError(
                    f"test_cases[{i}] is missing required fields: {missing}. "
                    f"Got keys: {set(tc.keys())}"
                )
            if not tc.get("test_name", "").strip():
                raise ValueError(f"test_cases[{i}]: 'test_name' must not be empty.")

        print(f"Loaded {len(test_cases)} test case(s) from {filepath}")
        return test_cases

    def execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test case using the shared TestAgent.
        The browser and LLM session persist; only per-task memory is reset.
        """
        test_name = test_case.get('test_name', 'test_case')
        steps_or_input = test_case.get('steps_or_input', '')
        expected_outcome = test_case.get('expected_outcome', '')

        user_goal = (
            steps_or_input
            + "\n DETERMINE whether this test can be successfully executed given the "
            "current requirements and implementation, or if there are any errors, "
            "inconsistencies, or missing validations in the requirements or the form itself."
        )

        analysis: Dict[str, Any] = {}
        result_str = "ERROR"

        try:
            analysis = self._shared_agent.execute_plan(
                user_goal, expected_outcome, test_case_name=test_name
            )

            verdict = analysis.get("llm_analysis", {}).get("test_result", "").upper()
            result_str = "PASSED" if verdict == "PASSED" else "FAILED"

            status_icon = "✅" if result_str == "PASSED" else "❌"
            print(f"\n  {status_icon} Test Case '{test_name}': {result_str}")
            return analysis

        except Exception as e:
            print(f"\n  ❌ Test Case '{test_name}' raised an exception: {e}")
            analysis = {"llm_analysis": {"error": str(e)}}
            raise

        finally:
            self._record_result(test_name, result_str, analysis)

    def execute_all_test_cases(self, test_cases: List[Dict[str, Any]]) -> None:
        """Execute all test cases sequentially with a single shared browser session."""
        if not test_cases:
            print("No test cases to execute.")
            return

        # Build the first test case name so the shared agent can point its
        # debug log at the right subfolder from the very first step.
        first_name = test_cases[0].get("test_name", "test_case")
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
        print(f"  🌐 Browser session started (shared across all {len(test_cases)} test cases)")

        total = len(test_cases)
        try:
            for i, test_case in enumerate(test_cases, 1):
                name = test_case.get("test_name", f"test_{i}")
                print(f"\n{'─' * 60}")
                print(f"  Executing Test Case {i}/{total}: {name}")
                print(f"{'─' * 60}")

                # Before each test (except the first which is already set up),
                # soft-reset the agent with a summary of prior results.
                if i > 1:
                    prior_summary = self._build_prior_context()
                    self._shared_agent.prepare_for_next_task(name, prior_summary)

                try:
                    if self.test_timeout > 0:
                        # signal.alarm only works on Linux/macOS main thread —
                        # safe with Playwright's sync (greenlet) API.
                        old_handler = signal.signal(signal.SIGALRM, _sigalrm_handler)
                        signal.alarm(self.test_timeout)
                        try:
                            self.execute_test_case(test_case)
                        except TimeoutError:
                            print(f"  ⏰ Test Case '{name}' timed out after {self.test_timeout}s.")
                            self._record_result(name, "ERROR",
                                               {"llm_analysis": {"error": "Timeout"}})
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
        print(f"  Run complete: {s['passed']} passed / {s['failed']} failed / {s['error']} error  (total {s['total']})")
        print(f"  Summary → {debug_logger.get_run_dir() / 'test_run_summary.json'}")
        print(f"{'═' * 60}")

    def _build_prior_context(self) -> str:
        """Build a human-readable summary of completed test cases for the LLM."""
        lines = []
        for entry in self._run_summary["test_cases"]:
            verdict = entry.get("result", "UNKNOWN")
            name = entry["test_name"]
            summary = entry.get("summary", "")[:200]  # keep it brief
            lines.append(f"- [{verdict}] {name}: {summary}")
        return "\n".join(lines) if lines else ""


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Testing Agent — AI-powered browser test automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  python -m src.test_agent_main --model gpt-5-mini --provider openai
  python -m src.test_agent_main --model claude-sonnet-4-20250514 --provider anthropic
  python -m src.test_agent_main --model gemini-2.0-flash --provider gemini
  python -m src.test_agent_main --model google/gemini-flash-1.5 --provider openrouter
        """,
    )
    parser.add_argument(
        "--model", type=str, default="gemini-2.0-flash",
        help="Model name (default: gemini-2.0-flash)",
    )
    parser.add_argument(
        "--provider", type=str, default="gemini",
        help="LLM provider: openai, anthropic, gemini, openrouter, etc. (default: gemini)",
    )
    parser.add_argument(
        "--max-actions", type=int, default=10,
        help="Maximum browser actions per test case (default: 10)",
    )
    parser.add_argument(
        "--test-file", type=str, default=None,
        help="Path to test_cases.json (default: test_cases/test_cases.json)",
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
        "--analyzer-model", type=str, default=None,
        help="Separate (cheaper) model for post-task analysis. Defaults to --model.",
    )
    parser.add_argument(
        "--analyzer-provider", type=str, default=None,
        help="Provider for --analyzer-model. Defaults to --provider.",
    )
    parser.add_argument(
        "--test-timeout", type=int, default=300,
        help="Max seconds per test case before it is killed (0 = no limit, default: 300)",
    )
    return parser.parse_args()


def main():
    """Entry point — parses CLI args and runs the agent."""
    args = parse_args()

    # Resolve test file path
    if args.test_file:
        test_cases_file = args.test_file
    else:
        test_cases_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "test_cases", "test_cases.json",
        )

    print(f"🤖 Testing Agent")
    print(f"   Provider : {args.provider}")
    print(f"   Model    : {args.model}")
    print(f"   Headless : {args.headless}")
    print(f"   Test file: {test_cases_file}")
    if args.analyzer_model:
        print(f"   Analyzer : {args.analyzer_provider or args.provider}/{args.analyzer_model}")
    print()

    main_agent = TestAgentMain(
        model=args.model,
        provider=args.provider,
        max_actions=args.max_actions,
        debug=args.debug,
        headless=args.headless,
        analyzer_model=args.analyzer_model,
        analyzer_provider=args.analyzer_provider,
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