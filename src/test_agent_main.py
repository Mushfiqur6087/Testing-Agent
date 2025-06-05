# filepath: /home/mushfiqur/vscode/Testing-Agent/src/test_agent_main.py
import os
import sys
import time
from typing import List, Dict, Any

# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.test_agent import TestAgent
from src.agent.instruction_agent.agent import InstructionAgent


class TestAgentMain:
    """
    Main agent class that orchestrates test case generation and execution.
    """
    
    def __init__(self, api_key: str, max_actions: int = 15, debug: bool = False):
        self.api_key = api_key
        self.max_actions = max_actions
        self.debug = debug
        self.instruction_agent = None
        
    def initialize(self):
        """Initialize the instruction agent."""
        self.instruction_agent = InstructionAgent(api_key=self.api_key)
            
    def generate_test_cases(self, test_case_description: str) -> List[Dict[str, Any]]:
        """
        Generate multiple test cases from a single test case description using the instruction agent.
        
        Args:
            test_case_description (str): Description of the test scenario/requirements
            
        Returns:
            list: List of generated test case dictionaries
        """
        if not self.instruction_agent:
            self.initialize()
            
        try:
            # Process the test case description to generate multiple test scenarios
            self.instruction_agent.process_test_case(test_case_description)
            
            # Get the generated test cases as a list
            test_cases = self.instruction_agent.get_test_cases_list()
            
            return test_cases
            
        except Exception as e:
            print(f"\n❌ Error generating test cases: {e}")
            if "quota" in str(e).lower() or "limit" in str(e).lower() or "rate" in str(e).lower():
                print("🚨 This looks like an API rate limit or quota issue during test case generation!")
            raise
            
    def execute_test_case(self, test_case: Dict[str, Any]):
        """
        Execute a single test case using TestAgent.
        
        Args:
            test_case (dict): Test case dictionary containing test details
        """
        # Extract test information
        steps_or_input = test_case.get('steps_or_input', '')
        expected_outcome = test_case.get('expected_outcome', '')
        
        # Use steps_or_input as user_goal
        user_goal = steps_or_input+ "\n DETERMINE whether this test can be successfully executed given the current requirements and implementation, or if there are any errors, inconsistencies, or missing validations in the requirements or the form itself."
        
        
        try:
            # Initialize a new TestAgent for this test case
            test_agent = TestAgent(
                api_key=self.api_key,
                max_actions=self.max_actions,
                debug=self.debug
            )
            # Initialize and execute the test - same as main.py
            test_agent.initialize()
            results = test_agent.execute_plan(user_goal, expected_outcome)
            print(f"\nTest Case '{test_case.get('test_name', 'N/A')}' executed successfully.")
            return results
            
        except Exception as e:
            raise
        finally:
            # Always cleanup the test agent
            test_agent.cleanup()
    
    def execute_all_test_cases(self, test_cases: List[Dict[str, Any]]):
        """
        Execute all test cases.
        
        Args:
            test_cases (list): List of test cases to execute
        """
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nExecuting Test Case {i}")
            self.execute_test_case(test_case)
            
            # Add 40-second delay between test cases to avoid API quota limits
            if i < len(test_cases):  # Don't wait after the last test case
                print(f"Waiting 40 seconds before next test case to avoid API quota limits...")
                time.sleep(40)
            



def main():
    """
    Example usage of TestAgentMain.
    """
    # Configuration
    API_KEY = os.getenv('GEMINI_API_KEY')
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    # Example test case description
    test_description = """
Go to file:///home/mushfiqur/vscode/Testing-Agent/html/test_page.html
Test the signup form functionality and verify that emails contain @ and password and confirm password fields match.
If not then alert will be shown.
"""
    
    # Initialize the main agent
    main_agent = TestAgentMain(
        api_key=API_KEY,
        max_actions=10,
        debug=True
    )
    
    try:
        # Generate test cases
        test_cases = main_agent.generate_test_cases(test_description)
        # for i, test_case in enumerate(test_cases, 1):
            # print(f"\nTest Case {i}:")
            # print(f"  Name: {test_case.get('test_name', 'N/A')}")
            # print(f"  Steps: {test_case.get('steps_or_input', 'N/A')[:100]}...")
            # print(f"  Expected Outcome: {test_case.get('expected_outcome', 'N/A')}")
        
        # Execute all test cases
        main_agent.execute_all_test_cases(test_cases)
        
    except Exception as e:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()