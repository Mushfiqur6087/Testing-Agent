"""
Test Result Analyzer — post-task LLM verdict on whether a test passed or failed.
Enhanced for the multi-agent pipeline: incorporates outcome validation results,
before/after state snapshots, and enriched test case metadata in the analysis prompt.
"""

import json
from typing import Dict, Any, Optional, List
from src.agent.core_utils.llm import LLMClient
from src.agent.core_utils.memory import EnhancedMemory
from src.agent.core_utils.logging_utils import debug_logger


class TestResultAnalyzer:
    """
    Analyzes test execution memory and returns a PASSED/FAILED verdict.

    In the multi-agent pipeline, the analysis prompt is enriched with:
    - ExecutionOutcomeValidator results (from each tools() call)
    - Before/after state snapshots
    - The expected_result from the enriched test case as ground truth
    - The Phase 3 pre-audited verdict (surfaced as context, not the answer)
    """

    def __init__(self, llm_client: LLMClient, analyzer_llm_client: Optional[LLMClient] = None):
        """
        Args:
            llm_client:          Navigation LLM (used as fallback).
            analyzer_llm_client: Optional separate model for post-task reasoning.
        """
        self.llm = analyzer_llm_client or llm_client

    def analyze_test_execution(
        self,
        memory: EnhancedMemory,
        original_test_goal: str,
        expected_outcome: str,
        test_case_name: str = "test_case",
        task_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze test execution and generate comprehensive summary.

        Args:
            memory:            EnhancedMemory from the completed test case
            original_test_goal: The full structured goal block sent to the agent
            expected_outcome:  The expected_result from the enriched test case
            test_case_name:    Used for log file routing
            task_metadata:     Full enriched test case dict (optional but recommended)

        Returns:
            Dict with detailed test analysis including llm_analysis sub-dict
        """
        analysis_prompt = self._create_analysis_prompt(
            original_test_goal, expected_outcome, memory, task_metadata
        )

        try:
            llm_response = self.llm.ask(analysis_prompt)

            try:
                analysis = json.loads(llm_response)
            except json.JSONDecodeError:
                try:
                    if "```json" in llm_response:
                        start = llm_response.find("```json") + 7
                        end = llm_response.find("```", start)
                        analysis = json.loads(llm_response[start:end].strip())
                    else:
                        analysis = {"summary": llm_response}
                except json.JSONDecodeError:
                    analysis = {"summary": llm_response}

            result = {
                "original_goal":    original_test_goal,
                "expected_outcome": expected_outcome,
                "llm_analysis":     analysis,
            }

            # Attach Phase 3 metadata flags for thesis audit trail
            if task_metadata:
                result["tc_metadata"] = {
                    "tc_id":    task_metadata.get("tc_id", ""),
                    "module":   task_metadata.get("module", ""),
                    "verdict":  task_metadata.get("verdict", ""),   # Phase 3 pre-audited verdict
                    "priority": task_metadata.get("priority", ""),
                    "type":     task_metadata.get("type", ""),
                    "steps_adjusted": task_metadata.get("verdict") == "invalid_steps",
                }

            self._save_analysis_to_logs(result, test_case_name)
            return result

        except Exception as e:
            error_result = {
                "original_goal":    original_test_goal,
                "expected_outcome": expected_outcome,
                "llm_analysis":     {"error": f"Analysis failed: {str(e)}"},
            }
            self._save_analysis_to_logs(error_result, test_case_name)
            return error_result

    def _create_analysis_prompt(
        self,
        test_goal: str,
        expected_outcome: str,
        memory: EnhancedMemory,
        task_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create comprehensive analysis prompt from memory and enriched metadata."""

        # ── Phase 3 metadata context ──────────────────────────────────────────
        meta_block = ""
        if task_metadata:
            phase3_verdict = task_metadata.get("verdict", "unknown")
            steps_adjusted = phase3_verdict == "invalid_steps"
            meta_block = f"""
PHASE 3 PRE-AUDIT CONTEXT (from enriched dataset — for context only, reach your own conclusion):
  Module:          {task_metadata.get('module', 'N/A')}
  TC-ID:           {task_metadata.get('tc_id', 'N/A')}
  Type:            {task_metadata.get('type', 'N/A')}
  Priority:        {task_metadata.get('priority', 'N/A')}
  Phase 3 Verdict: {phase3_verdict}
  Steps Adjusted:  {"YES — steps were modified during Phase 3 verification" if steps_adjusted else "No"}
  Verifier Notes:  {task_metadata.get('notes', 'N/A')}
"""

        # ── Execution flow ────────────────────────────────────────────────────
        prompt = f"""You are analyzing a browser test execution. Be concise and direct.

ORIGINAL TEST GOAL:
{test_goal}

EXPECTED RESULT (ground truth):
{expected_outcome}
{meta_block}
EXECUTION FLOW:
"""
        for state in memory.llm_states:
            step_num = state.get("step_number")
            cs = state.get("current_state", {})
            prompt += f"\nStep {step_num}:\n"
            prompt += f"  Goal:               {cs.get('next_goal', 'N/A')}\n"
            prompt += f"  Previous Evaluation:{cs.get('evaluation_previous_goal', 'N/A')}\n"
            prompt += f"  Memory:             {cs.get('memory', 'N/A')}\n"

        # ── Outcome validations ───────────────────────────────────────────────
        if memory.outcome_validations:
            prompt += "\nEXECUTION OUTCOME VALIDATIONS (from ExecutionOutcomeValidator):\n"
            for ov in memory.outcome_validations:
                status = "✅ PASSED" if ov.get("validation_passed") else "❌ FAILED"
                changed = "YES" if ov.get("state_changed") else "NO"
                prompt += (
                    f"\n  Step {ov.get('step_number')} Validation: {status}\n"
                    f"  State Changed: {changed}\n"
                    f"  Findings: {ov.get('findings', 'N/A')}\n"
                    f"  Message:  {ov.get('message', 'N/A')}\n"
                )

        # ── Before/after snapshots ────────────────────────────────────────────
        before = memory.get_before_state()
        if before:
            prompt += f"""
STATE TRANSITION EVIDENCE:
  Before URL:  {before.get('url', 'N/A')}
  Before Title:{before.get('title', 'N/A')}
"""
        # ── Legacy tool outputs (backward compat) ─────────────────────────────
        if memory.tool_outputs and not memory.outcome_validations:
            prompt += "\nTOOL VALIDATIONS:\n"
            for output in memory.tool_outputs:
                step_num = output.get("step_number")
                td = output.get("tool_output", {})
                prompt += (
                    f"\nStep {step_num} Tool Result:\n"
                    f"  Validation Passed: {td.get('validation_passed')}\n"
                    f"  Findings: {td.get('findings', 'N/A')}\n"
                    f"  Reason: {td.get('request_reason', 'N/A')}\n"
                )

        # ── Planning notes ────────────────────────────────────────────────────
        if memory.compliance_notes:
            prompt += f"\nPLANNING NOTES:\n"
            for note in memory.compliance_notes:
                prompt += f"  {note}\n"

        prompt += """
Please analyze this and respond in JSON format:

{
  "test_result": "PASSED" | "FAILED",
  "success": true | false,
  "summary": "Brief narrative (2-4 lines) describing what the agent did and why it passed or failed",
  "errors": "Describe any errors encountered, or 'None' if there were none"
}

Focus on whether the Expected Result was achieved. Use the Outcome Validation evidence as primary signal.
"""
        return prompt

    def _save_analysis_to_logs(
        self,
        analysis_result: Dict[str, Any],
        test_case_name: str = "test_case",
    ) -> None:
        """Save analysis result to the test case subfolder."""
        try:
            filepath = debug_logger.get_analysis_file_path(test_case_name)
            with open(filepath, 'w') as f:
                json.dump(analysis_result, f, indent=2)
        except Exception as e:
            print(f"Failed to save analysis to logs: {e}")
