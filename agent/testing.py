# Agent Usage Example with TestAgent Class
import sys
import time
from pathlib import Path

# Add parent directory to Python path to import controller module
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from test_agent import TestAgent

# Configuration - Define once, use everywhere
API_KEY = "AIzaSyAqCma6o6JFNFEPM_Tq4OMpeKtUNLBdmvA"  # Replace with actual API key

USER_GOAL = """
Navigate to the login form test page and test the login functionality:
1. Go to file:///home/mushfiqur/vscode/Testing-Agent/html/login_form.html
2. Fill in the email field with 'test@example.com'
3. Fill in the password field with 'password123'
4. Click the login button
"""

def simple_test_agent():
    """Simple example of TestAgent usage."""
    
    test_agent = TestAgent(api_key=API_KEY, max_actions=15, debug=True)
    
    try:
        # Initialize and execute
        test_agent.initialize()
        results = test_agent.execute_plan(USER_GOAL)
        
        print(f"✅ Results: {results}")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
    
    finally:
        test_agent.cleanup()

if __name__ == "__main__":
    simple_test_agent()
