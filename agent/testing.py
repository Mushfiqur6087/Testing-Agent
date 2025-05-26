import sys
from pathlib import Path
import time

# Add the parent directory to Python path to allow importing modules from the project root.
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

# Import necessary modules for controlling the agent and browser
from agent.agent import Agent
from agent.llm import GeminiFlashClient
from controller.browser_controller import BrowserController

def test_agent():
    """
    Example of how to use the completed Agent class for executing a login form test.
    The function initializes the agent and browser controller, executes a series of steps
    to simulate interacting with a login page, and logs the results.
    """

    # Initialize LLM (Large Language Model) client with a provided API key and model name
    llm = GeminiFlashClient(
        api_key="AIzaSyAqCma6o6JFNFEPM_Tq4OMpeKtUNLBdmvA",  # Replace with your actual API key
        model_name="models/gemini-1.5-flash"
    )
    
    # Initialize the Agent with the LLM client and set debug mode and max actions limit
    agent = Agent(llm, max_actions=20, debug=True)
    
    # Initialize the Browser Controller for managing browser sessions
    browser_controller = BrowserController()
    
    # Set the browser controller for the agent to interact with the browser
    agent.set_browser_controller(browser_controller)

    try:
        # Define the file path to the HTML login form
        html_path = project_root / "html" / "login_form.html"
        file_url = f"file:///{html_path.as_posix()}"

        # Define the user goal that outlines the steps for testing the login functionality
        user_goal = f"""
        Navigate to the login form test page and test the login functionality:
        1. Go to {file_url}
        2. Fill in the email field with 'test@example.com'
        3. Fill in the password field with 'password123'
        4. Click the login button
        """
        
        # Execute the plan using the agent and capture the log of actions and results
        execution_log = agent.execute_plan(user_goal)
        
        # Print the detailed execution log with each step and result
        print("=== EXECUTION LOG ===")
        for i, log_entry in enumerate(execution_log, 1):
            print(f"\nStep {i}:")
            print(f"  LLM Response: {log_entry.get('llm_response', {}).get('current_state', {})}")
            
            # Print the result of each action taken by the agent
            if 'action_results' in log_entry:
                for j, action_result in enumerate(log_entry['action_results']):
                    print(f"  Action {j + 1}: {action_result['action']}")
                    print(f"  Result: {action_result['result']}")
        
        # After the test, get the session summary (duration, successful/failed steps, etc.)
        summary = agent.get_session_summary()
        print(f"\n=== SESSION SUMMARY ===")
        print(f"Duration: {summary['session_duration_seconds']:.2f} seconds")
        print(f"Total steps: {summary['total_steps']}")
        print(f"Successful steps: {summary['successful_steps']}")
        print(f"Failed steps: {summary['failed_steps']}")
        print(f"Current URL: {summary['current_url']}")
        
        # Save the session log to a file for later review and analysis
        filename = agent.save_session_log()
        print(f"\nSession log saved to: {filename}")

    except Exception as e:
        # Catch any exceptions that occur during agent execution and print the error message
        print(f"Error during agent execution: {e}")

    finally:
        # Clean up resources by waiting for 10 seconds to observe the final state of the session
        time.sleep(10)
        
        # Close the browser session after the test is complete
        browser_controller.close()
        print("Browser session closed.")
        
        
def perform_web_testing(url, task_description):
    """
    Runs the agent on the given URL with the provided task description.
    """

    llm = GeminiFlashClient(
        api_key="AIzaSyAqCma6o6JFNFEPM_Tq4OMpeKtUNLBdmvA",  # Replace with your actual API key
        model_name="models/gemini-1.5-flash"
    )
    agent = Agent(llm, max_actions=20, debug=True)
    browser_controller = BrowserController()
    agent.set_browser_controller(browser_controller)

    try:
        user_goal = f"{task_description}\nStart URL: {url}"
        execution_log = agent.execute_plan(user_goal)
        print("=== EXECUTION LOG ===")
        for i, log_entry in enumerate(execution_log, 1):
            print(f"\nStep {i}:")
            print(f"  LLM Response: {log_entry.get('llm_response', {}).get('current_state', {})}")
            if 'action_results' in log_entry:
                for j, action_result in enumerate(log_entry['action_results']):
                    print(f"  Action {j + 1}: {action_result['action']}")
                    print(f"  Result: {action_result['result']}")
        summary = agent.get_session_summary()
        print(f"\n=== SESSION SUMMARY ===")
        print(f"Duration: {summary['session_duration_seconds']:.2f} seconds")
        print(f"Total steps: {summary['total_steps']}")
        print(f"Successful steps: {summary['successful_steps']}")
        print(f"Failed steps: {summary['failed_steps']}")
        print(f"Current URL: {summary['current_url']}")
        filename = agent.save_session_log()
        print(f"\nSession log saved to: {filename}")
    except Exception as e:
        print(f"Error during agent execution: {e}")
    finally:
        time.sleep(10)
        browser_controller.close()
        print("Browser session closed.")


if __name__ == "__main__":
    # Start the agent test when the script is executed
    test_agent()
