#!/usr/bin/env python3
# filepath: /home/mushfiqur/vscode/Testing-Agent/tests/browser_controller_test_clean.py

import os
import sys
import time
import asyncio
from unittest.mock import Mock

# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.controller.browser_controller import BrowserController

# Fix for "Playwright Sync API called from inside asyncio loop" error
def ensure_no_event_loop():
    """Ensure no asyncio event loop is running to prevent Playwright sync API conflicts"""
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            loop.close()
    except RuntimeError:
        # No loop running, which is what we want
        pass

def test_basic_initialization():
    """Test 1: Basic initialization and available commands"""
    print("\n=== Test 1: Basic Initialization ===")
    
    ensure_no_event_loop()  # Prevent asyncio conflicts
    controller = None
    try:
        controller = BrowserController()
        print("✓ BrowserController initialized successfully")
        
        # Test available commands
        commands = controller.available_commands()
        expected_commands = [
            "navigate_to", "click_element", "input_text", "switch_tab",
            "open_tab", "close_tab", "go_back", "tools", "end"
        ]
        
        print(f"Available commands: {commands}")
        assert all(cmd in commands for cmd in expected_commands), "Missing expected commands"
        print("✓ All expected commands are available")
        
        # Test available actions (should include basic actions)
        actions = controller.get_available_actions()
        print(f"Available actions: {actions}")
        assert "navigate_to" in actions, "navigate_to should always be available"
        assert "open_tab" in actions, "open_tab should always be available"
        assert "tools" in actions, "tools should always be available"
        assert "end" in actions, "end should always be available"
        print("✓ Basic actions are always available")
        
    except Exception as e:
        print(f"Basic initialization test error: {e}")
        raise
        
    finally:
        if controller:
            try:
                controller.close()
                time.sleep(1.0)  # Allow cleanup time
            except:
                pass

def test_navigation_operations():
    """Test 2: Navigation operations"""
    print("\n=== Test 2: Navigation Operations ===")
    
    ensure_no_event_loop()  # Prevent asyncio conflicts
    controller = None
    try:
        controller = BrowserController()
        test_html_path = os.path.join(PROJECT_ROOT, "html", "test_browser_controller.html")
        test_url = f"file://{test_html_path}"
        
        # Test navigation
        print(f"Navigating to: {test_url}")
        result = controller.navigate_to(test_url)
        assert result == True, "Navigation should succeed"
        print("✓ Navigation successful")
        
        # Wait for page to load
        time.sleep(1)
        
        # Test getting current page
        page = controller.browser_context.get_current_page()
        assert page is not None, "Current page should not be None"
        print("✓ Current page retrieved successfully")
        
        # Verify URL
        current_url = page.url
        print(f"Current URL: {current_url}")
        assert test_url in current_url, "URL should match navigated page"
        print("✓ URL verification successful")
        
        # Test going back (should work even if no previous page)
        back_result = controller.go_back()
        print(f"Go back result: {back_result}")
        
        # Test invalid navigation
        invalid_result = controller.navigate_to("invalid://nonexistent")
        print(f"Invalid navigation result: {invalid_result}")
        # Note: This might succeed or fail depending on browser behavior
        
    except Exception as e:
        print(f"Navigation test error: {e}")
        raise
        
    finally:
        if controller:
            try:
                controller.close()
                time.sleep(1.0)  # Allow cleanup time
            except:
                pass

def test_tab_operations():
    """Test 3: Tab operations"""
    print("\n=== Test 3: Tab Operations ===")
    
    ensure_no_event_loop()  # Prevent asyncio conflicts
    controller = None
    try:
        controller = BrowserController()
        test_html_path = os.path.join(PROJECT_ROOT, "html", "test_browser_controller.html")
        test_url = f"file://{test_html_path}"
        
        # Navigate to initial page
        controller.navigate_to(test_url)
        time.sleep(1)
        
        # Test opening a new tab
        print("Opening new tab...")
        new_tab_result = controller.open_tab("https://example.com")
        print(f"New tab result: {new_tab_result}")
        assert isinstance(new_tab_result, dict), "open_tab should return a dictionary"
        
        time.sleep(2)  # Wait for new tab to load
        
        # Test switching tabs
        print("Switching to tab 0...")
        switch_result = controller.switch_tab(0)
        print(f"Switch tab result: {switch_result}")
        
        # Test invalid tab switch
        invalid_switch = controller.switch_tab(99)
        print(f"Invalid switch result: {invalid_switch}")
        
        # Test closing a tab (close tab 1)
        print("Closing tab 1...")
        close_result = controller.close_tab(1)
        print(f"Close tab result: {close_result}")
        
    except Exception as e:
        print(f"Tab operations test error: {e}")
        raise
        
    finally:
        if controller:
            try:
                controller.close()
                time.sleep(1.0)  # Allow cleanup time
            except:
                pass

def test_element_interaction():
    """Test 4: Element interaction (click and input)"""
    print("\n=== Test 4: Element Interaction ===")
    
    ensure_no_event_loop()  # Prevent asyncio conflicts
    controller = None
    try:
        controller = BrowserController()
        test_html_path = os.path.join(PROJECT_ROOT, "html", "test_browser_controller.html")
        test_url = f"file://{test_html_path}"
        
        # Navigate to test page
        controller.navigate_to(test_url)
        time.sleep(1)
        
        # Get selector map to see available elements
        selector_map = controller.browser_context.get_selector_map(refresh=True)
        print(f"Found {len(selector_map)} interactive elements")
        
        # Print available elements for debugging
        for idx, element in selector_map.items():
            print(f"  Element {idx}: {element.tag_name} - {element.attributes}")
        
        # Test input text (find input field)
        input_elements = [idx for idx, el in selector_map.items() 
                         if el.tag_name.lower() in ['input', 'textarea']]
        
        if input_elements:
            input_idx = input_elements[0]
            print(f"Testing input on element {input_idx}")
            input_result = controller.input_text(input_idx, "test input")
            print(f"Input result: {input_result}")
            assert input_result == True, "Input text should succeed"
            print("✓ Input text successful")
        
        # Test click element (find button or link)
        clickable_elements = [idx for idx, el in selector_map.items() 
                            if el.tag_name.lower() in ['button', 'a', 'input']]
        
        if clickable_elements:
            click_idx = clickable_elements[0]
            print(f"Testing click on element {click_idx}")
            click_result = controller.click_element_by_index(click_idx)
            print(f"Click result: {click_result}")
            print("✓ Click element executed")
        
        # Test invalid element index
        invalid_click = controller.click_element_by_index(999)
        print(f"Invalid click result: {invalid_click}")
        assert invalid_click == False, "Invalid element click should return False"
        
    except Exception as e:
        print(f"Element interaction test error: {e}")
        raise
        
    finally:
        if controller:
            try:
                controller.close()
                time.sleep(1.0)  # Allow cleanup time
            except:
                pass

def test_command_execution():
    """Test 5: Command execution interface"""
    print("\n=== Test 5: Command Execution ===")
    
    ensure_no_event_loop()  # Prevent asyncio conflicts
    controller = None
    try:
        controller = BrowserController()
        test_html_path = os.path.join(PROJECT_ROOT, "html", "test_browser_controller.html")
        test_url = f"file://{test_html_path}"
        
        # Test execute_command with navigate_to
        nav_result = controller.execute_command("navigate_to", test_url)
        print(f"Execute navigate_to result: {nav_result}")
        assert nav_result == True, "Command execution should succeed"
        
        time.sleep(1)
        
        # Test execute_command with go_back
        back_result = controller.execute_command("go_back")
        print(f"Execute go_back result: {back_result}")
        
        # Test invalid command
        invalid_result = controller.execute_command("invalid_command")
        print(f"Invalid command result: {invalid_result}")
        assert invalid_result == False, "Invalid command should return False"
        print("✓ Command execution interface working")
        
    except Exception as e:
        print(f"Command execution test error: {e}")
        raise
        
    finally:
        if controller:
            try:
                controller.close()
                time.sleep(1.0)  # Allow cleanup time
            except:
                pass

def test_tools_integration():
    """Test 6: Tools integration"""
    print("\n=== Test 6: Tools Integration ===")
    
    ensure_no_event_loop()  # Prevent asyncio conflicts
    controller = None
    try:
        controller = BrowserController()
        
        # Test tools execution
        tools_result = controller.tools("Test reason for tools execution")
        print(f"Tools result: {tools_result}")
        assert isinstance(tools_result, dict), "Tools should return a dictionary"
        print("✓ Tools execution completed")
        
        # Test setting LLM client
        mock_llm = Mock()
        controller.set_llm_client(mock_llm)
        assert controller.llm_client == mock_llm, "LLM client should be updated"
        print("✓ LLM client updated successfully")
        
        # Test setting logging functions
        mock_log_func = Mock()
        controller.set_logging_functions(mock_log_func, "/tmp/test.log")
        assert controller.log_debug_func == mock_log_func, "Log function should be set"
        print("✓ Logging functions set successfully")
        
    except Exception as e:
        print(f"Tools integration test error: {e}")
        raise
        
    finally:
        if controller:
            try:
                controller.close()
                time.sleep(1.0)  # Allow cleanup time
            except:
                pass

def test_available_actions_with_context():
    """Test 7: Available actions based on browser context"""
    print("\n=== Test 7: Available Actions with Context ===")
    
    ensure_no_event_loop()  # Prevent asyncio conflicts
    controller = None
    try:
        controller = BrowserController()
        
        # Initial actions (no page loaded)
        initial_actions = controller.get_available_actions()
        print(f"Initial actions: {initial_actions}")
        assert "navigate_to" in initial_actions, "navigate_to should always be available"
        assert "open_tab" in initial_actions, "open_tab should always be available"
        
        # Load a page and check for new actions
        test_html_path = os.path.join(PROJECT_ROOT, "html", "test_browser_controller.html")
        test_url = f"file://{test_html_path}"
        controller.navigate_to(test_url)
        time.sleep(1)
        
        page_actions = controller.get_available_actions()
        print(f"Actions after navigation: {page_actions}")
        assert "go_back" in page_actions, "go_back should be available after navigation"
        
        # Test detailed action descriptions
        action_descriptions = controller.get_available_actions_description()
        print(f"Action descriptions length: {len(action_descriptions)}")
        assert "navigate_to" in action_descriptions, "Descriptions should include navigate_to"
        print("✓ Available actions change based on context")
        
    except Exception as e:
        print(f"Available actions test error: {e}")
        raise
        
    finally:
        if controller:
            try:
                controller.close()
                time.sleep(1.0)  # Allow cleanup time
            except:
                pass

def test_error_handling():
    """Test 8: Error handling when browser is closed"""
    print("\n=== Test 8: Error Handling ===")
    
    ensure_no_event_loop()  # Prevent asyncio conflicts
    controller = None
    try:
        controller = BrowserController()
        
        # Close browser session
        controller.close()
        
        # Try operations on closed browser - they should handle errors gracefully
        nav_result = controller.navigate_to("https://example.com")
        print(f"Navigation after close: {nav_result}")
        
        click_result = controller.click_element_by_index(0)
        print(f"Click after close: {click_result}")
        
        back_result = controller.go_back()
        print(f"Go back after close: {back_result}")
        
        print("✓ Error handling works gracefully")
        
    except Exception as e:
        print(f"Error handling test error: {e}")
        raise
        
    finally:
        # Controller is already closed, no need for cleanup
        pass

def test_end_command():
    """Test 9: End command functionality"""
    print("\n=== Test 9: End Command ===")
    
    ensure_no_event_loop()  # Prevent asyncio conflicts
    controller = None
    try:
        controller = BrowserController()
        
        # Test end command
        end_result = controller.end("Test completed")
        print(f"End command result: {end_result}")
        assert end_result == True, "End command should return True"
        print("✓ End command executed successfully")
        
        # After end, controller should be closed
        # Try a navigation to verify it's closed
        nav_result = controller.navigate_to("https://example.com")
        print(f"Navigation after end: {nav_result}")
        
    except Exception as e:
        print(f"End command test error: {e}")
        raise
        
    finally:
        # Controller should already be ended, but try to close just in case
        if controller:
            try:
                controller.close()
            except:
                pass

def run_all_tests():
    """Run all test functions"""
    print("=" * 60)
    print("BROWSER CONTROLLER TEST SUITE")
    print("=" * 60)
    
    test_functions = [
        test_basic_initialization,
        test_navigation_operations,
        test_tab_operations,
        test_element_interaction,
        test_command_execution,
        test_tools_integration,
        test_available_actions_with_context,
        test_error_handling,
        test_end_command
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
            print(f"✓ {test_func.__name__} PASSED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_func.__name__} FAILED: {e}")
        except AssertionError as e:
            failed += 1
            print(f"✗ {test_func.__name__} ASSERTION FAILED: {e}")
        
        # Add delay between tests to ensure complete cleanup
        print("Waiting for cleanup...")
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return passed, failed

if __name__ == "__main__":
    # Run individual test for debugging
    import sys
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name in globals() and callable(globals()[test_name]):
            print(f"Running single test: {test_name}")
            globals()[test_name]()
        else:
            print(f"Test function '{test_name}' not found")
    else:
        # Run all tests
        run_all_tests()
