"""
Unified LLM client using LiteLLM.
Supports any provider (openai, anthropic, gemini, openrouter, etc.)
"""

import time
import litellm

litellm.suppress_debug_info = True


class LLMClient:
    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        provider: str = "gemini",
        system_prompt: str = "You are a helpful assistant.",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        self.model = f"{provider}/{model}"
        self.system_prompt = system_prompt
        self.timeout = timeout
        self.max_retries = max_retries

    def ask(self, user_prompt: str) -> str:
        """Send a prompt via LiteLLM with retry + exponential backoff."""
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=self.timeout,
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = 2 ** attempt  # 2s, 4s, 8s
                    print(f"  [LLM] Attempt {attempt} failed ({e}). Retrying in {wait}s…")
                    time.sleep(wait)
        raise RuntimeError(f"LLM call failed after {self.max_retries} attempts: {last_error}")
