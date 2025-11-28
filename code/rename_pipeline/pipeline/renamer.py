import logging
import os

import yaml

from dotenv import load_dotenv
from llm_client import LLMClient
from logger import setup_logging

from pipeline.helper import (
    JavaTestCase,
    JavaTestSpan,
    only_identifier_renames,
    parse_method_name,
    parse_test_case,
    remove_wrap,
    strip_markdown_fences,
    wrap_test_case,
)

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

RETRY_USER_PROMPT_TEMPLATE = (
    "Here is the original obfuscated test:\n\n"
    "```java\n"
    "{test_case}\n"
    "```\n\n"
    "Error reason: {error_reason}\n\n"
    "Here is your previous refactored version, which was rejected because it changed logic/exception handling:\n\n"
    "```java\n"
    "{failed_test_case}\n"
    "```\n\n"
    "Produce a new version that ONLY renames identifiers and keeps the logic, assertions, and try/catch structure "
    "identical to the original test.\n"
    "Return ONLY the improved code block, nothing else."
)

SYSTEM_INSTRUCTION = (
    "You are a code refactoring assistant.\n"
    "Rename identifiers in the following Java unit test so that names are meaningful and self-explanatory.\n"
    "Do **NOT** change logic, literals, comments, formatting, assertions, try and catch methodology, or method call structure.\n"
    "ONLY improve identifier names (methods, variables)."
)

REATTEMPT_SYSTEM_INSTRUCT = (
    "You are a code refactoring assistant.\n"
    "Rename identifiers in the following Java unit test so that names are meaningful and self-explanatory.\n"
    "Do NOT change logic, literals, comments, formatting, assertions, or method call structure.\n"
    "Do NOT add, remove, or modify any try, catch, or finally blocks.\n"
    "Do NOT change which exception types are caught.\n"
    "Do NOT remove empty catch blocks, even if they only contain a comment.\n"
    "Only improve identifier names (methods, variables).\n"
    "If you are unsure whether a change would modify control flow or exception handling, do not make that change."
)


load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
LLM_MODEL = os.getenv(key="LLM_MODEL")

client = LLMClient(API_KEY, API_URL)


def make_messages(user_message: str, sys_instruction: str = SYSTEM_INSTRUCTION):
    return [
        {
            "role": "system",
            "content": sys_instruction,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]


def _rename_process(wrapped_source_code: str, source_code_clean):
    original_method_name = parse_method_name(wrapped_source_code)

    user_message = USER_PROMPT_TEMPLATE.format(test_case=wrapped_source_code)

    messages = make_messages(user_message)

    best_code = None
    best_name = original_method_name
    clean = False

    for i in range(config["TRIES"]):
        logger.info(f"LLM attempt {i + 1} for {original_method_name}")
        raw = client.chat(LLM_MODEL, messages)

        raw = strip_markdown_fences(raw)

        candidate_code = remove_wrap(raw)

        if not candidate_code:
            logger.warning(
                f"Empty candidate after remove_wrap for {original_method_name} on attempt {i + 1}"
            )

            user_message = RETRY_USER_PROMPT_TEMPLATE.format(
                test_case=wrapped_source_code,
                failed_test_case=wrap_test_case(candidate_code),
                error_reason=f"Empty candidate after remove_wrap for {original_method_name}",
            )
            messages = make_messages(user_message, REATTEMPT_SYSTEM_INSTRUCT)
            continue

        if not only_identifier_renames(source_code_clean, candidate_code):
            logger.warning(
                f"The new test case has logic changes: {original_method_name} (attempt {i + 1})"
            )
            logger.warning(f"New candidate code:\n{candidate_code}")

            user_message = RETRY_USER_PROMPT_TEMPLATE.format(
                test_case=wrapped_source_code,
                failed_test_case=wrap_test_case(candidate_code),
                error_reason="The new test case has logic changes",
            )
            messages = make_messages(user_message, REATTEMPT_SYSTEM_INSTRUCT)
            continue

        try:
            wrapped_candidate = wrap_test_case(candidate_code.splitlines())
            candidate_name = parse_method_name(wrapped_candidate)
        except Exception as e:
            logger.warning(
                f"Failed to parse method name for {original_method_name} on attempt "
                f"{i + 1}: {e}"
            )

            user_message = RETRY_USER_PROMPT_TEMPLATE.format(
                test_case=wrapped_source_code,
                failed_test_case=wrap_test_case(candidate_code),
                error_reason=f"Failed to parse method name for {original_method_name}",
            )
            
            messages = make_messages(user_message, REATTEMPT_SYSTEM_INSTRUCT)
            continue

        best_code = candidate_code
        best_name = candidate_name
        clean = True
        break

    if not clean or best_code is None:
        logger.warning(
            f"All {config['TRIES']} attempts changed logic or failed for {original_method_name}; "
            "keeping original test."
        )
        return JavaTestCase(
            name=original_method_name,
            original_code=source_code_clean,
            code="",
            clean=False,
        )

    logger.info(
        f"Renamed test method: {original_method_name} -> {best_name} (clean={clean})"
    )
    return JavaTestCase(
        name=best_name,
        original_code=source_code_clean,
        code=best_code,
        clean=clean,
    )


def rename(java_test_span: JavaTestSpan):
    assert os.path.exists(
        java_test_span.file_path
    ), f"Java file path: {java_test_span.file_path} does not exists"

    source_code_lines = parse_test_case(java_test_span)
    source_code_clean = "\n".join(source_code_lines)

    wrapped_source_code = wrap_test_case(source_code_lines)
    return _rename_process(wrapped_source_code, source_code_clean)


def rename_eval(src: str):
    source_code_clean = remove_wrap(src)
    java_test_case = _rename_process(src, source_code_clean)

    return wrap_test_case(java_test_case.code), int(java_test_case.clean)
