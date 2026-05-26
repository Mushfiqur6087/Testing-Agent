"""
Unified LLM client using LiteLLM.
Supports any provider (openai, anthropic, gemini, openrouter, etc.)
via a single interface.
"""

import os
import sys
import litellm

# Set up project root and add to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

# Suppress litellm's verbose logging by default
litellm.suppress_debug_info = True


class LLMClient:
    """
    Unified LLM client powered by LiteLLM.

    Usage:
        client = LLMClient(model="gpt-5-mini", provider="openai")
        response = client.ask("Hello, world!")

    LiteLLM reads API keys from environment variables automatically:
        - openai    → OPENAI_API_KEY
        - anthropic → ANTHROPIC_API_KEY
        - gemini    → GEMINI_API_KEY
        - openrouter → OPENROUTER_API_KEY
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        provider: str = "gemini",
        system_prompt: str = "You are a helpful assistant.",
    ):
        # LiteLLM model format: "provider/model" (e.g. "openai/gpt-5-mini")
        self.model = f"{provider}/{model}"
        self.system_prompt = system_prompt

    def ask(self, user_prompt: str) -> str:
        """
        Sends a prompt to the model via LiteLLM and returns the response text.
        """
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
