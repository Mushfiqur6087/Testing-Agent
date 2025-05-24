import logging
from typing import Optional, Dict, Any, Union

# Import from the browser package
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
        """
        command_map = {
            "go_back":       self.go_back,
            "click_element": self.click_element_by_index,
            "input_text":    self.input_text,
            "switch_tab":    self.switch_tab,
            "open_tab":      self.open_tab,
            "close_tab":     self.close_tab,
            "navigate_to":   self.navigate_to,
        }

        if command not in command_map:
            logger.error(f"Unknown command: {command}")
            logger.info(f"Available commands: {', '.join(command_map.keys())}")
            return False

        try:
            return command_map[command](*args)
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return False

    def go_back(self) -> bool:
        try:
            self.browser_context.go_back()
            return True
        except Exception as e:
            logger.error(f"Error navigating back: {e}")
            return False

    def click_element_by_index(self, element_index: int) -> bool:
        try:
            page = self.browser_context.get_current_page()
            if page is None:
                logger.error("No active page to interact with")
                return False

            selector_map = self.browser_context.get_selector_map(refresh=True)
            if not selector_map or element_index not in selector_map:
                logger.error(f"Element index {element_index} not found in selector map")
                return False

            element = selector_map[element_index]
            xpath   = element.xpath
            attrs   = element.attributes or {}            # Try ID first
            if (elem_id := attrs.get("id")):
                selector = f"#{elem_id}"
                logger.info(f"Clicking element using ID selector: {selector}")
                page.click(selector, timeout=5000)
            else:
                # fallback to XPath - use page.locator() with xpath= prefix for XPath selectors
                xpath_selector = f"xpath={xpath}"
                logger.info(f"Clicking element using XPath selector: {xpath_selector}")
                page.locator(xpath_selector).click(timeout=5000)
            page.wait_for_load_state("networkidle", timeout=5000)

            # clear parser & selector_map cache
            self.browser_context._parser = None
            self.browser_context._selector_map = None

            return True

        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return False

    def input_text(self, element_index: int, text: str) -> bool:
        try:
            page = self.browser_context.get_current_page()
            if page is None:
                logger.error("No active page to interact with")
                return False

            selector_map = self.browser_context.get_selector_map(refresh=True)
            if not selector_map or element_index not in selector_map:
                logger.error(f"Element index {element_index} not found in selector map")
                return False

            element = selector_map[element_index]
            xpath   = element.xpath
            attrs   = element.attributes or {}            # Try ID first
            if (elem_id := attrs.get("id")):
                selector = f"#{elem_id}"
                logger.info(f"Filling element using ID selector: {selector} with text: {text!r}")
                page.fill(selector, text, timeout=5000)
            else:
                # fallback to XPath - use page.locator() with xpath= prefix for XPath selectors
                xpath_selector = f"xpath={xpath}"
                logger.info(f"Filling element using XPath selector: {xpath_selector} with text: {text!r}")
                page.locator(xpath_selector).fill(text, timeout=5000)

            # clear parser & selector_map cache
            self.browser_context._parser = None
            self.browser_context._selector_map = None

            return True

        except Exception as e:
            logger.error(f"Error inputting text: {e}")
            return False

    def switch_tab(self, tab_index: int) -> bool:
        try:
            return self.browser_context.switch_to_tab(tab_index)
        except Exception as e:
            logger.error(f"Error switching tab: {e}")
            return False

    def open_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        try:
            return self.browser_context.create_new_tab(url)
        except Exception as e:
            logger.error(f"Error opening tab: {e}")
            return {}

    def close_tab(self, tab_index: int) -> bool:
        try:
            return self.browser_context.close_tab(tab_index)
        except Exception as e:
            logger.error(f"Error closing tab: {e}")
            return False

    def navigate_to(self, url: str) -> bool:
        try:
            self.browser_context.navigate_to(url)
            return True
        except Exception as e:
            logger.error(f"Error navigating to URL: {e}")
            return False

    def close(self) -> None:
        try:
            self.browser_context.close()
        except Exception as e:
            logger.error(f"Error closing browser session: {e}")
