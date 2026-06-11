"""
Enhanced Memory System for Testing Agent (Multi-Agent Pipeline).
Stores LLM states, tool outputs, execution outcome validations,
and before/after state snapshots per test-case task.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class EnhancedMemory:
    """
    Memory system that stores LLM states and tool outputs per test-case task.
    Extended to support the multi-agent pipeline with outcome validations
    and before/after state snapshots for state-transition proof.
    """

    def __init__(self, debug_file_path: Optional[str] = None, max_context_chars: int = 800):
        self.llm_states: list = []
        self.tool_outputs: list = []

        # ── New stores for multi-agent pipeline ──────────────────────────────
        # Before/After state snapshots captured around state-changing actions
        self.state_snapshots: List[Dict[str, Any]] = []
        # ExecutionOutcomeValidator results from each tools() call
        self.outcome_validations: List[Dict[str, Any]] = []
        # Free-text compliance/planning notes from AdaptivePlanner
        self.compliance_notes: List[str] = []
        # ─────────────────────────────────────────────────────────────────────

        self.session_start_time = datetime.now()
        self.debug_file_path = debug_file_path
        self.max_context_chars = max_context_chars

    # ── Original save methods ─────────────────────────────────────────────────

    def save_llm_response(self, llm_response: Dict[str, Any],
                          step_number: int, browser_context: Dict[str, Any] = None):
        """
        Save only the current_state from LLM response.

        Args:
            llm_response: Full JSON response from LLM including current_state and actions
            step_number: Current step number
            browser_context: Not used in simplified version
        """
        current_state = llm_response.get("current_state", {})
        actions = llm_response.get("actions", [])
        if current_state:
            memory_entry = {
                "step_number": step_number,
                "current_state": current_state,
                "actions": actions,
                "timestamp": datetime.now().isoformat()
            }
            self.llm_states.append(memory_entry)

    def save_tool_output(self, tool_output: Dict[str, Any],
                         step_number: int, browser_context: Dict[str, Any] = None,
                         request_reason: str = None):
        """
        Save tool execution output including request reason.

        Args:
            tool_output: Complete output from tool execution
            step_number: Current step number
            browser_context: Not used in simplified version
            request_reason: The reason/request that triggered the tool execution
        """
        essential_output = {
            "message": tool_output.get("message", ""),
            "findings": tool_output.get("findings", ""),
            "validation_passed": tool_output.get("validation_passed", None),
            "request_reason": request_reason or "No reason provided"
        }

        memory_entry = {
            "step_number": step_number,
            "tool_output": essential_output,
            "timestamp": datetime.now().isoformat()
        }
        self.tool_outputs.append(memory_entry)

    # ── New save methods for multi-agent pipeline ─────────────────────────────

    def save_state_snapshot(self, step_number: int, snapshot_type: str,
                            state: Dict[str, Any], diff_summary: str = "") -> None:
        """
        Save a before or after state snapshot for transition proofing.

        Args:
            step_number:   The step at which the snapshot was taken
            snapshot_type: "before" | "after"
            state:         Dict with url, title, dom_summary, screenshot_b64 (optional)
            diff_summary:  Human-readable summary of the diff (for "after" snapshots)
        """
        entry = {
            "step_number": step_number,
            "type": snapshot_type,
            "url": state.get("url", ""),
            "title": state.get("title", ""),
            "dom_summary": state.get("dom_summary", ""),
            "diff_summary": diff_summary,
            "timestamp": datetime.now().isoformat(),
        }
        self.state_snapshots.append(entry)

    def save_outcome_validation(self, step_number: int,
                                validation_passed: bool,
                                state_changed: bool,
                                findings: str,
                                expected_result: str,
                                message: str = "") -> None:
        """
        Save the result of an ExecutionOutcomeValidator (tools) call.

        Args:
            step_number:       Step at which tools was called
            validation_passed: Whether the expected_result was achieved
            state_changed:     Whether the page state changed from before → after
            findings:          What the LLM observed
            expected_result:   The expected_result from the enriched test case
            message:           One-sentence verdict from the validator
        """
        entry = {
            "step_number": step_number,
            "validation_passed": validation_passed,
            "state_changed": state_changed,
            "findings": findings,
            "expected_result": expected_result,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.outcome_validations.append(entry)

    def add_compliance_note(self, note: str) -> None:
        """Add a free-text note from the AdaptivePlanner or TraversalPlanner."""
        self.compliance_notes.append(f"[{datetime.now().isoformat()}] {note}")

    # ── Retrieval helpers ─────────────────────────────────────────────────────

    def get_recent_llm_states(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent LLM current_state entries."""
        return self.llm_states[-count:] if len(self.llm_states) > count else self.llm_states

    def get_recent_tool_outputs(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get recent tool outputs."""
        return self.tool_outputs[-count:] if len(self.tool_outputs) > count else self.tool_outputs

    def get_latest_outcome_validation(self) -> Optional[Dict[str, Any]]:
        """Return the most recent outcome validation result, or None."""
        return self.outcome_validations[-1] if self.outcome_validations else None

    def get_before_state(self) -> Optional[Dict[str, Any]]:
        """Return the first 'before' snapshot captured in this session."""
        for snap in self.state_snapshots:
            if snap["type"] == "before":
                return snap
        return None

    # ── Execution summary ─────────────────────────────────────────────────────

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get simplified execution summary."""
        total_llm_states = len(self.llm_states)
        total_tool_executions = len(self.tool_outputs)

        successful_goals = 0
        failed_goals = 0
        for state in self.llm_states:
            if "current_state" in state:
                evaluation = state["current_state"].get("evaluation_previous_goal", "").lower()
                if "success" in evaluation:
                    successful_goals += 1
                elif "failed" in evaluation:
                    failed_goals += 1

        successful_tools = 0
        failed_tools = 0
        for tool in self.tool_outputs:
            if "tool_output" in tool:
                validation_passed = tool["tool_output"].get("validation_passed")
                if validation_passed is True:
                    successful_tools += 1
                elif validation_passed is False:
                    failed_tools += 1

        # Outcome validation summary
        outcome_passed = sum(1 for v in self.outcome_validations if v.get("validation_passed"))
        outcome_total = len(self.outcome_validations)

        return {
            "session_duration": (datetime.now() - self.session_start_time).total_seconds(),
            "total_llm_states": total_llm_states,
            "total_tool_executions": total_tool_executions,
            "goal_success_rate": successful_goals / max(successful_goals + failed_goals, 1),
            "tool_success_rate": successful_tools / max(successful_tools + failed_tools, 1),
            "outcome_validations_total": outcome_total,
            "outcome_validations_passed": outcome_passed,
            "state_snapshots_captured": len(self.state_snapshots),
            "recent_memory_pattern": self._analyze_recent_patterns()
        }

    def _analyze_recent_patterns(self) -> Dict[str, Any]:
        """Analyze recent execution patterns for insights."""
        recent_states = self.get_recent_llm_states(3)
        recent_tools = self.get_recent_tool_outputs(2)

        patterns = {
            "recent_goal_evaluations": [
                state["current_state"].get("evaluation_previous_goal", "Unknown")
                for state in recent_states
            ],
            "recent_next_goals": [
                state["current_state"].get("next_goal", "Unknown")
                for state in recent_states
            ],
            "recent_tool_validations": [
                tool["tool_output"].get("validation_passed", None)
                for tool in recent_tools
            ]
        }
        return patterns

    # ── LLM context formatting ────────────────────────────────────────────────

    def format_memory_context(self) -> str:
        """Format memory context for LLM prompts."""
        if not self.llm_states and not self.tool_outputs:
            return "No previous actions executed in this session."

        lines = []
        mc = self.max_context_chars

        # Recent LLM states
        recent_states = self.get_recent_llm_states(3)
        if recent_states:
            lines.append("Recent LLM States:")
            for state in recent_states:
                cs = state["current_state"]
                mem_text = cs.get('memory', 'No memory')
                if len(mem_text) > mc:
                    mem_text = mem_text[:mc] + "…"
                lines.append(f"  Step {state['step_number']}:")
                lines.append(f"    Evaluation: {cs.get('evaluation_previous_goal', 'Unknown')}")
                lines.append(f"    Memory: {mem_text}")
                lines.append(f"    Next Goal: {cs.get('next_goal', 'Unknown')}")
            lines.append("")

        # Recent tool outputs
        recent_tools = self.get_recent_tool_outputs(2)
        if recent_tools:
            lines.append("Recent Tool Outputs:")
            for tool in recent_tools:
                to = tool["tool_output"]
                findings = to.get('findings', '')
                if len(findings) > mc:
                    findings = "…" + findings[-mc:]
                lines.append(f"  Step {tool['step_number']} Tool:")
                lines.append(f"    Request: {to.get('request_reason', '')}")
                if findings:
                    lines.append(f"    Findings: {findings}")
            lines.append("")

        # Latest outcome validation (most actionable for the agent)
        latest_ov = self.get_latest_outcome_validation()
        if latest_ov:
            status = "✅ PASSED" if latest_ov["validation_passed"] else "❌ FAILED"
            lines.append(f"Latest Outcome Validation: {status}")
            lines.append(f"  State Changed: {latest_ov['state_changed']}")
            findings = latest_ov.get("findings", "")
            if len(findings) > mc:
                findings = "…" + findings[-mc:]
            if findings:
                lines.append(f"  Findings: {findings}")
            lines.append("")

        # Compliance/planning notes (brief)
        if self.compliance_notes:
            lines.append(f"Planning Note: {self.compliance_notes[-1]}")
            lines.append("")

        return "\n".join(lines)

    # ── Debug logging ─────────────────────────────────────────────────────────

    def _log_to_debug_file(self, event_type: str, data: Dict[str, Any]):
        """Log memory events to debug file if available."""
        if not self.debug_file_path:
            return
        try:
            log_entry = {
                "event_type": f"MEMORY_{event_type.upper()}",
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            with open(self.debug_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"MEMORY EVENT: {event_type}\n")
                f.write(f"TIMESTAMP: {log_entry['timestamp']}\n")
                f.write(f"{'='*80}\n\n")
                f.write(json.dumps(data, indent=2, ensure_ascii=False))
                f.write(f"\n\n")
        except Exception:
            pass

    # ── Export ────────────────────────────────────────────────────────────────

    def export_session_data(self, file_path: str):
        """Export full session data to JSON file."""
        session_data = {
            "session_info": {
                "start_time": self.session_start_time.isoformat(),
                "export_time": datetime.now().isoformat(),
                "duration": (datetime.now() - self.session_start_time).total_seconds()
            },
            "llm_states": self.llm_states,
            "tool_outputs": self.tool_outputs,
            "state_snapshots": self.state_snapshots,
            "outcome_validations": self.outcome_validations,
            "compliance_notes": self.compliance_notes,
            "execution_summary": self.get_execution_summary()
        }
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)