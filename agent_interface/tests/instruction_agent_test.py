import os
import sys
import json

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.agent.instruction_agent.agent import InstructionAgent


def test_instruction_agent():
    """Test the InstructionAgent functionality."""
    
    # Test case for signup form validation
    TEST_CASE = """
    Go to file:///home/mushfiqur/vscode/Testing-Agent/html/signup.html
    signup with email field, password field, and confirm password field.
    Test whether the account creation field contains password verify input which takes the second password. If it doesn't match the first password, it shows an error message "passwords must match"
    """
    
    # Get API key from environment variable for security
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: Please set the GEMINI_API_KEY environment variable")
        return False
    
    try:
        # Create the agent
        agent = InstructionAgent(api_key=api_key)
        print("✅ InstructionAgent created successfully")
        
        # Process the test case
        print("\n🔄 Processing test case...")
        output = agent.process_test_case(TEST_CASE)
        print("✅ Test case processed successfully")
        
        print("\n📄 Generated Test Cases:")
        print("=" * 60)
        print(output)
        
        # Try to parse as JSON
        parsed_json = agent.parse_output_as_json()
        if parsed_json:
            print("\n" + "=" * 60)
            print("📋 Parsed JSON Test Cases:")
            print(json.dumps(parsed_json, indent=2))
            
            # Get test cases as list for iteration
            test_cases_list = agent.get_test_cases_list()
            print(f"\n📊 Number of test cases: {len(test_cases_list)}")
            
            # Example: Get a single test case by index
            if len(test_cases_list) > 0:
                first_test = agent.get_test_case_by_index(0)
                print(f"\n🥇 First test case:")
                print(f"  Name: {first_test.get('test_name', 'N/A')}")
                print(f"  Steps: {first_test.get('steps_or_input', 'N/A')[:100]}...")
                
                # Example: Get a test case by name
                specific_test = agent.get_test_case_by_name("passwords_do_not_match")
                if specific_test:
                    print(f"\n🎯 Found specific test case:")
                    print(f"  Name: {specific_test.get('test_name', 'N/A')}")
                    print(f"  Expected: {specific_test.get('expected_outcome', 'N/A')}")
                else:
                    print(f"\n⚠️  Could not find test case named 'passwords_do_not_match'")
            
            print(f"\n🔄 Iterating through all test cases:")
            for i, test_case in enumerate(test_cases_list, 1):
                print(f"\nTest Case {i}:")
                print(f"  📝 Name: {test_case.get('test_name', 'N/A')}")
                print(f"  🔧 Steps: {test_case.get('steps_or_input', 'N/A')[:80]}...")
                print(f"  ✅ Expected: {test_case.get('expected_outcome', 'N/A')[:60]}...")
                if test_case.get('reason_for_failure'):
                    print(f"  ❌ Reason for failure: {test_case.get('reason_for_failure')[:60]}...")
            
            print(f"\n✅ All tests completed successfully!")
            return True
            
        else:
            print("\n❌ Note: Could not parse output as JSON")
            return False
            
    except Exception as e:
        print(f"❌ Error processing test case: {e}")
        return False


def test_agent_methods():
    """Test individual agent methods."""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: Please set the GEMINI_API_KEY environment variable")
        return False
    
    try:
        agent = InstructionAgent(api_key=api_key)
        
        # Test empty state
        print("\n🧪 Testing empty state...")
        assert agent.get_output() is None, "Output should be None initially"
        assert agent.get_test_case() is None, "Test case should be None initially"
        assert len(agent.get_test_cases_list()) == 0, "Test cases list should be empty initially"
        print("✅ Empty state tests passed")
        
        # Test invalid input
        print("\n🧪 Testing invalid input...")
        try:
            agent.process_test_case("")
            assert False, "Should raise ValueError for empty test case"
        except ValueError:
            print("✅ Empty test case validation passed")
        
        # Test index out of bounds
        print("\n🧪 Testing index out of bounds...")
        result = agent.get_test_case_by_index(10)
        assert result is None, "Should return None for out of bounds index"
        print("✅ Index bounds test passed")
        
        # Test non-existent test name
        print("\n🧪 Testing non-existent test name...")
        result = agent.get_test_case_by_name("non_existent_test")
        assert result is None, "Should return None for non-existent test name"
        print("✅ Non-existent test name test passed")
        
        print("\n✅ All method tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in method tests: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting InstructionAgent Tests")
    print("=" * 60)
    
    # Run main functionality test
    success1 = test_instruction_agent()
    
    print("\n" + "=" * 60)
    
    # Run method tests
    success2 = test_agent_methods()
    
    print("\n" + "=" * 60)
    
    if success1 and success2:
        print("🎉 All tests completed successfully!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
