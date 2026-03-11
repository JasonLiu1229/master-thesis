import logging
import os
import threading
import time
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

from logger import setup_logging

setup_logging("llm_client")
logger = logging.getLogger("llm_client")


_thread_local = threading.local()


def _get_session() -> requests.Session:
    """
    Get a thread-local requests.Session.
    Each OS thread gets its own Session instance -> no cross-thread sharing.
    """
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
    return _thread_local.session


@dataclass
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


class LLMClient:
    def __init__(
        self, api_key: str, base_url: str = "https://api.openai.com/v1/chat/completions"
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url

    def chat(self, model: str, messages: list[dict]) -> str:
        """
        Thread-safe chat call. Returns only the response text.
        Preserved for backwards compatibility.
        """
        text, _ = self.chat_with_usage(model, messages)
        return text

    def chat_with_usage(self, model: str, messages: list[dict]) -> tuple[str, LLMUsage]:
        """
        Thread-safe chat call.
        Returns (response_text, LLMUsage) so the caller can record token usage.

        The ``usage`` object in every OpenAI-compatible response body looks like:
            { "prompt_tokens": N, "completion_tokens": M, "total_tokens": N+M }
        All major providers (OpenAI, Mistral, Together, Ollama, vLLM, LM Studio)
        include this field.
        """
        session = _get_session()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {"model": model, "messages": messages}

        t0 = time.perf_counter()
        response = session.post(self.base_url, headers=headers, json=data)
        latency_ms = (time.perf_counter() - t0) * 1000

        if response.status_code != 200:
            logger.error(f"LLM ERROR status: {response.status_code}")
            try:
                logger.error(f"LLM ERROR body: {response.json()}")
            except Exception:
                logger.error(f"LLM ERROR raw body: {response.text}")

        response.raise_for_status()
        body = response.json()

        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Unexpected response format from LLM: {e}; body={body!r}")
            raise

        usage_raw = body.get("usage") or {}
        usage = LLMUsage(
            prompt_tokens=usage_raw.get("prompt_tokens", 0),
            completion_tokens=usage_raw.get("completion_tokens", 0),
            latency_ms=round(latency_ms, 1),
        )

        return text, usage


if __name__ == "__main__":
    load_dotenv()

    API_KEY = os.getenv("API_KEY")
    API_URL = os.getenv("API_URL", "https://api.openai.com/v1/chat/completions")

    client = LLMClient(API_KEY, API_URL)

    reply, usage = client.chat_with_usage(
        "gpt-4o-mini",
        [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Give me the time of today."},
        ],
    )

    print(reply)
    print(f"Prompt tokens: {usage.prompt_tokens}")
    print(f"Completion tokens: {usage.completion_tokens}")
    print(f"Latency: {usage.latency_ms} ms")
