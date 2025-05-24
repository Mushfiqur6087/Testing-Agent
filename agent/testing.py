# Agent Usage Example
import sys
from pathlib import Path

# Add parent directory to Python path to import controller module
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from agent import Agent
from llm import GeminiFlashClient
from controller.browser_controller import BrowserController
import time

def test_agent():
    """Example of how to use the completed Agent class."""
    
    # Initialize LLM client
    llm = GeminiFlashClient(
        api_key="AIzaSyAqCma6o6JFNFEPM_Tq4OMpeKtUNLBdmvA",  # Replace with actual API key
        model_name="models/gemini-1.5-flash"
    )
      # Initialize Agent with debug enabled
    agent = Agent(llm, max_actions=20, debug=True)
    
    # Initialize Browser Controller
    browser_controller = BrowserController()
    agent.set_browser_controller(browser_controller)
    
    try:        # Execute a plan to test a login form
        user_goal = """
Navigate to the login form test page and test the login functionality:
1. Go to file://d:/Testing Agent/html/login_form.html
2. Fill in the email field with 'test@example.com'
3. Fill in the password field with 'password123'
4. Click the login button
"""
        
        execution_log = agent.execute_plan(user_goal)
        
        # Print execution results
        print("=== EXECUTION LOG ===")
        for i, log_entry in enumerate(execution_log, 1):
            print(f"\nStep {i}:")
            print(f"  LLM Response: {log_entry.get('llm_response', {}).get('current_state', {})}")
            if 'action_results' in log_entry:
                for j, action_result in enumerate(log_entry['action_results']):
                    print(f"  Action {j+1}: {action_result['action']}")
                    print(f"  Result: {action_result['result']}")
        
        # Get session summary
        summary = agent.get_session_summary()
        print(f"\n=== SESSION SUMMARY ===")
        print(f"Duration: {summary['session_duration_seconds']:.2f} seconds")
        print(f"Total steps: {summary['total_steps']}")
        print(f"Successful steps: {summary['successful_steps']}")
        print(f"Failed steps: {summary['failed_steps']}")
        print(f"Current URL: {summary['current_url']}")
        
        # Save session log
        filename = agent.save_session_log()
        print(f"\nSession log saved to: {filename}")
        
    except Exception as e:
        print(f"Error during agent execution: {e}")
    
    finally:
        # Clean up
        # before closing wait 10 seconds to see the final state
        time.sleep(10)
        browser_controller.close()
        print("Browser session closed.")

if __name__ == "__main__":
    test_agent()
