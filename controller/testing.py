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

# Add project root to PATH so we can import controller.browser_controller
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from controller.browser_controller import BrowserController

def test_controller_initialization():
    logger.info("=== TESTING BROWSER CONTROLLER INITIALIZATION ===")
    controller = BrowserController()
    logger.info(f"Browser controller initialized: {controller!r}")
    logger.info(f"Browser session created: {controller.browser_context!r}")
    print()
    return controller

def test_command_dispatcher(controller):
    logger.info("=== TESTING COMMAND DISPATCHER ===")
    available_commands = [
        "go_back", "click_element", "input_text",
        "switch_tab", "open_tab", "close_tab",
        "navigate_to"
    ]
    logger.info(f"Available commands: {', '.join(available_commands)}")

    # Test nonexistent command
    logger.info("Testing invalid command...")
    result = controller.execute_command("nonexistent_command")
    logger.info(f"Invalid command result (should be False): {result}")

    # Test navigate_to
    test_page = project_root / "html" / "test_page.html"
    test_url = f"file://{test_page}"
    logger.info(f"Testing navigate_to with URL: {test_url}")
    result = controller.execute_command("navigate_to", test_url)
    logger.info(f"Navigate command result: {result}")
    time.sleep(1)
    print()

def test_navigation_commands(controller):
    logger.info("=== TESTING NAVIGATION COMMANDS ===")

    page1 = project_root / "html" / "test_page.html"
    page2 = project_root / "html" / "test_page2.html"

    # ensure page2 exists
    if not page2.exists():
        logger.warning(f"Creating {page2} for test.")
        page2.parent.mkdir(exist_ok=True)
        page2.write_text("""<!DOCTYPE html>
<html><head><title>Test Page 2</title></head>
<body>
  <h1>Test Page 2</h1>
  <button id="testButton">Test Button</button>
  <input type="text" id="testInput" />
</body></html>""")

    url1 = f"file://{page1}"
    url2 = f"file://{page2}"

    controller.execute_command("navigate_to", url1)
    time.sleep(1)
    controller.execute_command("navigate_to", url2)
    time.sleep(1)

    logger.info("Testing go_back...")
    result = controller.execute_command("go_back")
    logger.info(f"Go back result: {result}")
    time.sleep(1)

    title = controller.browser_context.get_current_page().title()
    logger.info(f"Page title after go_back: {title}")
    print()

def test_tab_management_commands(controller):
    logger.info("=== TESTING TAB MANAGEMENT COMMANDS ===")
    tabs = controller.browser_context.get_tabs_info()
    logger.info(f"Initial tabs: {len(tabs)}")

    page2 = project_root / "html" / "test_page2.html"
    url2 = f"file://{page2}"
    logger.info(f"Opening new tab with {url2}")
    result = controller.execute_command("open_tab", url2)
    logger.info(f"open_tab result: {result}")
    time.sleep(1)

    tabs = controller.browser_context.get_tabs_info()
    logger.info(f"Tabs after open: {len(tabs)}")

    logger.info("Switching to tab 0")
    controller.execute_command("switch_tab", 0)
    time.sleep(0.5)

    for t in controller.browser_context.get_tabs_info():
        if t.get("is_current"):
            logger.info(f"Current tab: id={t['page_id']} title={t['title']}")

    logger.info("Closing tab 1")
    result = controller.execute_command("close_tab", 1)
    logger.info(f"close_tab result: {result}")

    tabs = controller.browser_context.get_tabs_info()
    logger.info(f"Tabs after close: {len(tabs)}")
    print()

def test_dom_interaction_commands(controller):
    logger.info("=== TESTING DOM INTERACTION COMMANDS ===")

    page1 = project_root / "html" / "test_page.html"
    url1 = f"file://{page1}"
    controller.execute_command("navigate_to", url1)
    time.sleep(1)

    # Pull selector map directly from the session
    selector_map = controller.browser_context.get_selector_map(refresh=True)
    if not selector_map:
        logger.error("No elements found in selector map")
        return

    logger.info("Selector map entries:")
    for idx, el in selector_map.items():
        logger.info(f"  [{idx}] <{el.tag_name}> xpath={el.xpath}")

    # find a button or link to click
    button_index = next(
        (i for i, e in selector_map.items() if e.tag_name.lower() in ("button", "a")),
        None
    )
    if button_index is not None:
        logger.info(f"Clicking element at index {button_index}")
        result = controller.execute_command("click_element", button_index)
        logger.info(f"click_element result: {result}")
        time.sleep(0.5)
    else:
        logger.warning("No clickable element found")

    # find an input to fill
    input_index = next(
        (i for i, e in selector_map.items() if e.tag_name.lower() == "input"),
        None
    )
    if input_index is not None:
        text = "Hello from BrowserController!"
        logger.info(f"Filling input at index {input_index} with '{text}'")
        result = controller.execute_command("input_text", input_index, text)
        logger.info(f"input_text result: {result}")
    else:
        logger.warning("No input element found")
    print()

def main():
    logger.info("Starting BrowserController tests...")
    controller = None

    try:
        controller = test_controller_initialization()
        test_command_dispatcher(controller)
        test_navigation_commands(controller)
        test_tab_management_commands(controller)
        test_dom_interaction_commands(controller)

        input("Press Enter to close the browser session...")
    except Exception as e:
        logger.error(f"Test suite error: {e}", exc_info=True)
    finally:
        if controller:
            logger.info("Closing browser session...")
            controller.close()
            logger.info("Done.")

if __name__ == "__main__":
    main()
