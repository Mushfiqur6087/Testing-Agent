# TestAgent Class for Controlled Agent Execution
import sys
from pathlib import Path

# Add parent directory to Python path to import modules
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from agent import Agent
from llm import GeminiFlashClient
from controller.browser_controller import BrowserController

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
            if self.debug:
                print("🔧 Initializing TestAgent...")
            
            # Initialize LLM client
            self.llm = GeminiFlashClient(api_key=self.api_key)
            
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
            
            if self.debug:
                print("✅ TestAgent initialized successfully with LLM-powered tools")
                
        except Exception as e:
            print(f"❌ Failed to initialize TestAgent: {e}")
            raise
            
    def cleanup(self):
        """Clean up resources and close browser session."""
        try:
            if self.debug:
                print("🧹 Cleaning up TestAgent...")
            
            # Close browser if it exists
            if self.browser_controller and hasattr(self.browser_controller, 'driver') and self.browser_controller.driver:
                self.browser_controller.driver.quit()
                if self.debug:
                    print("🌐 Browser session closed")
            
            if self.debug:
                print("✅ TestAgent cleanup completed")
                
        except Exception as e:
            if self.debug:
                print(f"⚠️ Error during cleanup: {e}")
    
    def execute_plan(self, user_goal):
        """
        Execute the agent plan.
        
        Args:
            user_goal (str): The goal for the agent to achieve
            
        Returns:
            Results from agent execution
        """
        if not self.agent:
            self.initialize()
            
        try:
            if self.debug:
                print(f"🚀 Starting execution...")
                print(f"📋 Goal: {user_goal}")
            
            # Execute the plan
            results = self.agent.execute_plan(user_goal)
            
            if self.debug:
                print("✅ Execution completed successfully")
                
            return results
            
        except Exception as e:
            if self.debug:
                print(f"❌ Execution failed: {e}")
            raise
    
    def stop(self):
        """Stop the agent by closing the browser session."""
        if self.debug:
            print("🛑 Stopping agent...")
        
        if self.browser_controller and hasattr(self.browser_controller, 'driver') and self.browser_controller.driver:
            try:
                # Execute an "end" action to properly close
                self.browser_controller.execute_command({"action": "end"})
                if self.debug:
                    print("✅ Agent stopped successfully")
            except Exception as e:
                if self.debug:
                    print(f"⚠️ Error during stop: {e}")
        else:
            if self.debug:
                print("⚠️ No active browser session to stop")
