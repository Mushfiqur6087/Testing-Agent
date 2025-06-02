from memory import Memory
from llm import GeminiFlashClient
from prompt_builder import SystemPromptBase
from logging_utils import debug_logger
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Agent:
    """
    Agent to generate JSON responses for browser automation tasks, using GeminiFlashClient for LLM evaluations.
    """
    def __init__(self, llm: GeminiFlashClient, max_actions: int = 10, debug: bool = True):
        self.memory = Memory()
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
            logger.info(f"Debug mode enabled. Logging to: {self.debug_file}")
              # Enable debug mode for memory with synchronized debug file
            memory_debug_file = debug_logger.get_debug_file_path("memory")
            self.memory.enable_debug(memory_debug_file)
        
    def enable_debug_mode(self, debug_file_prefix: str = None):
        """Enable debug mode for both agent and memory."""
        self.debug = True
        
        self.debug_file = debug_logger.get_debug_file_path("agent", debug_file_prefix)
        memory_debug_file = debug_logger.get_debug_file_path("memory", debug_file_prefix)
            
        self.memory.enable_debug(memory_debug_file)
        logger.info(f"Debug mode enabled. Agent logging to: {self.debug_file}, Memory logging to: {memory_debug_file}")
        
    def disable_debug_mode(self):
        """Disable debug mode for both agent and memory."""
        self.debug = False
        self.debug_file = None
        self.memory.disable_debug()
        logger.info("Debug mode disabled for agent and memory")

    def set_browser_controller(self, browser_controller):
        """Set the browser controller instance for the agent."""
        self.browser_controller = browser_controller
        # Initialize valid actions immediately
        if browser_controller:
            self.valid_actions = browser_controller.get_available_actions_description()
        logger.info("Browser controller attached to agent")
        
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
            
        logger.debug(f"Browser state updated: URL={self.current_url}, Tabs={len(self.open_tabs)}")
        
    def add_step(self, action: Dict[str, Any], result: Any, success: bool = True):
        """Add a completed step to the previous steps list and memory."""
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
        
        # Store in memory with structured format and more details
        action_name = list(action.keys())[0] if isinstance(action, dict) and action else "unknown"
        action_params = action.get(action_name, {}) if isinstance(action, dict) else {}
        
        memory_entry = {
            "type": "action_execution",
            "step": step["step_number"],
            "action": action_name,
            "action_params": action_params,  # Store the parameters too
            "success": success,
            "url": self.current_url,
            "timestamp": step["timestamp"],
            "result_summary": str(result)[:200] if result else ""  # Store truncated result
        }
        self.memory.add(memory_entry)
        
        # Log memory snapshot if debug mode is enabled
        if self.debug:
            self.memory.log_memory_snapshot(
                step_number=step["step_number"],
                custom_message=f"After executing {action_name} ({'success' if success else 'failed'})"
            )
        
        logger.info(f"Step {step['step_number']} added: {action} -> Success: {success}")
        
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
        """Format recent memory entries for context - simplified to show only success rate and behavior patterns."""
        if len(self.memory) == 0:
            return "No previous memory entries."
            
        recent_entries = self.memory.history[-10:]  # Look at recent entries for analysis
        
        # Extract basic statistics
        success_count = 0
        failure_count = 0
        actions_performed = []
        
        for entry in recent_entries:
            if entry.get("type") == "action_execution":
                action_name = entry.get("action", "unknown")
                success = entry.get("success", False)
                
                # Count successes and failures
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                # Track actions for pattern analysis
                actions_performed.append(action_name)
        
        # Build simplified context
        summary_lines = []
        if recent_entries:
            total_actions = success_count + failure_count
            success_rate = (success_count / total_actions * 100) if total_actions > 0 else 0
            
            summary_lines.append(f"📊 Success rate: {success_rate:.1f}% ({success_count}/{total_actions})")
            
            # Show recent action flow (behavior patterns)
            if actions_performed:
                recent_flow = " → ".join(actions_performed[-5:])  # Last 5 actions
                summary_lines.append(f"🔄 Recent flow: {recent_flow}")
        
        return "\n".join(summary_lines)
        
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
            formatted_steps.append(
                f"{status} Step {step['step_number']}: {action_name} "
                f"(Result: {step['result'][:100]}{'...' if len(step['result']) > 100 else ''})"
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
            logger.info("Requesting next action from LLM...")
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
                
            return action_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {
                "current_state": {
                    "evaluation_previous_goal": "Failed",
                    "memory": f"JSON parsing error: {str(e)}",
                    "next_goal": "Retry with corrected format"
                },
                "action": [{"error": {"reason": f"JSON parsing failed: {str(e)}"}}]
            }
        except Exception as e:
            logger.error(f"Error getting next action: {e}")
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
        
        logger.info(f"Executing action: {action_name} with params: {action_params}")
        
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
                return {"success": result.get("success", True), "message": result.get("message", f"Tools action executed with reason: {reason}"), "data": result.get("data", {})}
                
            elif action_name == "end":
                reason = action_params.get("reason", "Session ended by user request")
                result = self.browser_controller.execute_command("end", reason)
                return {"success": result, "message": f"Session ended: {reason}", "terminate": True}
                
            else:
                return {"success": False, "error": f"Unknown action: {action_name}"}
                
        except Exception as e:
            logger.error(f"Error executing action {action_name}: {e}")
            return {"success": False, "error": f"Exception during execution: {str(e)}"}
            
    def refresh_browser_state(self):
        """Refresh the current browser state from the browser controller."""
        if not self.browser_controller:
            logger.warning("No browser controller available to refresh state")
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
            
            logger.info(f"Browser state refreshed: {len(self.open_tabs)} tabs, URL: {self.current_url}")
            
        except Exception as e:
            logger.error(f"Error refreshing browser state: {e}")
            
    def execute_plan(self, user_goal: str) -> List[Dict[str, Any]]:
        """
        Execute a complete plan to achieve the user goal.
        Returns a list of all actions taken and their results.
        """
        if not self.browser_controller:
            return [{"error": "No browser controller available", "success": False}]
            
        execution_log = []
        logger.info(f"Starting execution plan for goal: {user_goal}")
        
        while len(self.previous_steps) < self.max_actions:
            # Refresh browser state
            self.refresh_browser_state()
            
            # Get next action from LLM
            action_response = self.get_next_action(user_goal)
            
            # Store LLM insights in memory
            self.add_llm_insight(action_response)
            
            execution_log.append({
                "step": len(self.previous_steps) + 1,
                "llm_response": action_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Check if we should stop
            actions = action_response.get("action", [])
            if not actions:
                logger.warning("No actions provided by LLM")
                break
                
            # Execute each action in sequence
            all_success = True
            action_results = []
            
            for action_item in actions:
                action_name = list(action_item.keys())[0]
                
                # Check for termination actions
                if action_name in ["end"]:
                    logger.info(f"Termination action received: {action_name}")
                    action_results.append({
                        "action": action_item,
                        "result": {"success": True, "message": f"Plan {action_name}"},
                        "terminate": True
                    })
                    all_success = True
                    break
                    
                # Execute the action
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
                        logger.warning(f"Action failed: {action_item}")
                        break
                        
                    # Check if this action terminates the sequence
                    if result.get("terminate", False):
                        break
                        
                except Exception as e:
                    error_result = {"success": False, "error": f"Exception: {str(e)}"}
                    action_results.append({
                        "action": action_item,
                        "result": error_result
                    })
                    self.add_step(action_item, error_result, False)
                    all_success = False
                    logger.error(f"Exception executing action {action_item}: {e}")
                    break
                      # Update execution log with results
            execution_log[-1]["action_results"] = action_results
            execution_log[-1]["overall_success"] = all_success
            
            # Check for termination
            if any(result.get("result", {}).get("terminate", False) for result in action_results):
                logger.info("Plan execution terminated by action")
                break
                
            if not all_success:
                logger.warning("Plan execution stopped due to failed action")
                break
                
        logger.info(f"Plan execution completed. Total steps: {len(self.previous_steps)}")
        return execution_log
        
    def reset_session(self):
        """Reset the current session while keeping memory intact."""
        self.previous_steps = []
        self.current_url = ""
        self.open_tabs = []
        self.interactive_elements = ""
        self.valid_actions = ""
        self.session_start_time = datetime.now()
        
        # Log memory snapshot at session reset if debug mode is enabled
        if self.debug:
            self.memory.log_memory_snapshot(
                custom_message="Session reset - starting new session"
            )
            
        logger.info("Agent session reset")
        
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session."""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        
        return {
            "session_duration_seconds": session_duration,
            "total_steps": len(self.previous_steps),
            "successful_steps": len([s for s in self.previous_steps if s["success"]]),
            "failed_steps": len([s for s in self.previous_steps if not s["success"]]),
            "current_url": self.current_url,
            "open_tabs_count": len(self.open_tabs),
            "memory_entries": len(self.memory),
            "last_action": self.previous_steps[-1]["action"] if self.previous_steps else None,
            "browser_controller_attached": self.browser_controller is not None        }
        
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
            "memory_history": self.memory.history,
            "final_state": {
                "current_url": self.current_url,
                "open_tabs": self.open_tabs,
                "interactive_elements": self.interactive_elements
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Session log saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save session log: {e}")
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
            logger.error(f"Failed to write debug log: {e}")
            
    def add_llm_insight(self, llm_response: Dict[str, Any]):
        """Store LLM insights and goal evaluation in memory."""
        if not isinstance(llm_response, dict):
            return
            
        current_state = llm_response.get("current_state", {})
        
        memory_entry = {
            "type": "llm_insight",
            "step": len(self.previous_steps),
            "evaluation": current_state.get("evaluation_previous_goal", "Unknown"),
            "memory_note": current_state.get("memory", ""),
            "next_goal": current_state.get("next_goal", ""),
            "timestamp": datetime.now().isoformat(),
            "url": self.current_url
        }
        
        self.memory.add(memory_entry)
        
        # Log LLM insight if debug mode is enabled
        if self.debug:
            self.memory.log_memory_snapshot(
                step_number=len(self.previous_steps),
                custom_message=f"LLM Insight: {current_state.get('next_goal', 'No goal specified')}"
            )





