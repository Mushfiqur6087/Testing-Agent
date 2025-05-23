#!/usr/bin/env python
# filepath: c:\Users\himel\Downloads\DOM_TREE\controller\testing.py
import sys
import os
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add parent directory to PATH to make imports work
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Import necessary modules
from controller.browser_controller import BrowserController

def test_controller_initialization():
    """Test browser controller initialization."""
    logger.info("=== TESTING BROWSER CONTROLLER INITIALIZATION ===")
    
    # Initialize the browser controller
    controller = BrowserController()
    logger.info(f"Browser controller initialized: {controller}")
    logger.info(f"Browser session created: {controller.browser_context}")
    
    logger.info("Browser controller initialization tests completed successfully.")
    print()
    
    return controller

def test_command_dispatcher(controller):
    """Test the execute_command dispatcher method."""
    logger.info("=== TESTING COMMAND DISPATCHER ===")
    
    # Get available commands
    available_commands = [
        "go_back", "click_element", "input_text", 
        "switch_tab", "open_tab", "close_tab", 
        "navigate_to", "get_selector_map"
    ]
    logger.info(f"Available commands: {', '.join(available_commands)}")
    
    # Test nonexistent command
    logger.info("Testing invalid command...")
    result = controller.execute_command("nonexistent_command")
    logger.info(f"Invalid command result (should be False): {result}")
    
    # Test command execution (navigate_to) which we'll use for other tests
    test_page_path = os.path.join(parent_dir, "html", "test_page.html")
    test_page_url = f"file://{test_page_path}"
    logger.info(f"Testing navigate_to command with URL: {test_page_url}")
    
    result = controller.execute_command("navigate_to", test_page_url)
    logger.info(f"Navigate command result: {result}")
    
    # Wait for page to load
    time.sleep(1)
    
    logger.info("Command dispatcher tests completed successfully.")
    print()

def test_navigation_commands(controller):
    """Test navigation related commands."""
    logger.info("=== TESTING NAVIGATION COMMANDS ===")
    
    # First navigate to a test page
    test_page_path = os.path.join(parent_dir, "html", "test_page.html")
    test_page_url = f"file://{test_page_path}"
    logger.info(f"Navigating to first test page: {test_page_url}")
    controller.execute_command("navigate_to", test_page_url)
    time.sleep(1)
    
    # Then navigate to another test page to create history
    test_page2_path = os.path.join(parent_dir, "html", "test_page2.html")
    if not os.path.exists(test_page2_path):
        logger.warning(f"Test page 2 not found at {test_page2_path}, creating a simple test page")
        # Create a simple test page if it doesn't exist
        os.makedirs(os.path.dirname(test_page2_path), exist_ok=True)
        with open(test_page2_path, "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Page 2</title>
            </head>
            <body>
                <h1>Test Page 2</h1>
                <p>This is a second test page.</p>
                <button id="testButton">Test Button</button>
                <input type="text" id="testInput" />
            </body>
            </html>
            """)
    
    test_page2_url = f"file://{test_page2_path}"
    logger.info(f"Navigating to second test page: {test_page2_url}")
    controller.execute_command("navigate_to", test_page2_url)
    time.sleep(1)
    
    # Test go_back command
    logger.info("Testing go_back command...")
    result = controller.execute_command("go_back")
    logger.info(f"Go back result: {result}")
    time.sleep(1)
    
    # Verify current page title
    current_title = controller.browser_context.get_current_page().title()
    logger.info(f"Current page title after go_back: {current_title}")
    
    logger.info("Navigation commands tests completed successfully.")
    print()

def test_tab_management_commands(controller):
    """Test tab management commands."""
    logger.info("=== TESTING TAB MANAGEMENT COMMANDS ===")
    
    # Get initial tabs info
    tabs_info = controller.browser_context.get_tabs_info()
    initial_tab_count = len(tabs_info)
    logger.info(f"Initial tab count: {initial_tab_count}")
    
    # Open a new tab with URL
    test_page_path = os.path.join(parent_dir, "html", "test_page2.html")
    test_page_url = f"file://{test_page_path}"
    logger.info(f"Opening new tab with URL: {test_page_url}")
    
    result = controller.execute_command("open_tab", test_page_url)
    logger.info(f"Open tab result: {result}")
    time.sleep(1)
    
    # Verify new tab was created
    tabs_info = controller.browser_context.get_tabs_info()
    logger.info(f"Tab count after opening new tab: {len(tabs_info)}")
    
    # Switch back to the first tab
    logger.info("Switching to first tab...")
    result = controller.execute_command("switch_tab", 0)
    logger.info(f"Switch tab result: {result}")
    time.sleep(0.5)
    
    # Verify current tab
    tabs_info = controller.browser_context.get_tabs_info()
    for tab in tabs_info:
        if tab['is_current']:
            logger.info(f"Current tab is now: Tab {tab['page_id']}: {tab['title']}")
    
    # Close the second tab
    logger.info("Closing second tab...")
    result = controller.execute_command("close_tab", 1)
    logger.info(f"Close tab result: {result}")
    
    # Verify tabs after closing
    tabs_info = controller.browser_context.get_tabs_info()
    logger.info(f"Tab count after closing tab: {len(tabs_info)}")
    
    logger.info("Tab management commands tests completed successfully.")
    print()

def test_dom_interaction_commands(controller):
    """Test DOM interaction commands."""
    logger.info("=== TESTING DOM INTERACTION COMMANDS ===")
    
    # Navigate to test page with interactive elements
    test_page_path = os.path.join(parent_dir, "html", "test_page.html")
    test_page_url = f"file://{test_page_path}"
    logger.info(f"Navigating to test page: {test_page_url}")
    controller.execute_command("navigate_to", test_page_url)
    time.sleep(1)
    
    # Get selector map
    logger.info("Getting selector map...")
    selector_map_string = controller.execute_command("get_selector_map")
    
    if not selector_map_string:
        logger.error("Failed to get selector map - empty result")
        return
    
    logger.info("Interactive elements found:")
    print(selector_map_string)
    
    # Test clicking an element (assuming there's at least one clickable element)
    logger.info("Testing click_element command...")
    
    # Find the first button or link in selector map
    selector_map = controller.browser_context.get_selector_map(refresh=True)
    if not selector_map:
        logger.error("Could not get selector map for testing click_element")
        return
    
    button_index = None
    for idx, element in selector_map.items():
        tag_name = element.tag_name.lower()
        if tag_name in ['button', 'a']:
            button_index = idx
            logger.info(f"Found {tag_name} element at index {idx}")
            break
    
    if button_index is not None:
        # Try clicking the button
        logger.info(f"Clicking element at index {button_index}...")
        result = controller.execute_command("click_element", button_index)
        logger.info(f"Click element result: {result}")
        time.sleep(0.5)
    else:
        logger.warning("No button or link element found for clicking test")
    
    # Test input text (assuming there's at least one input element)
    input_index = None
    for idx, element in selector_map.items():
        if element.tag_name.lower() == 'input':
            input_index = idx
            logger.info(f"Found input element at index {idx}")
            break
    
    if input_index is not None:
        # Try inputting text
        test_text = "Hello from Browser Controller!"
        logger.info(f"Inputting text into element at index {input_index}...")
        result = controller.execute_command("input_text", input_index, test_text)
        logger.info(f"Input text result: {result}")
    else:
        logger.warning("No input element found for input_text test")
    
    logger.info("DOM interaction commands tests completed successfully.")
    print()

def main():
    """Main test function that runs all tests."""
    logger.info("Starting BrowserController testing...")
    
    try:
        # Run initialization test and get the controller object
        controller = test_controller_initialization()
        
        # Run all tests
        test_command_dispatcher(controller)
        test_navigation_commands(controller)
        test_tab_management_commands(controller)
        test_dom_interaction_commands(controller)
        
        # Wait for user input before closing
        input("Press Enter to close the browser session...")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Close the browser session if controller exists
        if 'controller' in locals():
            logger.info("Closing browser controller...")
            controller.close()
            logger.info("Browser controller closed.")

if __name__ == "__main__":
    main()
