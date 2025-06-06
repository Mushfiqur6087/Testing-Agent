import google.generativeai as genai
import os
import sys
# Set up project root and add to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)


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




