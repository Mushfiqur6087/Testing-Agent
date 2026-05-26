
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import the required classes from the agent package
from src.agent.main_agent.agent import Agent
from src.agent.core_utils.llm import LLMClient
from src.agent.core_utils.test_result_analyzer import TestResultAnalyzer
from src.agent.core_utils.logging_utils import debug_logger
from src.controller.browser_controller import BrowserController


class TestAgent:
    """
    A simple wrapper class for the Agent that provides controlled execution with stopping capabilities.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash", provider: str = "gemini",
                 max_actions: int = 10, debug: bool = False, headless: bool = True,
                 test_case_name: str = "test_case"):
        """
        Initialize the TestAgent.
        
        Args:
            model (str): Model name (e.g. "gpt-5-mini", "claude-sonnet-4-20250514")
            provider (str): Provider name (e.g. "openai", "anthropic", "gemini")
            max_actions (int): Maximum number of actions to execute
            debug (bool): Enable debug mode
            headless (bool): Run browser in headless mode (False = visible browser)
            test_case_name (str): Name of the test case — used to create the log subfolder
        """
        self.model = model
        self.provider = provider
        self.max_actions = max_actions
        self.debug = debug
        self.headless = headless
        self.test_case_name = test_case_name
        
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
            # Initialize LLM client via LiteLLM
            self.llm = LLMClient(model=self.model, provider=self.provider)
            
            # Initialize test result analyzer
            self.test_analyzer = TestResultAnalyzer(llm_client=self.llm)
            
            # Initialize browser controller with LLM client for intelligent tools
            self.browser_controller = BrowserController(llm_client=self.llm, headless=self.headless)
            
            # Initialize agent with LLM instance — debug log goes into the test case subfolder
            tc_dir = debug_logger.get_test_case_dir(self.test_case_name)
            self.agent = Agent(
                llm=self.llm,
                max_actions=self.max_actions,
                debug=self.debug
            )
            # Override the debug file path to use the test-case-specific directory
            if self.debug:
                self.agent.debug_file = debug_logger.get_debug_file_path(
                    "agent", debug_file_prefix=self.test_case_name, output_dir=tc_dir
                )
                from src.agent.core_utils.memory import EnhancedMemory
                self.agent.memory = EnhancedMemory(debug_file_path=self.agent.debug_file)
            
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
                    expected_outcome=expected_outcome,
                    test_case_name=self.test_case_name,
                )                
            return results
            
        except Exception as e:
            raise
