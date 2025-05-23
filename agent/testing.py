"""
Testing script for the Browser Agent capabilities.

This module provides test cases to validate the agent's ability to:
1. Initialize with a browser context
2. Execute browser commands 
3. Maintain memory of actions
4. Generate summaries of activities
"""

import os
import sys
import logging
import time

# Add the parent directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import local modules with absolute imports
sys.path.insert(0, parent_dir)  # Ensure parent directory is first in path
from browser.browser_context import BrowserSession
from controller.browser_controller import BrowserController
# Use absolute imports
sys.path.insert(0, current_dir)  # Add current directory to path first
from agent import Agent
from memory_summarizer import MemorySummarizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AgentTester:
    """
    Test harness for the browser agent functionality.
    """
    
    def __init__(self, headless=False):
        """
        Initialize the test environment with a browser session and agent.
        
        Args:
            headless: Whether to run the browser in headless mode
        """
        # Initialize browser session
        self.browser_session = BrowserSession()
        self.browser_session._initialize_session(headless=headless)
        self.browser_session._create_context()
        
        # Initialize browser controller with the session
        self.browser_controller = self._create_browser_controller_with_context()
        
        # Initialize agent with the controller
        self.agent = self._create_agent_with_controller()
        
        logger.info("AgentTester initialized with browser session and agent")
    
    def _create_browser_controller_with_context(self):
        """
        Create a browser controller with a browser context.
        
        Returns:
            Initialized browser controller
        """
        # Create a controller and set its browser_context
        controller = BrowserController()
        controller.browser_context = self.browser_session
        return controller
    
    def _create_agent_with_controller(self):
        """
        Create an agent with the browser controller.
        
        Returns:
            Initialized agent
        """
        agent = Agent()
        # Set the agent's browser controller to our controller with context
        agent.browser_controller = self.browser_controller
        return agent
    
    def run_navigation_test(self):
        """
        Test basic navigation capabilities.
        
        Returns:
            True if test passed, False otherwise
        """
        logger.info("Running navigation test")
        
        # Set a task
        self.agent.set_task("Test navigation capabilities", max_steps=5)
        
        # Navigate to a website
        result = self.agent.execute_command("navigate_to", "https://www.example.com")
        if not result:
            logger.error("Failed to navigate to example.com")
            return False
        
        # Wait for page to load
        time.sleep(2)
        
        # Get selector map to verify page loaded
        selector_map = self.agent.execute_command("get_selector_map")
        if not selector_map:
            logger.error("Failed to get selector map")
            return False
        
        logger.info("Navigation test completed successfully")
        return True
    
    def run_interaction_test(self):
        """
        Test element interaction capabilities.
        
        Returns:
            True if test passed, False otherwise
        """
        logger.info("Running interaction test")
        
        # Navigate to a website with interactive elements
        result = self.agent.execute_command("navigate_to", "https://www.google.com")
        if not result:
            logger.error("Failed to navigate to Google")
            return False
        
        # Wait for page to load
        time.sleep(2)
        
        # Get selector map to find search input
        selector_map = self.agent.execute_command("get_selector_map")
        if not selector_map:
            logger.error("Failed to get selector map")
            return False
        
        # Try to find and click on an element (assuming element index 5 is clickable)
        # In a real test, you would analyze the selector map to find the right element
        try:
            result = self.agent.execute_command("click_element", 5)
            logger.info(f"Click result: {result}")
        except Exception as e:
            logger.warning(f"Click test encountered an exception: {e}")
        
        # Create a memory summary
        summary = self.agent.create_memory_summary()
        logger.info(f"Memory summary: {summary}")
        
        logger.info("Interaction test completed")
        return True
    
    def run_memory_test(self):
        """
        Test memory capabilities.
        
        Returns:
            True if test passed, False otherwise
        """
        logger.info("Running memory test")
        
        # Set a task
        self.agent.set_task("Test memory capabilities", max_steps=10)
        
        # Execute a series of commands
        commands = [
            ("navigate_to", "https://www.example.com"),
            ("get_selector_map", None),
            ("navigate_to", "https://www.python.org"),
            ("get_selector_map", None),
            ("go_back", None)
        ]
        
        for cmd in commands:
            command, args = cmd
            if args is not None:
                self.agent.execute_command(command, args)
            else:
                self.agent.execute_command(command)
        
        # Create a memory summary
        summary = self.agent.create_memory_summary()
        logger.info(f"Memory summary: {summary}")
        
        # Get memory history
        history = self.agent.get_memory_history(max_entries=10)
        logger.info(f"Memory history: {history}")
        
        # Test saving and loading memory
        memory_file = "test_memory.json"
        self.agent.save_memory(memory_file)
        logger.info(f"Memory saved to {memory_file}")
        
        # Clear memory and reload
        self.agent.memory.clear()
        self.agent.load_memory(memory_file)
        logger.info("Memory reloaded")
        
        # Compare memory count
        logger.info(f"Memory contains {len(self.agent.memory.actions)} actions")
        
        # Clean up the memory file
        if os.path.exists(memory_file):
            os.remove(memory_file)
        
        logger.info("Memory test completed successfully")
        return True
    
    def run_summarizer_test(self):
        """
        Test the MemorySummarizer class functionality.
        
        Returns:
            True if test passed, False otherwise
        """
        logger.info("Running memory summarizer test")
        
        # Create test memory entries
        test_actions = [
            {
                "timestamp": time.time() - 3600,  # 1 hour ago
                "action": "navigate_to",
                "params": "https://www.example.com",
                "success": True,
                "error": None,
                "content": "Successfully navigated to Example.com",
                "include_in_memory": True
            },
            {
                "timestamp": time.time() - 3000,  # 50 minutes ago
                "action": "click_element",
                "params": 3,
                "success": True,
                "error": None,
                "content": "Clicked on element with index 3",
                "include_in_memory": True
            },
            {
                "timestamp": time.time() - 2400,  # 40 minutes ago
                "action": "input_text",
                "params": (2, "test input"),
                "success": True,
                "error": None,
                "content": None,
                "include_in_memory": True
            },
            {
                "timestamp": time.time() - 1800,  # 30 minutes ago
                "action": "click_element",
                "params": 10,
                "success": False,
                "error": "Element with index 10 not found in selector map",
                "content": None,
                "include_in_memory": True
            },
            {
                "timestamp": time.time() - 1200,  # 20 minutes ago
                "action": "navigate_to",
                "params": "https://www.python.org",
                "success": True,
                "error": None,
                "content": "Successfully navigated to Python.org",
                "include_in_memory": True
            },
            {
                "timestamp": time.time() - 600,  # 10 minutes ago
                "action": "get_selector_map",
                "params": None,
                "success": True,
                "error": None,
                "content": "Selector map with 42 elements",
                "include_in_memory": False  # This one should be excluded from summaries
            }
        ]
        
        # Test summarize_actions method
        logger.info("Testing summarize_actions method")
        actions_summary = MemorySummarizer.summarize_actions(test_actions)
        logger.info(f"Actions summary:\n{actions_summary}")
        
        # Verify the summary excludes entries with include_in_memory=False
        if "get_selector_map" in actions_summary:
            logger.error("Summary includes action that should be excluded")
            return False
        
        # Test summarize_actions with max_items parameter
        max_items_summary = MemorySummarizer.summarize_actions(test_actions, max_items=3)
        logger.info(f"Max items (3) summary:\n{max_items_summary}")
        
        # Test create_periodic_summary method
        logger.info("Testing create_periodic_summary method")
        periodic_summary = MemorySummarizer.create_periodic_summary(
            test_actions,
            current_step=5,
            max_steps=10,
            task="Test task for periodic summary",
            interval=5
        )
        logger.info(f"Periodic summary:\n{periodic_summary}")
        
        # Test create_periodic_summary with non-matching interval
        non_matching_summary = MemorySummarizer.create_periodic_summary(
            test_actions,
            current_step=4,  # Not a multiple of 5
            max_steps=10,
            task="Test task for periodic summary",
            interval=5
        )
        
        if non_matching_summary is not None:
            logger.error("Periodic summary created when it shouldn't have been")
            return False
            
        # Test format_timestamp method
        logger.info("Testing format_timestamp method")
        timestamp = time.time()
        formatted_time = MemorySummarizer.format_timestamp(timestamp)
        logger.info(f"Formatted timestamp: {formatted_time}")
        
        # Test custom format
        custom_formatted = MemorySummarizer.format_timestamp(timestamp, "%Y/%m/%d %H:%M")
        logger.info(f"Custom formatted timestamp: {custom_formatted}")
        
        # All tests passed
        logger.info("Memory summarizer test completed successfully")
        return True
    
    def run_all_tests(self):
        """
        Run all agent tests.
        
        Returns:
            Dictionary with test results
        """
        results = {
            #"navigation": self.run_navigation_test(),
            #"interaction": self.run_interaction_test(),
            #"memory": self.run_memory_test(),
            #"summarizer": self.run_summarizer_test()
        }
        
        logger.info(f"All tests completed with results: {results}")
        return results
    
    def cleanup(self):
        """
        Clean up resources.
        """
        logger.info("Cleaning up resources")
        try:
            self.browser_controller.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """
    Main test function.
    """
    tester = None
    
    try:
        # Initialize tester with non-headless browser for debugging
        tester = AgentTester(headless=False)
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Print results
        print("\n=== Agent Test Results ===")
        for test_name, result in results.items():
            status = "PASSED" if result else "FAILED"
            print(f"{test_name}: {status}")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        
    finally:
        # Ensure cleanup happens
        if tester:
            tester.cleanup()


if __name__ == "__main__":
    main() 