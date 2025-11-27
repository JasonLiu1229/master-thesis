import logging
import os

from dotenv import load_dotenv
from llm_client import LLMClient
from logger import setup_logging

from pipeline.helper import (
    JavaTestCase,
    JavaTestSpan,
    parse_method_name,
    parse_test_case,
    remove_wrap,
    wrap_test_case,
    strip_markdown_fences,
    only_identifier_renames
)

import yaml

config = {}
with open("pipeline/config.yml", "r") as f:
    config = yaml.safe_load(f)

setup_logging("pipeline")
logger = logging.getLogger("pipeline")

USER_PROMPT_TEMPLATE = (
    "Here is the obfuscated test:\n\n"
    "```java\n"
    "{test_case}\n"
    "```\n\n"
    "Return ONLY the improved code block, nothing else."
)

SYSTEM_INSTRUCTION = (
    "You are a code refactoring assistant.\n"
    "Rename identifiers in the following Java unit test so that names are meaningful and self-explanatory.\n"
    "Do **NOT** change logic, literals, comments, formatting, assertions, or method call structure.\n"
    "ONLY improve identifier names (methods, variables)."
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
    
    original_method_name = parse_method_name(wrapped_source_code)

    source_code_clean = "\n".join(source_code)

    user_message = USER_PROMPT_TEMPLATE.format(test_case=wrapped_source_code)
    
    messages = [
        {
            "role": "system",
            "content": SYSTEM_INSTRUCTION,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]
    clean = True
    
    for i in range(config["TRIES"]):
        new_test_code = client.chat(LLM_MODEL, messages)
        
        new_test_code = strip_markdown_fences(new_test_code)

        new_test_code_clean = remove_wrap(new_test_code)
        
        if not only_identifier_renames(source_code_clean, new_test_code_clean):
            logger.warning(f"The new test case has logic changes: {original_method_name}")
            logger.warning(f"Attempt {i + 1}")
            clean = False
    
    # logger.info(f"new test codeP: {new_test_code}")
    
    new_method_name = parse_method_name(new_test_code)

    assert new_test_code != "", "New test code is not made, it is still empty"
    assert new_method_name != "", "New method name is not made, it is still empty"
    
    logger.info(f"new test method name: {new_method_name}, original test method name: {original_method_name}")
    return JavaTestCase(
        name=new_method_name, original_code=source_code_clean, code=new_test_code_clean, clean=clean
    )


def rename_eval(src: str):
    pass
