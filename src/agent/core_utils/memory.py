"""
Simplified Memory System for Testing Agent
Stores only essential information from LLM responses and tool outputs.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class EnhancedMemory:
    """
    Simplified memory system that stores only essential information:
    - current_state from LLM responses 
    - Essential tool execution outputs (message, findings, validation_passed)
    """
    
    def __init__(self, debug_file_path: Optional[str] = None):
        """Initialize the simplified memory system."""
        self.llm_states = []
        self.tool_outputs = []
        self.session_start_time = datetime.now()
        self.debug_file_path = debug_file_path
        
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
        # Extract only the essential fields
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
        
    def get_recent_llm_states(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent LLM current_state entries."""
        recent_states = self.llm_states[-count:] if len(self.llm_states) > count else self.llm_states
        return recent_states
        
    def get_recent_tool_outputs(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get recent tool outputs."""
        recent_tools = self.tool_outputs[-count:] if len(self.tool_outputs) > count else self.tool_outputs
        return recent_tools
        
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get simplified execution summary."""
        total_llm_states = len(self.llm_states)
        total_tool_executions = len(self.tool_outputs)
        
        # Analyze success patterns from LLM states
        successful_goals = 0
        failed_goals = 0
        
        for state in self.llm_states:
            if "current_state" in state:
                evaluation = state["current_state"].get("evaluation_previous_goal", "").lower()
                if "success" in evaluation:
                    successful_goals += 1
                elif "failed" in evaluation:
                    failed_goals += 1
        
        # Analyze tool success patterns
        successful_tools = 0
        failed_tools = 0
        
        for tool in self.tool_outputs:
            if "tool_output" in tool:
                validation_passed = tool["tool_output"].get("validation_passed")
                if validation_passed is True:
                    successful_tools += 1
                elif validation_passed is False:
                    failed_tools += 1
        
        return {
            "session_duration": (datetime.now() - self.session_start_time).total_seconds(),
            "total_llm_states": total_llm_states,
            "total_tool_executions": total_tool_executions,
            "goal_success_rate": successful_goals / max(successful_goals + failed_goals, 1),
            "tool_success_rate": successful_tools / max(successful_tools + failed_tools, 1),
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
        
    def format_memory_context(self) -> str:
        """Format simplified memory context for LLM prompts."""
        if not self.llm_states and not self.tool_outputs:
            return "No previous actions executed in this session."
        
        context_lines = []
        
        # Add recent LLM states
        recent_states = self.get_recent_llm_states(3)
        if recent_states:
            context_lines.append("Recent LLM States:")
            for state in recent_states:
                current_state = state["current_state"]
                context_lines.append(f"  Step {state['step_number']}:")
                context_lines.append(f"    Evaluation: {current_state.get('evaluation_previous_goal', 'Unknown')}")
                context_lines.append(f"    Memory: {current_state.get('memory', 'No memory')[:500]}...")
                context_lines.append(f"    Next Goal: {current_state.get('next_goal', 'Unknown')}")
            context_lines.append("")
        
        # Add recent tool outputs
        recent_tools = self.get_recent_tool_outputs(2)
        if recent_tools:
            context_lines.append("Recent Tool Outputs:")
            for tool in recent_tools:
                tool_output = tool["tool_output"]
                context_lines.append(f"  Step {tool['step_number']} Tool:")
                context_lines.append(f"    Request: {tool_output.get('request_reason', 'No reason provided')}")
                if tool_output.get('findings'):
                    context_lines.append(f"    Findings: {tool_output['findings'][:1000]}...")
            context_lines.append("")
        
        return "\n".join(context_lines)
        
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
                
        except Exception as e:
            # Silent fail for logging - don't break main execution
            pass
            
    def export_session_data(self, file_path: str):
        """Export simplified session data to JSON file."""
        session_data = {
            "session_info": {
                "start_time": self.session_start_time.isoformat(),
                "export_time": datetime.now().isoformat(),
                "duration": (datetime.now() - self.session_start_time).total_seconds()
            },
            "llm_states": self.llm_states,
            "tool_outputs": self.tool_outputs,
            "execution_summary": self.get_execution_summary()
        }
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)