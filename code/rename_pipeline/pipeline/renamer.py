import os

from dotenv import load_dotenv

from llm_client import LLMClient

from helper import JavaTestCase, JavaTestSpan

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


def rename(java_test_span: JavaTestSpan):
    assert os.path.exists(java_test_span.file_path), f"Java file path: {java_test_span.file_path} does not exists"
    
    
    new_method_name: str = ""
    new_test_code: str = ""
    
    # renaming
    
    assert new_test_code != "", "New test code is not made, it is still empty"
    assert new_method_name != "", "New method name is not made, it is still empty"
    return JavaTestCase(new_method_name, java_test_span, new_test_code)
