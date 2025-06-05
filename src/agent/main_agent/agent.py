import json
import os
import sys
import ast
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)
from src.agent.core_utils.llm import GeminiFlashClient
from src.agent.main_agent.prompt_generator import SystemPromptBase
from src.agent.core_utils.logging_utils import debug_logger
from src.agent.core_utils.memory import EnhancedMemory
from typing import Dict, List, Any
from datetime import datetime

# Configure logging


class Agent:
    """
    Agent to generate JSON responses for browser automation tasks, using GeminiFlashClient for LLM evaluations.
    """
    def __init__(self, llm: GeminiFlashClient, max_actions: int = 10, debug: bool = True):
        self.llm = llm
        self.max_actions = max_actions
        self.debug = debug
        self.previous_steps = []
        self.current_url = ""
        self.open_tabs = []
        self.interactive_elements = ""
        self.valid_actions = "No browser controller attached. Available actions will be populated when browser controller is set."
        self.system_prompt = SystemPromptBase(max_actions_per_step=max_actions)
        self.browser_controller = None
        self.session_start_time = datetime.now()
        
        # Create debug log file if debug is enabled
        if self.debug:
            self.debug_file = debug_logger.get_debug_file_path("agent")
        else:
            self.debug_file = None
            
        # Initialize enhanced memory system with debug file path
        self.memory = EnhancedMemory(debug_file_path=self.debug_file)
        
    def enable_debug_mode(self, debug_file_prefix: str = None):
        """Enable debug mode for agent."""
        self.debug = True
        self.debug_file = debug_logger.get_debug_file_path("agent", debug_file_prefix)
        
        # Update memory system with new debug file path
        self.memory = EnhancedMemory(debug_file_path=self.debug_file)
        
        # Update browser controller logging functions if available
        if self.browser_controller and hasattr(self.browser_controller, 'set_logging_functions'):
            self.browser_controller.set_logging_functions(
                log_debug_func=self._log_debug,
                debug_file_path=self.debug_file
            )
        
    def disable_debug_mode(self):
        """Disable debug mode for agent."""
        self.debug = False
        self.debug_file = None
        
        # Clear browser controller logging functions if available
        if self.browser_controller and hasattr(self.browser_controller, 'set_logging_functions'):
            self.browser_controller.set_logging_functions(
                log_debug_func=None,
                debug_file_path=None
            )

    def set_browser_controller(self, browser_controller):
        """Set the browser controller instance for the agent."""
        self.browser_controller = browser_controller
        
        # Pass the LLM client to the browser controller for intelligent tools operations
        if hasattr(browser_controller, 'set_llm_client') and self.llm:
            browser_controller.set_llm_client(self.llm)
        
        # Pass logging functions to the browser controller for tools integration
        if hasattr(browser_controller, 'set_logging_functions') and self.debug:
            browser_controller.set_logging_functions(
                log_debug_func=self._log_debug,
                debug_file_path=self.debug_file
            )
        
        # Initialize valid actions immediately
        if browser_controller:
            self.valid_actions = browser_controller.get_available_actions_description()
        
    def update_browser_state(self, url: str = None, tabs: List[str] = None, 
                           elements: str = None, actions: str = None):
        """Update the current browser state information."""
        if url is not None:
            self.current_url = url
        if tabs is not None:
            self.open_tabs = tabs
        if elements is not None:
            self.interactive_elements = elements
        if actions is not None:
            self.valid_actions = actions
            
        
    def add_step(self, action: Dict[str, Any], result: Any, success: bool = True):
        """Add a completed step to the previous steps list."""
        step = {
            "step_number": len(self.previous_steps) + 1,
            "action": action,
            "result": str(result),
            "success": success,
            "url": self.current_url,
            "timestamp": datetime.now().isoformat(),
            "session_time": (datetime.now() - self.session_start_time).total_seconds()
        }
        
        self.previous_steps.append(step)
        
    def build_context_prompt(self, user_goal: str) -> str:
        """Build the complete context prompt for the LLM."""
        # Get system prompt
        system_prompt = self.system_prompt.get_prompt()
        
        # Get recent memory context
        memory_context = self._format_memory_context()
        
        # Format previous steps
        previous_steps_text = self._format_previous_steps()
        
        # Format current browser state
        browser_state = self._format_browser_state()
        
        # Build the complete prompt
        context_prompt = f"""
{system_prompt}

# Current Task
{user_goal}

# Previous Steps
{previous_steps_text}

# Current Browser State
{browser_state}

# Memory Context
{memory_context}

# Available Actions
{self.valid_actions}

Please provide your next action(s) in the required JSON format.
"""
        
        return context_prompt
        
    def _format_memory_context(self) -> str:
        """Format memory context using the enhanced memory system."""
        return self.memory.format_memory_context()
        
    def _format_previous_steps(self) -> str:
        """Format previous steps for the prompt."""
        if not self.previous_steps:
            return "No previous steps in this session."
            
        formatted_steps = []
        for step in self.previous_steps[-3:]:  # Show last 3 steps
            # Extract action name from the action dictionary
            if isinstance(step["action"], dict):
                # Get the first (and should be only) key from the action dict
                action_name = list(step["action"].keys())[0] if step["action"] else "unknown"
            else:
                action_name = str(step["action"])
            
            status = "✓" if step["success"] else "✗"
            # Truncate result to 100 characters since memory system handles full details
            result_text = str(step['result'])
            if len(result_text) > 100:
                result_text = result_text[:100] + "..."
            
            formatted_steps.append(
                f"{status} Step {step['step_number']}: {action_name} "
                f"(Result: {result_text})"
            )
            
        return "\n".join(formatted_steps)
        
    def _format_browser_state(self) -> str:
        """Format current browser state for the prompt."""
        tabs_text = f"{len(self.open_tabs)} tabs open" if self.open_tabs else "No tabs"
        
        return f"""Current URL: {self.current_url or 'No URL'}
Open Tabs: {tabs_text}
Interactive Elements:
{self.interactive_elements or 'No interactive elements detected'}"""

    def get_next_action(self, user_goal: str) -> Dict[str, Any]:
        """
        Get the next action to perform based on current state and user goal.
        Returns a JSON response with the action(s) to take.
        """
        if len(self.previous_steps) >= self.max_actions:
            return {
                "current_state": {
                    "evaluation_previous_goal": "Failed",
                    "memory": f"Maximum number of actions ({self.max_actions}) reached without completing the goal",
                    "next_goal": "Task terminated due to action limit"
                },
                "action": [{"stop": {"reason": f"Maximum actions ({self.max_actions}) reached"}}]            }
            
        try:
            # Build context for LLM
            context = self.build_context_prompt(user_goal)
            
            # Get response from LLM
            response = self.llm.ask(context)
            
            # Log debug information if enabled
            self._log_debug(context, response, len(self.previous_steps) + 1)
            
            # Parse JSON response
            try:
                action_data = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from response if it's wrapped in text
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.endswith("```"):
                    response = response[:-3]
                action_data = json.loads(response.strip())
            
            # Validate response format
            if not self._validate_action_response(action_data):
                return {
                    "current_state": {
                        "evaluation_previous_goal": "Failed",
                        "memory": "LLM returned invalid response format",
                        "next_goal": "Fix response format and retry"
                    },
                    "action": [{"error": {"reason": "Invalid response format from LLM"}}]
                }
            
            # Save LLM response to memory
            self.memory.save_llm_response(
                llm_response=action_data,
                step_number=len(self.previous_steps) + 1
            )
                
            return action_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            return {
                "current_state": {
                    "evaluation_previous_goal": "Failed",
                    "memory": f"JSON parsing error: {str(e)}",
                    "next_goal": "Retry with corrected format"
                },
                "action": [{"error": {"reason": f"JSON parsing failed: {str(e)}"}}]
            }
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return {
                "current_state": {
                    "evaluation_previous_goal": "Failed",
                    "memory": f"Unexpected error: {str(e)}",
                    "next_goal": "Handle error and retry"
                },
                "action": [{"error": {"reason": f"Unexpected error: {str(e)}"}}]
            }
            
    def _validate_action_response(self, action_data: Dict) -> bool:
        """Validate that the action response has required fields and structure."""
        if not isinstance(action_data, dict):
            return False
            
        # Check for required top-level keys
        if "current_state" not in action_data or "action" not in action_data:
            return False
            
        # Check current_state structure
        current_state = action_data["current_state"]
        required_state_fields = ["evaluation_previous_goal", "memory", "next_goal"]
        if not all(field in current_state for field in required_state_fields):
            return False
            
        # Check action structure
        actions = action_data["action"]
        if not isinstance(actions, list) or len(actions) == 0:
            return False
            
        # Each action should be a dict with exactly one key
        for action in actions:
            if not isinstance(action, dict) or len(action) != 1:
                return False
                
        return True
        
    def execute_action(self, action_item: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action using the browser controller."""
        if not self.browser_controller:
            return {"success": False, "error": "No browser controller available"}
            
        # Extract action name and parameters
        action_name = list(action_item.keys())[0]
        action_params = action_item[action_name]
        
        
        try:
            if action_name == "navigate_to":
                url = action_params.get("url")
                if not url:
                    return {"success": False, "error": "No URL provided for navigation"}
                result = self.browser_controller.execute_command("navigate_to", url)
                return {"success": result, "message": f"Navigated to {url}"}
                
            elif action_name == "click_element":
                index = action_params.get("index")
                if index is None:
                    return {"success": False, "error": "No element index provided"}
                result = self.browser_controller.execute_command("click_element", index)
                return {"success": result, "message": f"Clicked element at index {index}"}
                
            elif action_name == "input_text":
                index = action_params.get("index")
                text = action_params.get("text")
                if index is None or text is None:
                    return {"success": False, "error": "Missing index or text for input"}
                result = self.browser_controller.execute_command("input_text", index, text)
                return {"success": result, "message": f"Input text '{text}' into element {index}"}
                
            elif action_name == "switch_tab":
                index = action_params.get("index")
                if index is None:
                    return {"success": False, "error": "No tab index provided"}
                result = self.browser_controller.execute_command("switch_tab", int(index))
                return {"success": result, "message": f"Switched to tab {index}"}
                
            elif action_name == "open_tab":
                url = action_params.get("url")
                result = self.browser_controller.execute_command("open_tab", url)
                return {"success": bool(result), "message": f"Opened new tab", "tab_info": result}
                
            elif action_name == "close_tab":
                index = action_params.get("index")
                if index is None:
                    return {"success": False, "error": "No tab index provided"}
                result = self.browser_controller.execute_command("close_tab", int(index))
                return {"success": result, "message": f"Closed tab {index}"}
                
            elif action_name == "go_back":
                result = self.browser_controller.execute_command("go_back")
                return {"success": result, "message": "Navigated back"}
                
            elif action_name == "tools":
                reason = action_params.get("reason", "No reason provided")
                result = self.browser_controller.execute_command("tools", reason)
                
                # Save tool output to memory with request reason
                tool_output = {
                    "message": result.get("message", f"Tools action executed with reason: {reason}"),
                    "findings": result.get("data", {}).get("findings", ""),
                    "validation_passed": result.get("data", {}).get("validation_passed", None)
                }
                self.memory.save_tool_output(
                    tool_output=tool_output,
                    step_number=len(self.previous_steps) + 1,
                    request_reason=reason
                )
                
                return {"success": result.get("success", True), "message": result.get("message", f"Tools action executed with reason: {reason}"), "data": result.get("data", {})}
                
            elif action_name == "end":
                reason = action_params.get("reason", "Session ended by user request")
                result = self.browser_controller.execute_command("end", reason)
                
                # Export memory data when session ends
                try:
                    memory_export_path = debug_logger.get_debug_file_path("memory_export")
                    memory_export_path = memory_export_path.replace('.log', '.json')
                    self.memory.export_session_data(memory_export_path)
                except Exception as e:
                    print(f"Error exporting memory data: {str(e)}")
                    # Silent fail for memory export - don't break main execution
                    pass
                
                return {"success": result, "message": f"Session ended: {reason}", "terminate": True}
                
            else:
                return {"success": False, "error": f"Unknown action: {action_name}"}
                
        except Exception as e:
            print(f"Exception during action execution: {str(e)}")
            return {"success": False, "error": f"Exception during execution: {str(e)}"}
            
    def refresh_browser_state(self):
        """Refresh the current browser state from the browser controller."""
        if not self.browser_controller:
            return
            
        try:
            # Get current page info
            page = self.browser_controller.browser_context.get_current_page()
            if page:
                self.current_url = page.url
                
            # Get tabs info
            tabs_info = self.browser_controller.browser_context.get_tabs_info()
            self.open_tabs = [f"Tab {tab['page_id']}: {tab['title']}" for tab in tabs_info]
            
            # Get interactive elements
            selector_map_string = self.browser_controller.browser_context.get_selector_map_string(refresh=True)
            self.interactive_elements = selector_map_string
            
            # Get available actions with detailed descriptions
            self.valid_actions = self.browser_controller.get_available_actions_description()
            
            
        except Exception as e:
            print(f"Error refreshing browser state: {str(e)}")
            self.current_url = "Error: Unable to get current URL"
            self.open_tabs = ["Error: Unable to get tabs info"]
            self.interactive_elements = "Error: Unable to get interactive elements"
            self.valid_actions = "Error: Unable to get available actions"
            
            
    def execute_plan(self, user_goal: str) -> List[Dict[str, Any]]:
        """
        Execute a complete plan to achieve the user goal.
        Returns a list of all actions taken and their results.
        """
        if not self.browser_controller:
            return [{"error": "No browser controller available", "success": False}]
            
        execution_log = []
        
        while len(self.previous_steps) < self.max_actions:
            # Refresh browser state
            self.refresh_browser_state()
            
            # Get next action from LLM
            action_response = self.get_next_action(user_goal)
            
            execution_log.append({
                "step": len(self.previous_steps) + 1,
                "llm_response": action_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Check if we should stop
            actions = action_response.get("action", [])
                
            # Filter out 'end' actions when chained with other actions
            actions = self._filter_chained_end_actions(actions)
                
            # Execute each action in sequence
            all_success = True
            action_results = []
            should_terminate = False
            
            # Filter out 'end' actions if they are chained with other actions
            actions = self._filter_chained_end_actions(actions)
            
            for action_item in actions:
                action_name = list(action_item.keys())[0]
                
                # Execute the action (including termination actions)
                try:
                    result = self.execute_action(action_item)
                    action_results.append({
                        "action": action_item,
                        "result": result
                    })
                    
                    # Add step to history
                    self.add_step(action_item, result, result.get("success", False))
                    
                    if not result.get("success", False):
                        all_success = False
                        break
                        
                    # Check if this action terminates the sequence
                    if result.get("terminate", False) or action_name in ["end"]:
                        should_terminate = True
                        break
                        
                except Exception as e:
                    print(f"Exception during action execution: {str(e)}")
                    error_result = {"success": False, "error": f"Exception: {str(e)}"}
                    action_results.append({
                        "action": action_item,
                        "result": error_result
                    })
                    self.add_step(action_item, error_result, False)
                    all_success = False
                    break
                      # Update execution log with results
            execution_log[-1]["action_results"] = action_results
            execution_log[-1]["overall_success"] = all_success
            
            # Check for termination
            if should_terminate or any(result.get("result", {}).get("terminate", False) for result in action_results):
                break
                
            if not all_success:
                break
                
        return execution_log
        
    def reset_session(self):
        """Reset the current session and create a new memory instance."""
        self.previous_steps = []
        self.current_url = ""
        self.open_tabs = []
        self.interactive_elements = ""
        self.valid_actions = ""
        self.session_start_time = datetime.now()
        
        # Create a new memory instance for the new session
        self.memory = EnhancedMemory(debug_file_path=self.debug_file)
                    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session."""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        
        # Get memory execution summary
        memory_summary = self.memory.get_execution_summary()
        
        return {
            "session_duration_seconds": session_duration,
            "total_steps": len(self.previous_steps),
            "successful_steps": len([s for s in self.previous_steps if s["success"]]),
            "failed_steps": len([s for s in self.previous_steps if not s["success"]]),
            "current_url": self.current_url,
            "open_tabs_count": len(self.open_tabs),
            "memory_llm_states": memory_summary["total_llm_states"],
            "memory_tool_executions": memory_summary["total_tool_executions"],
            "memory_goal_success_rate": memory_summary["goal_success_rate"],
            "memory_tool_success_rate": memory_summary["tool_success_rate"],
            "last_action": self.previous_steps[-1]["action"] if self.previous_steps else None,
            "browser_controller_attached": self.browser_controller is not None
        }
        
    def save_session_log(self, filename: str = None) -> str:
        """Save the current session to a JSON file."""
        if filename is None:
            filename = debug_logger.get_session_log_path()
        else:
            # If a custom filename is provided, still put it in the logs directory
            filename = debug_logger.get_session_log_path(filename)
            
        session_data = {
            "session_summary": self.get_session_summary(),
            "previous_steps": self.previous_steps,
            "memory_llm_states": self.memory.llm_states,
            "memory_tool_outputs": self.memory.tool_outputs,
            "memory_execution_summary": self.memory.get_execution_summary(),
            "final_state": {
                "current_url": self.current_url,
                "open_tabs": self.open_tabs,
                "interactive_elements": self.interactive_elements
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            return filename
        except Exception as e:
            print(f"Error saving session log: {str(e)}")
            return ""
        
    def _log_debug(self, request: str, response: str, step_number: int = None):
        """Log LLM request and response to debug file if debug mode is enabled."""
        if not self.debug:
            return
            
        try:
            timestamp = datetime.now().isoformat()
            step_info = f" (Step {step_number})" if step_number else ""
            
            debug_entry = f"""
{'='*80}
TIMESTAMP: {timestamp}{step_info}
{'='*80}

REQUEST TO LLM:
{'-'*40}
{request}
{'-'*40}

RESPONSE FROM LLM:
{'-'*40}
{response}
{'-'*40}

"""
            
            with open(self.debug_file, 'a', encoding='utf-8') as f:
                f.write(debug_entry)
                
        except Exception as e:
            print(f"Error logging debug information: {str(e)}")

    def _filter_chained_end_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out 'end' actions when they are chained with other actions.
        The 'end' action should only be executed if it's the only action in the list.
        
        Args:
            actions: List of action dictionaries from LLM response
            
        Returns:
            Filtered list of actions with 'end' removed if chained with others
        """
        if not actions or len(actions) <= 1:
            return actions
            
        # Check if there's an 'end' action in a list with multiple actions
        has_end_action = any(
            list(action.keys())[0] == "end" 
            for action in actions 
            if isinstance(action, dict) and action
        )
        
        if has_end_action and len(actions) > 1:
            # Filter out 'end' actions when chained with others
            filtered_actions = [
                action for action in actions 
                if not (isinstance(action, dict) and action and list(action.keys())[0] == "end")
            ]
            return filtered_actions
            
        return actions




