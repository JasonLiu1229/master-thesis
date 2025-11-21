import os

from dotenv import load_dotenv

from llm_client import LLMClient

USER_PROMPT_TEMPLATE = (
    "Here is the obfuscated test:\n\n"
    "```java\n"
    "{obf}\n"
    "```\n\n"
    "Return ONLY the improved code block, nothing else."
)

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")

client = LLMClient(API_KEY, API_URL)
