# Agent Usage Example with TestAgent Class
import sys
import os


# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


from src.test_agent import TestAgent

# Configuration - Define once, use everywhere
API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")

USER_GOAL = """
Navigate to the login form test page and test the login functionality:
1. Go to file:///home/mushfiqur/vscode/Testing-Agent/html/login_form.html
2. Fill in the email field with 'test@example.com'
3. Fill in the password field with 'password123'
4. Click the login button
5. Verify that your test is successful
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
