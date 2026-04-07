SYSTEM_INSTRUCTION = (
    "You are a Java test code refactoring expert.\n"
    "You will be given:\n"
    "- A Java test method (wrapped in a dummy class), and\n"
    "- A list of identifiers to rename, each tagged with its kind: (method) or (variable).\n\n"
    "Your job is to propose meaningful names for ALL of the listed identifiers.\n\n"
    "Naming conventions to follow:\n"
    "- Methods (func_*): use camelCase starting with 'test', e.g. testShouldReturnNullWhenInputIsEmpty.\n"
    "- Variables used in assertions (var_*): prefer 'expected' / 'actual' where applicable.\n"
    "- Other variables (var_*): use concise camelCase nouns that describe the value, e.g. userCount, resultList.\n\n"
    "Rules:\n"
    "- You MUST include every identifier from the list as a key — no omissions.\n"
    "- Use ONLY the listed identifiers as keys — no extras.\n"
    "- You MUST ONLY respond with a valid JSON object mapping originalName -> newName.\n"
    "- Do NOT output code, comments, markdown, or any text outside the JSON object.\n"
)

REATTEMPT_SYSTEM_INSTRUCT = SYSTEM_INSTRUCTION

SYSTEM_INSTRUCTION_WITH_TEMPL = (
    "You are a Java test code refactoring expert.\n"
    "You will be given:\n"
    "- A Java test method (wrapped in a dummy class), and\n"
    "- A list of identifiers to rename, each tagged with its kind: (method) or (variable).\n\n"
    "Your job is to propose meaningful names for ALL of the listed identifiers.\n\n"
    "Naming conventions to follow:\n"
    "- Methods (func_*): MUST follow this template exactly: testShouldExpectedBehaviorWhenStateUnderTest.\n"
    "- Variables used in assertions (var_*): prefer 'expected' / 'actual' where applicable.\n"
    "- Other variables (var_*): use concise camelCase nouns that describe the value, e.g. userCount, resultList.\n\n"
    "Rules:\n"
    "- You MUST include every identifier from the list as a key — no omissions.\n"
    "- Use ONLY the listed identifiers as keys — no extras.\n"
    "- You MUST ONLY respond with a valid JSON object mapping originalName -> newName.\n"
    "- Do NOT output code, comments, markdown, or any text outside the JSON object.\n"
)


def _format_identifier_list_with_kinds(identifiers: list[str]) -> str:
    """
    Format identifiers with their kind tag so the model knows which naming
    convention to apply to each one.
      func_* -> (method)
      var_*  -> (variable)
    """
    lines = []
    for name in identifiers:
        if name.startswith("func_"):
            lines.append(f"- {name} (method)")
        else:
            lines.append(f"- {name} (variable)")
    return "\n".join(lines)


USER_PROMPT_TEMPLATE = (
    "Here is the obfuscated Java test method wrapped in a dummy class:\n\n"
    "```java\n"
    "{test_case}\n"
    "```\n\n"
    "Here are ALL the identifiers that must be renamed:\n"
    "{identifiers}\n\n"
    "Rename ALL of the identifiers above. You MUST include every one of them as a key.\n"
    "Return a single JSON object mapping originalName -> newName.\n\n"
    "Example (for a method + two variables):\n"
    '{{"func_1": "testShouldReturnEmptyListWhenInputIsNull", "var_1": "actualResult", "var_2": "expectedSize"}}\n\n'
    "Rules:\n"
    "- ALL listed identifiers must appear as keys in your response.\n"
    "- Use ONLY the listed identifiers as keys — do NOT add or remove any.\n"
    "- Do NOT output anything except the JSON object (no backticks, no text)."
)

RETRY_USER_PROMPT_TEMPLATE = (
    "Here is the original obfuscated Java test method wrapped in a dummy class:\n\n"
    "```java\n"
    "{test_case}\n"
    "```\n\n"
    "Here are ALL the identifiers that must be renamed:\n"
    "{identifiers}\n\n"
    "Your previous response was rejected for this reason:\n"
    "{error_reason}\n\n"
    "Your previous (rejected) response was:\n"
    "{failed_response}\n\n"
    "Please try again. Make sure your new response:\n"
    "- Includes EVERY identifier from the list above as a key.\n"
    "- Uses ONLY the listed identifiers as keys.\n"
    "- Is a valid JSON object only — no backticks, no explanation.\n"
)


# ---------------------------------------------------------------------------
# Commented-out experimental prompts kept for reference
# ---------------------------------------------------------------------------

# Single-identifier prompt — alternative approach where each identifier is
# handled in a separate call. Avoids omission entirely at the cost of more
# API calls. Worth benchmarking if omission errors persist after the fix.
#
# SINGLE_IDENTIFIER_PROMPT = (
#     "Here is a single identifier:\n"
#     "{identifier}\n\n"
#     "Here are the code snippets where it is used:\n"
#     "{code_snippets}\n\n"
#     "These names are already taken — do NOT use them:\n"
#     "{taken_identifiers}\n\n"
#     "Propose a more meaningful name for this identifier.\n"
#     "Return a single JSON object mapping originalName -> newName.\n"
#     "Example:\n"
#     '{{ "func_1": "testYearEnd" }}\n\n'
#     "Rules:\n"
#     "- Use ONLY the listed identifier as key.\n"
#     "- Do NOT introduce new identifiers.\n"
#     "- Do NOT output anything except the JSON object (no backticks, no text).\n"
# )
