import logging
from typing import Optional, Dict, Any, List, Union, Tuple
from browser.browser_context import BrowserSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserController:
    """
    Controller class that wraps the BrowserSession to provide high-level browser operations.
    """
    
    def __init__(self):
        """Initialize the BrowserController with a BrowserSession."""
        self.browser_context = BrowserSession()
    
    def execute_command(self, command: str, *args) -> Union[bool, Dict[str, Any], str]:
        """
        Execute a browser command with the provided arguments.
        
        Args:
            command: String command to execute (go_back, click_element, input_text, etc.)
            *args: Variable arguments to pass to the command method
            
        Returns:
            Result of the command execution (typically bool, dict, or string)
            
        Supported commands:
        - go_back: Navigate back in browser history
        - click_element: Click element by index (requires element_index)
        - input_text: Input text into element (requires element_index, text)
        - switch_tab: Switch to specific tab (requires tab_index)
        - open_tab: Open a new tab (optional url)
        - close_tab: Close a specific tab (requires tab_index)
        - navigate_to: Navigate to a URL (requires url)
        - get_selector_map: Get the selector map as a string
        """
        try:
            # Map commands to their respective methods
            command_map = {
                "go_back": self.go_back,
                "click_element": self.click_element_by_index,
                "input_text": self.input_text,
                "switch_tab": self.switch_tab,
                "open_tab": self.open_tab,
                "close_tab": self.close_tab,
                "navigate_to": self.navigate_to,
                "get_selector_map": self.get_selector_map_string
            }
            
            # Check if the command exists
            if command not in command_map:
                logger.error(f"Unknown command: {command}")
                logger.info(f"Available commands: {', '.join(command_map.keys())}")
                return False
            
            # Get the method to call
            method = command_map[command]
            
            # Call the method with the provided arguments
            return method(*args)
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return False
    
    def go_back(self) -> bool:
        """
        Navigate back in the browser history.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.browser_context.go_back()
            return True
        except Exception as e:
            logger.error(f"Error navigating back: {e}")
            return False
    
    def click_element_by_index(self, element_index: int) -> bool:
        """
        Click an element in the DOM by its index in the selector map.
        
        Args:
            element_index: The index of the element to click
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current page
            page = self.browser_context.get_current_page()
            if not page:
                logger.error("No active page to interact with")
                return False
            
            # Get the selector map
            selector_map = self.browser_context.get_selector_map(refresh=True)
            if not selector_map:
                logger.error("Could not get selector map")
                return False
            
            # Check if the index is valid
            if element_index not in selector_map:
                logger.error(f"Element index {element_index} not found in selector map")
                return False
            
            # Get the element's XPath
            element = selector_map[element_index]
            xpath = element.xpath
            
            logger.info(f"Attempting to click element with XPath: {xpath}")
            
            # First try to click directly using CSS or other selectors if available
            try:
                if hasattr(element, 'id') and element.id:
                    page.click(f"#{element.id}")
                    logger.info(f"Clicked element by ID: {element.id}")
                elif hasattr(element, 'tag_name') and element.tag_name.lower() == 'button':
                    # Try to find button by text
                    if hasattr(element, 'text_content') and element.text_content:
                        page.click(f"button:has-text('{element.text_content}')")
                        logger.info(f"Clicked button by text: {element.text_content}")
                    else:
                        # Try nth button
                        page.click(f"{element.tag_name.lower()}")
                        logger.info(f"Clicked first {element.tag_name} element")
                elif hasattr(element, 'tag_name') and element.tag_name.lower() == 'a':
                    # Try to find link by text
                    if hasattr(element, 'text_content') and element.text_content:
                        page.click(f"a:has-text('{element.text_content}')")
                        logger.info(f"Clicked link by text: {element.text_content}")
                    else:
                        # Try nth link
                        page.click(f"{element.tag_name.lower()}")
                        logger.info(f"Clicked first {element.tag_name} element")
                else:
                    # Fall back to XPath but with shorter timeout
                    page.click(f"xpath={xpath}", timeout=5000)
                    logger.info(f"Clicked element by XPath: {xpath}")
                
            except Exception as e:
                logger.warning(f"First click attempt failed: {e}")
                
                # Try a more general selector
                try:
                    # Use tag name as a fallback
                    if hasattr(element, 'tag_name'):
                        page.click(element.tag_name.lower(), timeout=5000)
                        logger.info(f"Clicked element by tag name: {element.tag_name}")
                    else:
                        logger.error("No fallback selector available")
                        return False
                except Exception as e2:
                    logger.error(f"All click attempts failed: {e2}")
                    return False
            
            # Wait a moment for the click to take effect
            page.wait_for_load_state("networkidle", timeout=5000)
            
            # Clear the element tree and selector map cache as the page might have changed
            self.browser_context._dom_element_tree = None
            self.browser_context._selector_map = None
            
            return True
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return False
    
    def input_text(self, element_index: int, text: str) -> bool:
        """
        Input text into an element in the DOM by its index in the selector map.
        
        Args:
            element_index: The index of the element to input text into
            text: The text to input
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current page
            page = self.browser_context.get_current_page()
            if not page:
                logger.error("No active page to interact with")
                return False
            
            # Get the selector map
            selector_map = self.browser_context.get_selector_map(refresh=True)
            if not selector_map:
                logger.error("Could not get selector map")
                return False
            
            # Check if the index is valid
            if element_index not in selector_map:
                logger.error(f"Element index {element_index} not found in selector map")
                return False
            
            # Get the element's XPath
            element = selector_map[element_index]
            xpath = element.xpath
            
            logger.info(f"Attempting to fill element with XPath: {xpath}")
            
            # Try different selector strategies
            try:
                if hasattr(element, 'id') and element.id:
                    page.fill(f"#{element.id}", text)
                    logger.info(f"Filled element by ID: {element.id}")
                elif hasattr(element, 'tag_name') and element.tag_name.lower() == 'input':
                    # Try using input type
                    if 'type' in element.attributes:
                        input_type = element.attributes['type']
                        page.fill(f"input[type='{input_type}']", text)
                        logger.info(f"Filled input by type: {input_type}")
                    else:
                        # Try first input
                        page.fill("input", text)
                        logger.info("Filled first input element")
                else:
                    # Fall back to XPath but with shorter timeout
                    page.fill(f"xpath={xpath}", text, timeout=5000)
                    logger.info(f"Filled element by XPath: {xpath}")
                
            except Exception as e:
                logger.warning(f"First fill attempt failed: {e}")
                
                # Try a more general selector
                try:
                    # Use tag name as a fallback
                    if hasattr(element, 'tag_name') and element.tag_name.lower() == 'input':
                        page.fill("input", text, timeout=5000)
                        logger.info(f"Filled element by tag name: {element.tag_name}")
                    else:
                        logger.error("No fallback selector available")
                        return False
                except Exception as e2:
                    logger.error(f"All fill attempts failed: {e2}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error inputting text: {e}")
            return False
    
    def switch_tab(self, tab_index: int) -> bool:
        """
        Switch to a tab by its index.
        
        Args:
            tab_index: The index of the tab to switch to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.browser_context.switch_to_tab(tab_index)
        except Exception as e:
            logger.error(f"Error switching tab: {e}")
            return False
    
    def open_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Open a new tab and optionally navigate to a URL.
        
        Args:
            url: Optional URL to navigate to
            
        Returns:
            Dictionary with new tab information
        """
        try:
            return self.browser_context.create_new_tab(url)
        except Exception as e:
            logger.error(f"Error opening tab: {e}")
            return {}
    
    def close_tab(self, tab_index: int) -> bool:
        """
        Close a tab by its index.
        
        Args:
            tab_index: The index of the tab to close
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.browser_context.close_tab(tab_index)
        except Exception as e:
            logger.error(f"Error closing tab: {e}")
            return False
    
    def get_selector_map_string(self) -> str:
        """
        Get a string representation of the selector map for interactive elements.
        
        Returns:
            String representation of the selector map
        """
        try:
            return self.browser_context.get_selector_map_string(refresh=True)
        except Exception as e:
            logger.error(f"Error getting selector map string: {e}")
            return ""
    
    def navigate_to(self, url: str) -> bool:
        """
        Navigate to a specified URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.browser_context.navigate_to(url)
            return True
        except Exception as e:
            logger.error(f"Error navigating to URL: {e}")
            return False
    
    def close(self) -> None:
        """
        Close the browser session and release all resources.
        """
        try:
            self.browser_context.close()
        except Exception as e:
            logger.error(f"Error closing browser session: {e}")
