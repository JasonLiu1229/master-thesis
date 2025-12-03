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
    "Do NOT qualify or de-qualify identifiers. For example, do NOT change DAY_OF_YEAR to Calendar.DAY_OF_YEAR or vice versa.\n"
    "ONLY change identifier names (methods, variables)."
)

REATTEMPT_SYSTEM_INSTRUCT = (
    "You are a code refactoring assistant.\n"
    "Rename identifiers in the following Java unit test so that names are meaningful and self-explanatory.\n"
    "Do NOT change logic, literals, comments, formatting, assertions, or method call structure.\n"
    "Do NOT add, remove, or modify any try, catch, or finally blocks.\n"
    "Do NOT change which exception types are caught.\n"
    "Do NOT remove empty catch blocks, even if they only contain a comment.\n"
    "Assume every import is already done, so do NOT worry about if something is imported already and keep it as is.\n"
    "Do NOT qualify or de-qualify identifiers. For example, do NOT change DAY_OF_YEAR to Calendar.DAY_OF_YEAR or vice versa.\n"
    "Only change identifier names (methods, variables).\n"
    "If you are unsure whether a change would modify control flow or exception handling, do not make that change."
)
