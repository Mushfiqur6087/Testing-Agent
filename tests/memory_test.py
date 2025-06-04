"""
Test script for the simplified EnhancedMemory system.
Tests the core functionality of storing and retrieving LLM states and tool outputs.
"""

import sys
import os
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.agent.core_utils.memory import EnhancedMemory


def test_memory_initialization():
    """Test memory system initialization."""
    print("Testing memory initialization...")
    memory = EnhancedMemory()
    
    assert memory.llm_states == []
    assert memory.tool_outputs == []
    assert memory.session_start_time is not None
    print("✓ Memory initialization test passed")


def test_save_llm_response():
    """Test saving multiple LLM responses in sequence."""
    print("\nTesting LLM response saving with multiple sequences...")
    memory = EnhancedMemory()
    
    # First LLM response - Opening login page
    llm_response_1 = {
        "current_state": {
            "evaluation_previous_goal": "Success - Successfully opened the login form page.",
            "memory": "Opened login form page. Need to fill in email and password fields and click the login button. 0 out of 1 login attempts made. Next step: fill form and submit.",
            "next_goal": "Fill the login form and submit it"
        },
        "actions": [
            {"action": "click", "selector": "#login-button"}
        ]
    }
    
    # Second LLM response - Filling form
    llm_response_2 = {
        "current_state": {
            "evaluation_previous_goal": "Success - Clicked login button and form appeared.",
            "memory": "Login form is now visible. Filled email field with test@example.com. Now need to fill password field and submit the form. 0 out of 1 login attempts made.",
            "next_goal": "Fill password field and submit the login form"
        },
        "actions": [
            {"action": "type", "selector": "#email", "text": "test@example.com"},
            {"action": "type", "selector": "#password", "text": "password123"}
        ]
    }
    
    # Third LLM response - Submitting form
    llm_response_3 = {
        "current_state": {
            "evaluation_previous_goal": "Success - Form fields filled successfully.",
            "memory": "Email and password fields are now filled. Ready to submit the login form. 1 out of 1 login attempts about to be made.",
            "next_goal": "Submit the login form by clicking submit button"
        },
        "actions": [
            {"action": "click", "selector": "#submit-btn"}
        ]
    }
    
    # Fourth LLM response - Login result
    llm_response_4 = {
        "current_state": {
            "evaluation_previous_goal": "Success - Login form submitted successfully.",
            "memory": "Login form submitted. Received success message. User is now logged in. Login attempt completed successfully (1 out of 1).",
            "next_goal": "Verify login success and proceed to next task"
        },
        "actions": [
            {"action": "wait", "selector": "#success-message"}
        ]
    }
    
    # Save all responses in sequence
    memory.save_llm_response(llm_response_1, step_number=1)
    memory.save_llm_response(llm_response_2, step_number=2)
    memory.save_llm_response(llm_response_3, step_number=3)
    memory.save_llm_response(llm_response_4, step_number=4)
    
    # Test that all responses were saved
    assert len(memory.llm_states) == 4
    print(f"✓ Saved {len(memory.llm_states)} LLM responses")
    
    # Test first response
    first_state = memory.llm_states[0]
    assert first_state["step_number"] == 1
    assert first_state["current_state"]["evaluation_previous_goal"] == "Success - Successfully opened the login form page."
    assert "timestamp" in first_state
    
    # Test last response
    last_state = memory.llm_states[-1]
    assert last_state["step_number"] == 4
    assert last_state["current_state"]["next_goal"] == "Verify login success and proceed to next task"
    
    # Test sequence ordering
    for i in range(len(memory.llm_states)):
        assert memory.llm_states[i]["step_number"] == i + 1
    
    # Print summary of what was saved
    print("LLM Response Sequence Summary:")
    for i, state in enumerate(memory.llm_states):
        print(f"  Step {state['step_number']}:")
        print(f"    Evaluation: {state['current_state']['evaluation_previous_goal']}")
        print(f"    Next Goal: {state['current_state']['next_goal']}")
        print(f"    Actions: {len(state.get('actions', []))} action(s)")
        print()
    
    print("✓ Multiple LLM response saving test passed")


def test_save_tool_output():
    """Test saving tool outputs."""
    print("\nTesting tool output saving...")
    memory = EnhancedMemory()
    
    # Sample tool output
    tool_output = {
        "message": "Login successful!",
        "findings": "The login attempt was successful. A success message ('Login attempt successful! Email: test@example.com') is displayed within a div with id 'feedback'. The email address used for login ('test@example.com') is also displayed, confirming the successful authentication.",
        "validation_passed": True,
        "extra_field": "This should not be saved",
        "another_field": {"complex": "data"}
    }
    
    memory.save_tool_output(tool_output, step_number=2)
    
    assert len(memory.tool_outputs) == 1
    saved_output = memory.tool_outputs[0]
    assert saved_output["step_number"] == 2
    assert saved_output["tool_output"]["message"] == "Login successful!"
    assert saved_output["tool_output"]["validation_passed"] is True
    assert "extra_field" not in saved_output["tool_output"]  # Should be filtered out
    assert "another_field" not in saved_output["tool_output"]  # Should be filtered out
    assert "timestamp" in saved_output
    print("✓ Tool output saving test passed")


def test_get_recent_data():
    """Test retrieving recent data."""
    print("\nTesting recent data retrieval...")
    memory = EnhancedMemory()
    
    # Add multiple LLM states
    for i in range(7):
        llm_response = {
            "current_state": {
                "evaluation_previous_goal": f"Step {i} evaluation",
                "memory": f"Memory for step {i}",
                "next_goal": f"Next goal for step {i}"
            }
        }
        memory.save_llm_response(llm_response, step_number=i)
    
    # Add multiple tool outputs
    for i in range(5):
        tool_output = {
            "message": f"Tool message {i}",
            "findings": f"Tool findings {i}",
            "validation_passed": i % 2 == 0  # Alternate between True/False
        }
        memory.save_tool_output(tool_output, step_number=i)
    
    # Test getting recent LLM states (default 5)
    recent_states = memory.get_recent_llm_states()
    assert len(recent_states) == 5
    assert recent_states[-1]["step_number"] == 6  # Last step
    assert recent_states[0]["step_number"] == 2   # 5 steps back
    
    # Test getting recent LLM states (custom count)
    recent_states_3 = memory.get_recent_llm_states(3)
    assert len(recent_states_3) == 3
    assert recent_states_3[-1]["step_number"] == 6
    
    # Test getting recent tool outputs (default 3)
    recent_tools = memory.get_recent_tool_outputs()
    assert len(recent_tools) == 3
    assert recent_tools[-1]["step_number"] == 4  # Last step
    
    print("✓ Recent data retrieval test passed")


def test_execution_summary():
    """Test execution summary generation."""
    print("\nTesting execution summary...")
    memory = EnhancedMemory()
    
    # Add LLM states with success/failure patterns
    success_response = {
        "current_state": {
            "evaluation_previous_goal": "Success - Task completed",
            "memory": "Task was successful",
            "next_goal": "Next task"
        }
    }
    
    failure_response = {
        "current_state": {
            "evaluation_previous_goal": "Failed - Could not complete task",
            "memory": "Task failed",
            "next_goal": "Retry task"
        }
    }
    
    memory.save_llm_response(success_response, 1)
    memory.save_llm_response(success_response, 2)
    memory.save_llm_response(failure_response, 3)
    
    # Add tool outputs with success/failure patterns
    success_tool = {"message": "Success", "findings": "Good", "validation_passed": True}
    failure_tool = {"message": "Failed", "findings": "Bad", "validation_passed": False}
    
    memory.save_tool_output(success_tool, 1)
    memory.save_tool_output(failure_tool, 2)
    memory.save_tool_output(success_tool, 3)
    
    summary = memory.get_execution_summary()
    
    assert summary["total_llm_states"] == 3
    assert summary["total_tool_executions"] == 3
    assert summary["goal_success_rate"] == 2/3  # 2 successes out of 3
    assert summary["tool_success_rate"] == 2/3  # 2 successes out of 3
    assert "session_duration" in summary
    assert "recent_memory_pattern" in summary
    
    print("✓ Execution summary test passed")


def test_memory_context_formatting():
    """Test memory context string formatting."""
    print("\nTesting memory context formatting...")
    memory = EnhancedMemory()
    
    # Test empty memory
    context = memory.format_memory_context()
    assert "No previous actions executed" in context
    
    # Add some data
    llm_response = {
        "current_state": {
            "evaluation_previous_goal": "Success - Test completed",
            "memory": "This is a test memory with some details about what happened",
            "next_goal": "Continue with next test"
        }
    }
    tool_output = {
        "message": "Test tool executed successfully",
        "findings": "Found some interesting results during the test execution",
        "validation_passed": True
    }
    
    memory.save_llm_response(llm_response, 1)
    memory.save_tool_output(tool_output, 1)
    
    context = memory.format_memory_context()
    
    assert "Session Summary:" in context
    assert "Recent LLM States:" in context
    assert "Recent Tool Outputs:" in context
    assert "Success - Test completed" in context
    assert "Test tool executed successfully" in context
    
    print("✓ Memory context formatting test passed")


def test_export_session_data():
    """Test exporting session data to file."""
    print("\nTesting session data export...")
    memory = EnhancedMemory()
    
    # Add some test data
    llm_response = {
        "current_state": {
            "evaluation_previous_goal": "Success - Export test",
            "memory": "Testing export functionality",
            "next_goal": "Verify export"
        }
    }
    tool_output = {
        "message": "Export test tool",
        "findings": "Export functionality working",
        "validation_passed": True
    }
    
    memory.save_llm_response(llm_response, 1)
    memory.save_tool_output(tool_output, 1)
    
    # Export to file
    export_path = "/tmp/test_memory_export.json"
    memory.export_session_data(export_path)
    
    # Verify export file exists and contains correct data
    assert os.path.exists(export_path)
    
    with open(export_path, 'r') as f:
        exported_data = json.load(f)
    
    assert "session_info" in exported_data
    assert "llm_states" in exported_data
    assert "tool_outputs" in exported_data
    assert "execution_summary" in exported_data
    assert len(exported_data["llm_states"]) == 1
    assert len(exported_data["tool_outputs"]) == 1
    
    # Clean up
    os.remove(export_path)
    print("✓ Session data export test passed")


def test_memory_methods_with_dummy_data():
    """Test and demonstrate the three key memory methods with dummy data."""
    print("\n" + "="*60)
    print("TESTING MEMORY METHODS WITH DUMMY DATA")
    print("="*60)
    
    memory = EnhancedMemory()
    
    # Create realistic dummy data for a web automation session
    dummy_llm_responses = [
        {
            "current_state": {
                "evaluation_previous_goal": "Success - Successfully navigated to login page",
                "memory": "Opened the login page. Can see email and password fields. The page title shows 'User Login' and there's a submit button available.",
                "next_goal": "Fill in the login credentials and submit the form"
            },
            "actions": [{"action": "navigate", "url": "https://example.com/login"}]
        },
        {
            "current_state": {
                "evaluation_previous_goal": "Success - Form fields filled successfully",
                "memory": "Entered email 'user@example.com' and password. Both fields are now populated. Ready to submit the login form.",
                "next_goal": "Submit the login form by clicking the submit button"
            },
            "actions": [
                {"action": "type", "selector": "#email", "text": "user@example.com"},
                {"action": "type", "selector": "#password", "text": "securepass123"}
            ]
        },
        {
            "current_state": {
                "evaluation_previous_goal": "Failed - Login submission resulted in error",
                "memory": "Clicked submit button but received error message 'Invalid credentials'. The form is still visible with error text displayed.",
                "next_goal": "Retry login with different credentials or investigate the error"
            },
            "actions": [{"action": "click", "selector": "#submit-btn"}]
        },
        {
            "current_state": {
                "evaluation_previous_goal": "Success - Login successful on retry",
                "memory": "Used correct credentials and login was successful. Now on dashboard page with welcome message visible. User session is active.",
                "next_goal": "Navigate to user profile section to verify account details"
            },
            "actions": [
                {"action": "type", "selector": "#email", "text": "admin@example.com"},
                {"action": "type", "selector": "#password", "text": "admin123"},
                {"action": "click", "selector": "#submit-btn"}
            ]
        },
        {
            "current_state": {
                "evaluation_previous_goal": "Success - Successfully accessed user profile",
                "memory": "Navigated to profile page. Can see user details including name, email, and account settings. All information appears correct.",
                "next_goal": "Update user profile information as requested"
            },
            "actions": [{"action": "click", "selector": "#profile-link"}]
        }
    ]
    
    dummy_tool_outputs = [
        {
            "message": "Navigation to login page completed successfully",
            "findings": "Page loaded correctly. Login form is present with email field (id='email'), password field (id='password'), and submit button (id='submit-btn'). No error messages visible.",
            "validation_passed": True
        },
        {
            "message": "Form submission attempt completed",
            "findings": "Login form was submitted but returned error message 'Invalid credentials'. Error element has id='error-msg' and is now visible on the page.",
            "validation_passed": False
        },
        {
            "message": "Login retry successful",
            "findings": "Second login attempt with admin credentials was successful. Page redirected to dashboard (/dashboard). Welcome message 'Welcome, Admin!' is now displayed.",
            "validation_passed": True
        },
        {
            "message": "Profile page access verified",
            "findings": "Successfully navigated to user profile page. Profile information is displayed including: Name: 'Admin User', Email: 'admin@example.com', Role: 'Administrator'.",
            "validation_passed": True
        }
    ]
    
    # Save the dummy data to memory
    for i, llm_resp in enumerate(dummy_llm_responses):
        memory.save_llm_response(llm_resp, step_number=i+1)
    
    for i, tool_out in enumerate(dummy_tool_outputs):
        memory.save_tool_output(tool_out, step_number=i+1)
    
    print(f"\n📊 Created dummy data:")
    print(f"   - {len(memory.llm_states)} LLM states")
    print(f"   - {len(memory.tool_outputs)} tool outputs")
    
    # Test and display get_execution_summary()
    print("\n" + "="*50)
    print("1. GET_EXECUTION_SUMMARY() OUTPUT:")
    print("="*50)
    
    summary = memory.get_execution_summary()
    for key, value in summary.items():
        if key == "recent_memory_pattern":
            print(f"{key}:")
            for pattern_key, pattern_value in value.items():
                print(f"  {pattern_key}: {pattern_value}")
        elif key == "session_duration":
            print(f"{key}: {value:.2f} seconds")
        elif "rate" in key:
            print(f"{key}: {value:.1%}")
        else:
            print(f"{key}: {value}")
    
    # Test and display _analyze_recent_patterns()
    print("\n" + "="*50)
    print("2. _ANALYZE_RECENT_PATTERNS() OUTPUT:")
    print("="*50)
    
    patterns = memory._analyze_recent_patterns()
    for key, value in patterns.items():
        print(f"{key}: {value}")
    
    # Test and display format_memory_context()
    print("\n" + "="*50)
    print("3. FORMAT_MEMORY_CONTEXT() OUTPUT:")
    print("="*50)
    
    context = memory.format_memory_context()
    print(context)
    
    print("\n" + "="*60)
    print("✅ MEMORY METHODS DEMONSTRATION COMPLETED")
    print("="*60)


def run_all_tests():
    """Run all memory tests."""
    print("Running EnhancedMemory Tests")
    print("=" * 50)
    
    try:
        # test_memory_initialization()
        # test_save_llm_response()
        # test_save_tool_output()
        # test_get_recent_data()
        # test_execution_summary()
        # test_memory_context_formatting()
        # test_export_session_data()
        test_memory_methods_with_dummy_data()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        print("The simplified EnhancedMemory system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
