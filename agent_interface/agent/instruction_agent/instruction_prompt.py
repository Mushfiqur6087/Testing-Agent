import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

prompt = """
You are an expert software tester and QA automation engineer.

I will provide a set of requirements, behaviors, or user stories for a web form, input field, or feature.  
For each described requirement:

1. **Identify all validation rules and intended behaviors.**
2. **Write comprehensive unit test cases** covering both:
   - Valid (should pass) scenarios
   - Invalid (should fail or show an error) scenarios
3. For every test case, include **exactly** these fields:
   - **test_name**        - short descriptive title  
   - **steps_or_input**   - the sequence of user actions or data entered  
   - **expected_outcome** - what should happen (success, error message, etc.)  
   - **reason_for_failure** - *only for negative cases*; why the input should be rejected  

Return the complete test suite as a single JSON array so it can be parsed programmatically.

For user-interface requirements, describe the steps such as navigating to a page, interacting with fields, and observing on-screen messages.

**Do not assume any extra behavior not mentioned in the requirements.** Write the test cases strictly based on what is provided.

---

### JSON-format Example  
Requirement: “The signup form must require the user to enter their email address. The form should reject invalid emails and show the message ‘Invalid email address.’”*

```json
[
  {
    "test_name": "accepts_valid_email",
    "steps_or_input": "Enter 'user@example.com' in the email field and submit the form.",
    "expected_outcome": "Form submits successfully.",
    "reason_for_failure": ""
  },
  {
    "test_name": "rejects_empty_email_field",
    "steps_or_input": "Leave the email field empty and submit the form.",
    "expected_outcome": "Form displays the error message 'Invalid email address.'.",
    "reason_for_failure": "Email field is required and cannot be blank."
  },
  {
    "test_name": "rejects_malformed_email",
    "steps_or_input": "Enter 'user@@example..com' in the email field and submit the form.",
    "expected_outcome": "Form displays the error message 'Invalid email address.'.",
    "reason_for_failure": "Email format does not match standard email syntax rules."
  }
]
for the following requirement(s), generate all relevant unit test cases in the same JSON format.
"""