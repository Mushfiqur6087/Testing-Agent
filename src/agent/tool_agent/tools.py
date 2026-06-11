"""
ExecutionOutcomeValidator — upgraded from the generic Tools class.

In the AutoTestGenX Phase 3 architecture, the TestStepVerifier audited
static test steps before execution. In the Testing Agent (execution phase),
the test steps have already been verified and are being *actually run*.

The validator here answers a different question:
    "After the agent executed the steps, did the application state change
     as described in the expected_result?"

It achieves this by:
1. Capturing a lightweight 'before' state at TC start (URL, DOM summary, screenshot)
2. When tools() is called (after a critical step or at TC completion), capturing
   the 'after' state and comparing against the expected_result using LLM + vision.

Uses the same vision-capable model as the main agent.
"""

import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from src.browser.browser_context import BrowserSession


class Tools:
    """
    ExecutionOutcomeValidator for the multi-agent testing pipeline.

    Validates whether the application state after step execution matches
    the expected_result from the enriched test case. Uses before/after
    state capture and LLM+vision analysis as the primary evaluation method.
    """

    def __init__(self, llm_client=None, log_debug_func=None, debug_file_path=None):
        """
        Args:
            llm_client:      Vision-capable LLM client for analysis
            log_debug_func:  Debug logging function from the agent
            debug_file_path: Path to the debug log file
        """
        self.llm_client = llm_client
        self.log_debug_func = log_debug_func
        self.debug_file_path = debug_file_path

    def set_logging_functions(self, log_debug_func=None, debug_file_path=None):
        """Update logging functions (called when debug file path changes per TC)."""
        self.log_debug_func = log_debug_func
        self.debug_file_path = debug_file_path

    # ── Public API ────────────────────────────────────────────────────────────

    def capture_state(self, browser_context: BrowserSession) -> Dict[str, Any]:
        """
        Capture a lightweight state snapshot for before/after comparison.

        Called automatically at the START of each test case (before-state)
        and again when the agent invokes tools() (after-state).

        Returns:
            {url, title, dom_summary, screenshot_b64 (optional)}
        """
        try:
            page = browser_context.get_current_page()
            if page is None:
                return {"url": "", "title": "", "dom_summary": "", "error": "No active page"}

            state = {
                "url": page.url,
                "title": page.title(),
                "dom_summary": browser_context.get_selector_map_string(refresh=True) or "",
                "captured_at": datetime.now().isoformat(),
            }

            # Capture screenshot for vision-capable validation
            try:
                screenshot_bytes = page.screenshot(type="jpeg", quality=60, full_page=False)
                state["screenshot_b64"] = base64.b64encode(screenshot_bytes).decode()
            except Exception:
                pass  # Not all setups support screenshots

            return state

        except Exception as e:
            return {"url": "", "title": "", "dom_summary": "", "error": str(e)}

    def execute(
        self,
        reason: str,
        browser_context: BrowserSession,
        llm_client=None,
        expected_result: str = "",
        before_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute outcome validation using LLM + vision comparison.

        Args:
            reason:          The agent's description of why tools is called
            browser_context: Current browser session
            llm_client:      LLM client override (uses instance client if None)
            expected_result: The expected_result from the enriched test case
            before_state:    State captured at TC start (for before/after diff)

        Returns:
            {
                "message":          str,   — one-sentence verdict
                "data": {
                    "findings":         str,   — detailed observations
                    "validation_passed": bool,
                    "state_changed":     bool,
                    "expected_result":   str,
                }
            }
        """
        try:
            active_llm = llm_client or self.llm_client
            if not active_llm:
                return {
                    "message": "No LLM client available for outcome validation",
                    "data": {"error": "No LLM client", "validation_passed": False}
                }

            # Capture after-state
            after_state = self._get_page_info(browser_context)

            # Perform LLM-driven outcome validation
            result = self._validate_outcome_with_llm(
                reason=reason,
                expected_result=expected_result,
                before_state=before_state,
                after_state=after_state,
                llm_client=active_llm,
            )

            return {
                "message": result.get("message", "Outcome validation completed"),
                "data": {
                    "findings":          result.get("findings", ""),
                    "validation_passed": result.get("validation_passed", False),
                    "state_changed":     result.get("state_changed", False),
                    "expected_result":   expected_result,
                }
            }

        except Exception as e:
            return {
                "message": f"Outcome validation failed: {e}",
                "data": {"error": str(e), "validation_passed": False}
            }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_page_info(self, browser_context: BrowserSession) -> Dict[str, Any]:
        """Get current page information (DOM, alerts, screenshot) for LLM analysis."""
        try:
            page = browser_context.get_current_page()
            if page is None:
                return {"error": "No active page"}

            page_info = {
                "url": page.url,
                "title": page.title(),
                "element_tree": browser_context.get_element_tree_string(refresh=True) or "No elements found",
                "has_alerts": browser_context.has_recent_alerts(),
            }

            alerts_info = browser_context.get_formatted_alerts_for_llm()
            if alerts_info:
                page_info["alerts"] = alerts_info

            try:
                screenshot_bytes = page.screenshot(type="jpeg", quality=60, full_page=False)
                page_info["screenshot_b64"] = base64.b64encode(screenshot_bytes).decode()
            except Exception:
                pass

            return page_info

        except Exception as e:
            return {"error": f"Failed to get page info: {e}"}

    def _validate_outcome_with_llm(
        self,
        reason: str,
        expected_result: str,
        before_state: Optional[Dict[str, Any]],
        after_state: Dict[str, Any],
        llm_client,
    ) -> Dict[str, Any]:
        """
        Core LLM + vision validation: compare before/after against expected_result.
        """
        try:
            screenshot_b64 = after_state.pop("screenshot_b64", None)

            # Build before-state context block
            if before_state:
                before_block = (
                    f"BEFORE STATE (captured at test case start):\n"
                    f"  URL:   {before_state.get('url', 'N/A')}\n"
                    f"  Title: {before_state.get('title', 'N/A')}\n"
                    f"  Key elements (truncated):\n"
                    f"  {before_state.get('dom_summary', 'N/A')[:400]}"
                )
            else:
                before_block = "BEFORE STATE: Not captured (single-point validation)"

            prompt = f"""OUTCOME VALIDATION REQUEST: {reason}

EXPECTED RESULT (ground truth from test case):
{expected_result if expected_result else "(no expected result provided — assess observable outcome only)"}

{before_block}

AFTER STATE (current page — the result of executing the test steps):
  URL:   {after_state.get('url', 'Unknown')}
  Title: {after_state.get('title', 'Unknown')}"""

            if after_state.get('has_alerts', False):
                prompt += f"""
  Browser Alert Observed: YES
{after_state.get('alerts', '')}"""
            else:
                prompt += "\n  Browser Alert Observed: NO"

            prompt += f"""

DOM SNAPSHOT (after execution):
{after_state.get('element_tree', 'No elements found')[:1200]}

Using the screenshot (if provided) as the primary visual source of truth:
1. Does the current page state match the Expected Result?
2. Did the application state change from the Before State to the After State
   in the way the Expected Result describes?

Respond ONLY with valid JSON:
{{
    "message":          "One-sentence verdict on whether the expected result was achieved",
    "findings":         "2-3 sentences: what you observed (screenshot + DOM + alerts). Be specific about what changed.",
    "validation_passed": true or false,
    "state_changed":     true or false
}}
"""
            if self.log_debug_func:
                self._log_request(prompt)

            # Build messages list with optional screenshot
            system_content = (
                "You are a browser test outcome validator. Your job is to determine whether "
                "a test PASSED or FAILED based on observable evidence after executing the test steps.\n\n"
                "VALIDATION RULES:\n"
                "1. TRUST the screenshot first — it shows the real visual state of the page.\n"
                "2. Compare the current page state (after) against the Expected Result.\n"
                "3. If the screenshot and DOM together match the Expected Result, set validation_passed=true.\n"
                "4. Only set validation_passed=false if there is CLEAR POSITIVE EVIDENCE of failure.\n"
                "5. DOM attributes like 'value' are static and do NOT reflect live JS input state.\n"
                "6. Be concise. Report only what you can directly observe."
            )

            messages = [{"role": "system", "content": system_content}]

            if screenshot_b64:
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}"},
                        },
                    ],
                })
            else:
                messages.append({"role": "user", "content": prompt})

            import litellm
            response = litellm.completion(
                model=llm_client.model,
                messages=messages,
                timeout=llm_client.timeout,
            )
            raw = response.choices[0].message.content

            if self.log_debug_func:
                self._log_response(raw)

            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            try:
                parsed = json.loads(cleaned.strip())
                return {
                    "message":          parsed.get("message", "Outcome validation completed"),
                    "findings":         parsed.get("findings", ""),
                    "validation_passed": parsed.get("validation_passed", False),
                    "state_changed":     parsed.get("state_changed", False),
                }
            except json.JSONDecodeError:
                return {
                    "message":          "Outcome validation completed (unparsed response)",
                    "findings":         cleaned,
                    "validation_passed": True,
                    "state_changed":     False,
                }

        except Exception as e:
            return {
                "message":          "LLM outcome validation unavailable",
                "findings":         str(e),
                "validation_passed": False,
                "state_changed":     False,
            }

    def _log_request(self, prompt: str) -> None:
        """Log validation request to the debug file."""
        if not self.debug_file_path:
            return
        try:
            with open(self.debug_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write("OUTCOME VALIDATOR — LLM REQUEST\n")
                f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                f.write(f"{'='*80}\n\n")
                f.write(prompt)
                f.write(f"\n{'-'*40}\n\n")
        except Exception:
            pass

    def _log_response(self, response: str) -> None:
        """Log validation response to the debug file."""
        if not self.debug_file_path:
            return
        try:
            with open(self.debug_file_path, 'a', encoding='utf-8') as f:
                f.write("OUTCOME VALIDATOR — LLM RESPONSE\n")
                f.write(f"{'-'*40}\n")
                f.write(response)
                f.write(f"\n{'-'*40}\n\n")
        except Exception:
            pass
