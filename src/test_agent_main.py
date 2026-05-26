# filepath: /home/mushfiqur/Documents/Testing-Agent/src/test_agent_main.py
import os
import sys
import time
import json
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load API keys from env/.env automatically
_ENV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "env", ".env"
)
load_dotenv(_ENV_FILE)

# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.test_agent import TestAgent


class TestAgentMain:
    """
    Main agent class that orchestrates test execution.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash", provider: str = "gemini",
                 max_actions: int = 15, debug: bool = False, headless: bool = True):
        self.model = model
        self.provider = provider
        self.max_actions = max_actions
        self.debug = debug
        self.headless = headless
        
    def generate_test_cases(self, test_case_description: str) -> List[Dict[str, Any]]:
        """
        Wrap a single test description as a single test case, ready for execution.
        No LLM expansion — the description is used as-is.
        
        Args:
            test_case_description (str): Description of the test scenario
            
        Returns:
            list: A list containing one test case dictionary
        """
        if not test_case_description.strip():
            raise ValueError("Test case description cannot be empty")
        
        return [
            {
                "test_name": "test_case_1",
                "steps_or_input": test_case_description.strip(),
                "expected_outcome": "",
                "reason_for_failure": "",
            }
        ]

    def load_test_cases(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Load test cases from a JSON file.

        Args:
            filepath (str): Path to the JSON file containing a list of test case dicts.

        Returns:
            list: List of test case dictionaries read from the file.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Test cases file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)

        if not isinstance(test_cases, list):
            raise ValueError(f"Expected a JSON array in {filepath}, got {type(test_cases).__name__}")

        print(f"Loaded {len(test_cases)} test case(s) from {filepath}")
        return test_cases

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
        user_goal = steps_or_input + "\n DETERMINE whether this test can be successfully executed given the current requirements and implementation, or if there are any errors, inconsistencies, or missing validations in the requirements or the form itself."
        
        
        try:
            # Initialize a new TestAgent for this test case
            test_agent = TestAgent(
                model=self.model,
                provider=self.provider,
                max_actions=self.max_actions,
                debug=self.debug,
                headless=self.headless,
                test_case_name=test_case.get('test_name', 'test_case'),
            )
            # Initialize and execute the test
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


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Testing Agent — AI-powered browser test automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  python -m src.test_agent_main --model gpt-5-mini --provider openai
  python -m src.test_agent_main --model claude-sonnet-4-20250514 --provider anthropic
  python -m src.test_agent_main --model gemini-2.0-flash --provider gemini
  python -m src.test_agent_main --model google/gemini-flash-1.5 --provider openrouter
        """,
    )
    parser.add_argument(
        "--model", type=str, default="gemini-2.0-flash",
        help="Model name (default: gemini-2.0-flash)",
    )
    parser.add_argument(
        "--provider", type=str, default="gemini",
        help="LLM provider: openai, anthropic, gemini, openrouter, etc. (default: gemini)",
    )
    parser.add_argument(
        "--max-actions", type=int, default=10,
        help="Maximum browser actions per test case (default: 10)",
    )
    parser.add_argument(
        "--test-file", type=str, default=None,
        help="Path to test_cases.json (default: test_cases/test_cases.json)",
    )
    parser.add_argument(
        "--no-headless", dest="headless", action="store_false", default=True,
        help="Show the browser window (default: headless / invisible)",
    )
    parser.add_argument(
        "--debug", action="store_true", default=True,
        help="Enable debug logging (default: True)",
    )
    return parser.parse_args()


def main():
    """
    Entry point — parses CLI args and runs the agent.
    """
    args = parse_args()

    # Resolve test file path
    if args.test_file:
        test_cases_file = args.test_file
    else:
        test_cases_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "test_cases", "test_cases.json",
        )

    print(f"🤖 Testing Agent")
    print(f"   Provider : {args.provider}")
    print(f"   Model    : {args.model}")
    print(f"   Headless : {args.headless}")
    print(f"   Test file: {test_cases_file}")
    print()

    # Initialize the main agent
    main_agent = TestAgentMain(
        model=args.model,
        provider=args.provider,
        max_actions=args.max_actions,
        debug=args.debug,
        headless=args.headless,
    )

    try:
        # Load test cases from JSON file
        test_cases = main_agent.load_test_cases(test_cases_file)

        # Execute all test cases
        main_agent.execute_all_test_cases(test_cases)

    except Exception as e:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()