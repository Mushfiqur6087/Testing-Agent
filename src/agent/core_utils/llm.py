"""
Unified LLM client using LiteLLM.

LiteLLM provides a single, unified API for 100+ LLM providers including:
  OpenAI    — openai/gpt-5-mini, openai/gpt-5-mini-mini
  Anthropic — anthropic/claude-sonnet-4-5, anthropic/claude-haiku-3-5
  Google    — gemini/gemini-2.0-flash, gemini/gemini-1.5-pro
  OpenRouter— openrouter/meta-llama/llama-3.1-8b-instruct
  Azure     — azure/<deployment-name>
  ... and many more

Model strings follow the LiteLLM convention: "provider/model-name"
Set the corresponding API key in env/.env:
  OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, etc.
"""

import time
import litellm

litellm.suppress_debug_info = True


class LLMClient:
    def __init__(
        self,
        model: str = "openai/gpt-5-mini",
        provider: str = None,
        system_prompt: str = "You are a helpful assistant.",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        Args:
            model:    Full LiteLLM model string. Can be:
                        - "provider/model-name"  (e.g. "openai/gpt-5-mini")
                        - "model-name" if provider is given separately
            provider: Optional provider prefix. If given, combined as
                      "{provider}/{model}" unless model already contains "/".
            system_prompt: Default system prompt for all calls.
            timeout:  Request timeout in seconds.
            max_retries: Number of retry attempts on failure.
        """
        # Build the full LiteLLM model string
        if provider and "/" not in model:
            self.model = f"{provider}/{model}"
        else:
            self.model = model  # already a full string e.g. "openai/gpt-5-mini"

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
