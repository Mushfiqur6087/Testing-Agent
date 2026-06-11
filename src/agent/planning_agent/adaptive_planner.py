"""
AdaptivePlanner — Phase 3 Step 5 analog for the Testing Agent.

Called between test cases to check whether the next TC's prerequisites
are reachable given the current browser state and prior test results.

If the environment has changed unexpectedly (e.g., a logout TC ran early,
a prior test left the browser on an unexpected page, or authentication was
lost), the planner proposes a recovery action so the pipeline can self-heal
without manual intervention.

Uses the same vision-capable LLM as the main agent — no separate model.
"""

import json
import os
import sys
from typing import List, Dict, Any, Optional

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, PROJECT_ROOT)

from src.agent.core_utils.llm import LLMClient


class AdaptivePlanner:
    """
    Inter-test prerequisite checker and recovery planner.

    Mirrors the NavigationPlanner's step-advisor role from AutoTestGenX
    Phase 3, Step 5, which re-evaluates remaining goals against the live
    DOM state after each module is audited and autonomously replans if the
    environment has drifted.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def evaluate_next(
        self,
        next_tc: Dict[str, Any],
        current_url: str,
        current_dom_summary: str,
        prior_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate whether the prerequisites for the next test case are met.

        Args:
            next_tc:            The enriched test case dict that will run next.
            current_url:        The browser's current URL after the last test.
            current_dom_summary: A short text summary of current interactive elements.
            prior_results:      List of completed test result dicts from the run summary.

        Returns:
            {
                "proceed":         bool   — True if safe to start next TC immediately,
                "replan_needed":   bool   — True if recovery action is required,
                "recovery_action": str|None — e.g. "navigate_to_login", "navigate_to_base_url",
                "recovery_url":    str|None — URL to navigate to for recovery,
                "note":            str    — Human-readable explanation for the run log
            }
        """
        prompt = self._build_prompt(next_tc, current_url, current_dom_summary, prior_results)

        try:
            raw = self.llm.ask(prompt)
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            result = json.loads(cleaned.strip())
            return {
                "proceed":         result.get("proceed", True),
                "replan_needed":   result.get("replan_needed", False),
                "recovery_action": result.get("recovery_action", None),
                "recovery_url":    result.get("recovery_url", None),
                "note":            result.get("note", ""),
            }
        except Exception as e:
            # On any error, default to proceeding (don't block execution)
            return {
                "proceed":         True,
                "replan_needed":   False,
                "recovery_action": None,
                "recovery_url":    None,
                "note":            f"AdaptivePlanner evaluation failed ({e}); defaulting to proceed.",
            }

    def _build_prompt(
        self,
        next_tc: Dict[str, Any],
        current_url: str,
        current_dom_summary: str,
        prior_results: List[Dict[str, Any]],
    ) -> str:
        """Build the evaluation prompt for the LLM."""
        # Summarise the last 3 prior results for context
        recent_results = prior_results[-3:] if len(prior_results) >= 3 else prior_results
        results_text = "\n".join(
            f"  - [{r.get('result', 'UNKNOWN')}] {r.get('test_name', '?')}: "
            f"{r.get('summary', '')[:120]}"
            for r in recent_results
        ) or "  (no prior results)"

        requires_auth = next_tc.get("requires_auth", False)
        preconditions = next_tc.get("preconditions", "Not specified")
        direct_link = next_tc.get("direct_link", "Not specified")
        module = next_tc.get("module", "Unknown")
        tc_id = next_tc.get("tc_id", "?")

        return f"""You are an inter-test prerequisite advisor for a browser test automation pipeline.

NEXT TEST CASE TO RUN:
  Module:       {module}
  TC-ID:        {tc_id}
  Requires Auth: {"Yes" if requires_auth else "No"}
  Start URL:    {direct_link}
  Preconditions: {preconditions}

CURRENT BROWSER STATE:
  URL: {current_url}
  Interactive Elements Summary:
{current_dom_summary[:600] if current_dom_summary else "  (not available)"}

RECENT TEST RESULTS:
{results_text}

TASK:
Determine if the browser environment is in a suitable state to immediately
start the next test case, or if a recovery action is needed first.

Consider:
1. If the next TC requires auth (requires_auth=Yes) but the current page appears
   to be a login page (unauthenticated), recovery is needed.
2. If the last test was a Logout or Reset App State and the next TC requires auth,
   the agent will need to re-authenticate.
3. If the current URL is on a completely unrelated domain or error page, navigate
   to the Start URL first.
4. If prerequisites seem already met (e.g., already logged in, on a compatible page),
   proceed directly.

Respond ONLY with valid JSON — no markdown, no explanation outside the JSON:
{{
  "proceed":         true | false,
  "replan_needed":   true | false,
  "recovery_action": "none" | "navigate_to_login" | "navigate_to_base_url" | "navigate_to_start_url",
  "recovery_url":    null | "<URL to navigate to>",
  "note":            "One sentence explaining the decision"
}}
"""
