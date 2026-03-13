import json
import logging
import os

import yaml

from dotenv import load_dotenv
from llm_client import LLMClient
from logger import setup_logging

from prompts import (
    REATTEMPT_SYSTEM_INSTRUCT,
    RETRY_USER_PROMPT_TEMPLATE,
    SYSTEM_INSTRUCTION,
    USER_PROMPT_TEMPLATE,
)

from pipeline.helper import (
    apply_rename_mapping,
    extract_identifier_candidates,
    JavaTestCase,
    JavaTestSpan,
    looks_stringified,
    parse_method_name,
    parse_test_case,
    remove_wrap,
    strip_markdown_fences,
    unescape_java_stringified_source,
    wrap_test_case,
)

from pipeline.stats_tracker import log_error
from pipeline.usage_tracker import record_llm_call


config = {}
with open("pipeline/config.yml", "r") as f:
    config = yaml.safe_load(f)

setup_logging("pipeline")
logger = logging.getLogger("pipeline")

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


def _format_identifier_list_for_prompt(identifiers: list[str]) -> str:
    return "\n".join(f"- {name}" for name in identifiers)


def _rename_process(
    wrapped_source_code: str, source_code_clean: str, file_path: str = None
):
    try:
        original_method_name = parse_method_name(source_code_clean)
    except Exception as e:
        logger.error(f"Failed to extract method name: {e}")

        log_error(file_path, 1, "MethodNotFound", f"Failed to extract method name: {e}")

        return JavaTestCase(
            name=None,
            original_code=source_code_clean,
            code="",
            clean=False,
        )

    try:
        identifier_candidates = extract_identifier_candidates(wrapped_source_code)
    except Exception as e:
        logger.error(
            f"Failed to extract identifier candidates for {original_method_name}: {e}"
        )

        log_error(
            file_path,
            1,
            "NoIdentifiers",
            f"Failed to extract identifier candidates for {original_method_name}: {e}",
        )

        return JavaTestCase(
            name=original_method_name,
            original_code=source_code_clean,
            code="",
            clean=False,
        )

    if not identifier_candidates:
        logger.info(
            f"No identifier candidates found for {original_method_name}; keeping original test."
        )
        return JavaTestCase(
            name=original_method_name,
            original_code=source_code_clean,
            code="",
            clean=False,
        )

    identifier_candidates.append(original_method_name)

    identifiers_for_prompt = _format_identifier_list_for_prompt(identifier_candidates)

    user_message = USER_PROMPT_TEMPLATE.format(
        test_case=wrapped_source_code,
        identifiers=identifiers_for_prompt,
    )

    messages = make_messages(user_message, SYSTEM_INSTRUCTION)

    best_mapping = None
    clean = False

    assert config["TRIES"] > 0, "Amount of tries can not be 0 or smaller"

    attempts = 0

    for i in range(config["TRIES"]):
        logger.info(f"\nLLM attempt {i + 1} (mapping) for {original_method_name}")
        raw, usage = client.chat_with_usage(LLM_MODEL, messages)
        raw = strip_markdown_fences(raw).strip()

        try:
            mapping = json.loads(raw)
        except json.JSONDecodeError as e:
            error_reason = f"Response was not valid JSON: {e}"
            logger.error(
                f"{error_reason} for {original_method_name} on attempt {i + 1}: {raw!r}"
            )

            log_error(file_path, i + 1, "UnvalidJson", error_reason, raw)

            user_message = RETRY_USER_PROMPT_TEMPLATE.format(
                test_case=wrapped_source_code,
                identifiers=identifiers_for_prompt,
                error_reason=error_reason,
                failed_response=raw,
            )
            messages = make_messages(user_message, REATTEMPT_SYSTEM_INSTRUCT)
            continue

        if not isinstance(mapping, dict):
            error_reason = "Response JSON is not an object (expected mapping originalName -> newName)."
            logger.error(
                f"{error_reason} for {original_method_name} on attempt {i + 1}: {raw!r}"
            )

            log_error(file_path, i + 1, "JsonObjectError", error_reason, raw)

            user_message = RETRY_USER_PROMPT_TEMPLATE.format(
                test_case=wrapped_source_code,
                identifiers=identifiers_for_prompt,
                error_reason=error_reason,
                failed_response=raw,
            )
            messages = make_messages(user_message, REATTEMPT_SYSTEM_INSTRUCT)
            continue

        candidate_set = set(identifier_candidates)
        mapping_keys = set(mapping.keys())

        extra_keys = mapping_keys - candidate_set
        if extra_keys:
            error_reason = f"Mapping for {original_method_name} contains unexpected keys {extra_keys}; they will be ignored."
            logger.error(error_reason)

            log_error(file_path, i + 1, "ExtraKeyError", error_reason)

            for k in extra_keys:
                mapping.pop(k, None)

        missing = candidate_set - mapping_keys

        if missing:
            error_reason = (
                "The mapping did not contain all required identifiers. "
                f"Missing: {sorted(missing)}"
            )
            logger.error(
                f"{error_reason} for {original_method_name} on attempt {i+1}: {mapping}"
            )

            log_error(file_path, i + 1, "MissingKeysError", error_reason)

            user_message = RETRY_USER_PROMPT_TEMPLATE.format(
                test_case=wrapped_source_code,
                identifiers=identifiers_for_prompt,
                error_reason=error_reason,
                failed_response=json.dumps(mapping),
            )
            messages = make_messages(user_message, REATTEMPT_SYSTEM_INSTRUCT)
            continue

        best_mapping = mapping
        clean = True
        attempts = i
        break

    if not clean or best_mapping is None:
        error_reason = f"All {config['TRIES']} attempts failed to produce a usable mapping for {original_method_name}; keeping original test."

        logger.error(error_reason)

        log_error(file_path, config["TRIES"], "FailedRename", error_reason)

        return JavaTestCase(
            name=original_method_name,
            original_code=source_code_clean,
            code="",
            clean=False,
        )

    candidate_code = apply_rename_mapping(source_code_clean, best_mapping)

    record_llm_call(
        file_path=file_path,
        method_name=original_method_name,
        new_method_name=best_mapping[original_method_name],
        attempt=attempts + 1,
        call_type="rename" if attempts == 0 else "rename_retry",
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        latency_ms=usage.latency_ms,
        success=clean,
    )

    logger.info(
        f"Renamed test method (mapping mode): {original_method_name} -> {best_mapping[original_method_name]} (clean={clean})"
    )

    return JavaTestCase(
        name=best_mapping[original_method_name],
        original_code=source_code_clean,
        code=candidate_code,
        clean=clean,
    )


def _rename_process_local(wrapped_source_code: str, source_code_clean: str): ...


def rename(java_test_span: JavaTestSpan):
    assert os.path.exists(
        java_test_span.file_path
    ), f"Java file path: {java_test_span.file_path} does not exists"

    source_code_lines = parse_test_case(java_test_span)
    source_code_clean = "\n".join(source_code_lines)

    wrapped_source_code = wrap_test_case(source_code_lines)

    if looks_stringified(wrapped_source_code):
        wrapped_source_code = unescape_java_stringified_source(wrapped_source_code)

    return _rename_process(
        wrapped_source_code, source_code_clean, java_test_span.file_path
    )


def rename_eval(src: str, file_path: str = None):
    if looks_stringified(src):
        src = unescape_java_stringified_source(src)

    source_code_clean = remove_wrap(src)

    java_test_case = _rename_process(src, source_code_clean, file_path)

    return wrap_test_case(java_test_case.code), bool(java_test_case.clean)
