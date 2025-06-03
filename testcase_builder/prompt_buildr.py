import os
import google.generativeai as genai

class GeminiFlashClient:
    def __init__(self, api_key: str, model_name: str = "models/gemini-1.5-flash", system_prompt: str = "You are a helpful assistant."):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.system_prompt = system_prompt

    def ask(self, user_prompt: str) -> str:
        """
        Sends a prompt to the model and returns the response.
        """
        prompt = f"{self.system_prompt}\n\nUser: {user_prompt}"
        response = self.model.generate_content(prompt)
        return response.text


prompt = '''You are an expert software tester and QA automation engineer.

I will provide a set of requirements, behaviors, or user stories for a web form, input field, API, or feature.  
For each described requirement:

1. **Identify all validation rules and intended behaviors.**
2. **Write comprehensive unit test cases** covering both:
   - Valid (should pass) scenarios
   - Invalid (should fail or show an error) scenarios
3. For each test case, include:
   - Test Name / Description
   - Test steps or input data
   - Expected outcome/result (pass/fail, error message, etc.)
   - Reason for failure (for negative tests)

If the requirement involves a user interface, include steps like navigating to a page, interacting with fields, and observing UI messages.  
If the requirement is about an API, specify input and expected response.

**Format each test case clearly for easy implementation.**

---

**Example:**  
Requirement: "The signup form must require the user to enter their email address. The form should reject invalid emails and show the message 'Invalid email address.'"

**Example Test Cases:**

1. **Test Name:** Accepts valid email  
   **Steps/Input:** Enter `user@example.com` in the email field and submit  
   **Expected Outcome:** Form submits successfully

2. **Test Name:** Rejects empty email field  
   **Steps/Input:** Leave email field empty and submit  
   **Expected Outcome:** Form displays 'Invalid email address.'
---

**Now, for the following requirement(s), generate all relevant unit test cases.**
'''

TEST_CASE = """
Go to file:///home/mushfiqur/vscode/Testing-Agent/html/signup.html
signup with email field, password field, and confirm password field.
Test whether the account creation field contains password verify input which takes the second password. If it doesn't match the first password, it shows an error message "passwords must match"
"""

if __name__ == "__main__":
    # Get API key from environment variable for security
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: Please set the GEMINI_API_KEY environment variable")
        exit(1)
    client = GeminiFlashClient(api_key=api_key)

    # Combine the general prompt template with the specific test-case instruction
    full_prompt = f"{prompt}\n{TEST_CASE}"

    # Send the combined prompt to the LLM and get the response
    response_text = client.ask(full_prompt)

    # Print out the generated unit test cases
    print(response_text)
