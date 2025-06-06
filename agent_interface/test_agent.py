
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import the required classes from the agent package
from src.agent.main_agent.agent import Agent
from src.agent.core_utils.llm import GeminiFlashClient
from src.agent.core_utils.test_result_analyzer import TestResultAnalyzer
from src.controller.browser_controller import BrowserController


class TestAgent:
    """
    A simple wrapper class for the Agent that provides controlled execution with stopping capabilities.
    """
    
    def __init__(self, api_key, max_actions=10, debug=False):
        """
        Initialize the TestAgent.
        
        Args:
            api_key (str): API key for the LLM
            max_actions (int): Maximum number of actions to execute
            debug (bool): Enable debug mode
        """
        self.api_key = api_key
        self.max_actions = max_actions
        self.debug = debug
        
        # Initialize components
        self.llm = None
        self.agent = None
        self.browser_controller = None
        self.test_analyzer = None
        
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
        
    def initialize(self):
        """Initialize the agent and browser controller."""
        try:
            # Initialize LLM client
            self.llm = GeminiFlashClient(api_key=self.api_key)
            
            # Initialize test result analyzer
            self.test_analyzer = TestResultAnalyzer(llm_client=self.llm)
            
            # Initialize browser controller with LLM client for intelligent tools
            self.browser_controller = BrowserController(llm_client=self.llm)
            
            # Initialize agent with LLM instance
            self.agent = Agent(
                llm=self.llm,
                max_actions=self.max_actions,
                debug=self.debug
            )
            
            # Set browser controller for the agent (LLM will be passed automatically)
            self.agent.set_browser_controller(self.browser_controller)
                
        except Exception as e:
            print(f"❌ Failed to initialize TestAgent: {e}")
            raise
            
    def cleanup(self):
        """Clean up resources and close browser session."""
        try:
            # Close browser session properly
            if self.browser_controller and hasattr(self.browser_controller, 'browser_context'):
                self.browser_controller.browser_context.close()
                
        except Exception as e:
            pass
    
    def execute_plan(self, user_goal, expected_outcome):
        """
        Execute the agent plan.
        
        Args:
            user_goal (str): The goal for the agent to achieve
            expected_outcome (str): The expected outcome of the test
            
        Returns:
            Results from agent execution including test analysis
        """
        if not self.agent:
            self.initialize()
            
        try:
            # Execute the plan
            results = self.agent.execute_plan(user_goal)
            
            # Analyze the test results using the memory from execution
            if hasattr(self.agent, 'memory') and self.agent.memory:
                self.test_analyzer.analyze_test_execution(
                    memory=self.agent.memory,
                    original_test_goal=user_goal,
                    expected_outcome=expected_outcome
                )                
            return results
            
        except Exception as e:
            raise
