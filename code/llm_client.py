import logging
import os
import threading

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


class LLMClient:
    def __init__(
        self, api_key: str, base_url: str = "https://api.openai.com/v1/chat/completions"
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url

    def chat(self, model: str, messages: list[dict]) -> str:
        """
        Thread-safe chat call.
        - No mutation of self.*
        - Uses thread-local requests.Session for connection reuse.
        """
        session = _get_session()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {"model": model, "messages": messages}

        response = session.post(self.base_url, headers=headers, json=data)

        if response.status_code != 200:
            logger.error(f"LLM ERROR status: {response.status_code}")
            try:
                logger.error(f"LLM ERROR body: {response.json()}")
            except Exception:
                logger.error(f"LLM ERROR raw body: {response.text}")

        response.raise_for_status()
        body = response.json()

        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Unexpected response format from LLM: {e}; body={body!r}")
            raise


if __name__ == "__main__":
    load_dotenv()

    API_KEY = os.getenv("API_KEY")
    API_URL = os.getenv("API_URL", "https://api.openai.com/v1/chat/completions")

    client = LLMClient(API_KEY, API_URL)

    reply = client.chat(
        "gpt-5-mini",
        [
            {"role": "user", "content": "Give me the time of today."},
            {"role": "system", "content": "You are a helpful assistant"},
        ],
    )

    print(reply)
