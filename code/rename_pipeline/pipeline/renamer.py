import logging
import os

from dotenv import load_dotenv

from helper import (
    JavaTestCase,
    JavaTestSpan,
    parse_method_name,
    parse_test_case,
    wrap_test_case,
    remove_wrap,
)
from llm_client import LLMClient
from logger import setup_logging

setup_logging("pipeline")
logger = logging.getLogger("pipeline")

USER_PROMPT_TEMPLATE = (
    "Here is the obfuscated test:\n\n"
    "```java\n"
    "{test_case}\n"
    "```\n\n"
    "Return ONLY the improved code block, nothing else."
)

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
LLM_MODEL = os.getenv(key="LLM_MODEL")

client = LLMClient(API_KEY, API_URL)


def rename(java_test_span: JavaTestSpan):
    assert os.path.exists(
        java_test_span.file_path
    ), f"Java file path: {java_test_span.file_path} does not exists"

    new_method_name: str = ""
    new_test_code: str = ""

    # ==== Renaming ====
    source_code = parse_test_case(java_test_span)

    wrapped_source_code = wrap_test_case(source_code)
    
    source_code_clean = '\n'.join(source_code)

    user_message = USER_PROMPT_TEMPLATE.format(test_case=wrapped_source_code)

    new_test_code = client.chat(LLM_MODEL, [user_message])
    
    new_test_code_clean = remove_wrap(new_test_code)

    new_method_name = parse_method_name(new_test_code)

    assert new_test_code != "", "New test code is not made, it is still empty"
    assert new_method_name != "", "New method name is not made, it is still empty"
    return JavaTestCase(name=new_method_name, original_code=source_code_clean, code=new_test_code_clean)

def rename_eval(src: str):
    pass
