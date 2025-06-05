from typing import Optional, Dict, Any, Union, List
import os
import sys
# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
# Import from the browser package
from src.browser.browser_context import BrowserSession
# Import from the tools package
from src.agent.tool_agent.tools import Tools

class BrowserController:
    """
    Controller class that wraps the BrowserSession to provide high-level browser operations.
    """

    def __init__(self, llm_client=None):
        """Initialize the BrowserController with a BrowserSession and optional LLM client."""
        self.browser_context = BrowserSession()
        self.tools_instance = Tools(llm_client)
        self.llm_client = llm_client
        # Store logging functions for tools integration
        self.log_debug_func = None
        self.debug_file_path = None

    def execute_command(self, command: str, *args) -> Union[bool, Dict[str, Any], str]:
        """
        Execute a browser command with the provided arguments.
        """
        command_map = {
            "go_back":       self.go_back,
            "click_element": self.click_element_by_index,
            "input_text":    self.input_text,
            "switch_tab":    self.switch_tab,
            "open_tab":      self.open_tab,
            "close_tab":     self.close_tab,
            "navigate_to":   self.navigate_to,
            "tools":         self.tools,
            "end":           self.end,
        }

        if command not in command_map:
            return False

        try:
            return command_map[command](*args)
        except Exception as e:
            return False

    def go_back(self) -> bool:
        try:
            self.browser_context.go_back()
            return True
        except Exception as e:
            return False

    def click_element_by_index(self, element_index: int) -> bool:
        try:
            page = self.browser_context.get_current_page()
            if page is None:
                return False

            selector_map = self.browser_context.get_selector_map(refresh=True)
            if not selector_map or element_index not in selector_map:
                return False

            element = selector_map[element_index]
            xpath   = element.xpath
            attrs   = element.attributes or {}            # Try ID first
            if (elem_id := attrs.get("id")):
                selector = f"#{elem_id}"
                page.click(selector, timeout=5000)
            else:
                # fallback to XPath - use page.locator() with xpath= prefix for XPath selectors
                xpath_selector = f"xpath={xpath}"
                page.locator(xpath_selector).click(timeout=5000)
            page.wait_for_load_state("networkidle", timeout=5000)

            # clear parser & selector_map cache
            self.browser_context._parser = None
            self.browser_context._selector_map = None

            return True

        except Exception as e:
            return False

    def input_text(self, element_index: int, text: str) -> bool:
        try:
            page = self.browser_context.get_current_page()
            if page is None:
                return False

            selector_map = self.browser_context.get_selector_map(refresh=True)
            if not selector_map or element_index not in selector_map:
                return False

            element = selector_map[element_index]
            xpath   = element.xpath
            attrs   = element.attributes or {}            # Try ID first
            if (elem_id := attrs.get("id")):
                selector = f"#{elem_id}"
                page.fill(selector, text, timeout=5000)
            else:
                # fallback to XPath - use page.locator() with xpath= prefix for XPath selectors
                xpath_selector = f"xpath={xpath}"
                page.locator(xpath_selector).fill(text, timeout=5000)

            # clear parser & selector_map cache
            self.browser_context._parser = None
            self.browser_context._selector_map = None

            return True

        except Exception as e:
            return False

    def switch_tab(self, tab_index: int) -> bool:
        try:
            return self.browser_context.switch_to_tab(tab_index)
        except Exception as e:
            return False

    def open_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        try:
            return self.browser_context.create_new_tab(url)
        except Exception as e:
            return {}

    def close_tab(self, tab_index: int) -> bool:
        try:
            return self.browser_context.close_tab(tab_index)
        except Exception as e:
            return False

    def navigate_to(self, url: str) -> bool:
        try:
            self.browser_context.navigate_to(url)
            return True
        except Exception as e:
            return False

    def tools(self, reason: str) -> Dict[str, Any]:
        """
        Execute tools action using the Tools class.
        
        Args:
            reason: The reason why tools action is needed
            
        Returns:
            Dictionary indicating success and any relevant information
        """
        try:
            # Use the Tools class to execute the action, passing the LLM client
            result = self.tools_instance.execute(reason, self.browser_context, self.llm_client)
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Tools action failed: {e}",
                "data": {}
            }

    def end(self, reason: Optional[str] = None) -> bool:
        try:
            self.browser_context.close()
            return True
        except Exception as e:
            return False

    def available_commands(self) -> list:
        """Return a list of available command names."""
        return [
            "navigate_to",
            "click_element", 
            "input_text",
            "switch_tab",
            "open_tab",
            "close_tab",
            "go_back",
            "tools",
            "end"
        ]
    
    def get_available_actions(self) -> list:
        """
        Return a list of actions that can be executed in the current state.
        Only returns command names from the command_map based on current browser state.
        """
        available = []

        # These two always make sense as long as the session exists
        available.append("open_tab")
        available.append("navigate_to")

        # Try to see if there is a "current page":
        try:
            page = self.browser_context.get_current_page()
        except Exception:
            page = None

        if page is not None:
            # If a page is open, you can generally go back
            available.append("go_back")

            # Check if there are any selectors/elements visible on this page
            try:
                selector_map = self.browser_context.get_selector_map(refresh=True)
            except Exception:
                selector_map = {}

            if selector_map:
                available.append("click_element")
                available.append("input_text")

            # See how many tabs exist to decide if switch/close are feasible
            try:
                # Access the _tabs attribute directly since there's no get_all_pages method
                all_tabs = self.browser_context._tabs
            except Exception:
                all_tabs = []

            if isinstance(all_tabs, (list, tuple)):
                if len(all_tabs) > 1:
                    available.append("switch_tab")
                # You can always close at least the current tab if one exists:
                if len(all_tabs) > 0:
                    available.append("close_tab")

        # The 'tools' and 'end' actions are always available
        available.append("tools")
        available.append("end")

        return available

    def get_available_actions_description(self) -> str:
        """Return a detailed description of currently available actions for the LLM."""
        available_actions = self.get_available_actions()
        
        # Action descriptions mapping - using exact command_map names
        action_descriptions = {
            "navigate_to": """navigate_to: Navigate to a URL
   Format: {"navigate_to": {"url": "string"}}
   Example: {"navigate_to": {"url": "https://example.com"}}""",
   
            "click_element": """click_element: Click on an interactive element by its index
   Format: {"click_element": {"index": number}}
   Example: {"click_element": {"index": 0}}
   Note: Use element indices from the Interactive Elements list""",
   
            "input_text": """input_text: Type text into an input field by its index
   Format: {"input_text": {"index": number, "text": "string"}}
   Example: {"input_text": {"index": 1, "text": "hello@example.com"}}
   Note: Use element indices from the Interactive Elements list""",
   
            "switch_tab": """switch_tab: Switch to a different browser tab
   Format: {"switch_tab": {"index": number}}
   Example: {"switch_tab": {"index": 1}}""",
   
            "open_tab": """open_tab: Open a new browser tab (optionally with URL)
   Format: {"open_tab": {"url": "string"}} or {"open_tab": {}}
   Example: {"open_tab": {"url": "https://google.com"}}""",
   
            "close_tab": """close_tab: Close a browser tab by its index
   Format: {"close_tab": {"index": number}}
   Example: {"close_tab": {"index": 1}}""",
   
            "go_back": """go_back: Navigate back in browser history
   Format: {"go_back": {}}
   Example: {"go_back": {}}""",
   
            "tools": """tools: Execute tools action for complex operations
   Format: {"tools": {"reason": "string"}}
   Example: {"tools": {"reason": "Need to verify login success or validate form data"}}""",
   
            "end": """end: End the browser session and terminate the automation
   Format: {"end": {"reason": "string"}}
   Example: {"end": {"reason": "Task completed successfully"}}
   Note: This action closes the browser session and stops the LLM"""
        }
        
        # Build description for currently available actions
        descriptions = ["Currently Available Browser Actions:\n"]
        
        counter = 1
        for action in available_actions:
            if action in action_descriptions:
                descriptions.append(f"{counter}. {action_descriptions[action]}")
                counter += 1         
        return "\n".join(descriptions)

    def close(self) -> None:
        try:
            self.browser_context.close()
        except Exception as e:
            pass

    def set_llm_client(self, llm_client):
        """Set or update the LLM client for intelligent tools operations."""
        self.llm_client = llm_client
        # Update the tools instance with the new LLM client
        self.tools_instance.llm_client = llm_client
        
    def set_logging_functions(self, log_debug_func=None, debug_file_path=None):
        """
        Set logging functions for the tools integration.
        
        Args:
            log_debug_func: Function to log debug information (from agent's _log_debug)
            debug_file_path: Path to the debug file for structured logging
        """
        self.log_debug_func = log_debug_func
        self.debug_file_path = debug_file_path
        # Update the tools instance with the logging functions
        self.tools_instance.set_logging_functions(log_debug_func, debug_file_path)

    def get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get the list of recent browser alerts."""
        return self.browser_context.get_recent_alerts()
    
    def has_recent_alerts(self) -> bool:
        """Check if there are any recent browser alerts."""
        return self.browser_context.has_recent_alerts()
    
    def get_formatted_alerts(self) -> str:
        """Get a formatted string of recent alerts."""
        return self.browser_context.get_formatted_alerts_for_llm()
    
    def clear_alerts(self) -> None:
        """Clear the alert history."""
        self.browser_context.clear_alerts()
