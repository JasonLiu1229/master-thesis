USER_PROMPT_TEMPLATE = (
    "Here is the obfuscated Java test method wrapped in a dummy class:\n\n"
    "```java\n"
    "{test_case}\n"
    "```\n\n"
    "Here are the identifiers that may be renamed:\n"
    "{identifiers}\n\n"
    "Propose more meaningful names for each of THESE identifiers only.\n"
    "Return a single JSON object mapping originalName -> newName.\n"
    "Example:\n"
    "{{ \"func_1\": \"testYearEnd\", \"var_1\": \"yearEndDate\", \"var_2\": \"calendar\" }}\n\n"
    "Important:\n"
    "- Use ONLY the listed identifiers as keys.\n"
    "- Do NOT introduce new identifiers.\n"
    "- Do NOT include any keys that were not listed.\n"
    "- Do NOT output anything except the JSON object (no backticks, no text).\n"
)

RETRY_USER_PROMPT_TEMPLATE = (
    "Here is the original obfuscated Java test method wrapped in a dummy class:\n\n"
    "```java\n"
    "{test_case}\n"
    "```\n\n"
    "Here are the identifiers that may be renamed:\n"
    "{identifiers}\n\n"
    "Your previous response was rejected for this reason:\n"
    "{error_reason}\n\n"
    "Your previous response was:\n"
    "{failed_response}\n\n"
    "Please try again.\n"
    "Return a single JSON object mapping originalName -> newName.\n"
    "Use ONLY the listed identifiers as keys.\n"
    "Do NOT introduce new identifiers or keys.\n"
    "Do NOT output anything except the JSON object (no backticks, no text).\n"
)

SYSTEM_INSTRUCTION = (
    "You are a code refactoring assistant for Java unit tests.\n"
    "You will be given:\n"
    "- A Java test method (wrapped in a dummy class), and\n"
    "- A list of identifier names (method + local variables + parameters).\n\n"
    "Your job is to propose more meaningful names for these identifiers.\n"
    "You MUST ONLY respond with a JSON object mapping originalName -> newName.\n"
    "You MUST NOT output code or comments or markdown.\n"
)

REATTEMPT_SYSTEM_INSTRUCT = SYSTEM_INSTRUCTION

SINGLE_IDENTIFIER_PROMPT = (
    "Here is single identifier:\n"
    "{identifier}\n\n"
    "Here is the snippets of code it used for:\n"
    "{code_snippets}\n\n"
    "Here is a list of names already taken, so do NOT use these:\n"
    "{teken_identifiers}\n\n"
    "Propose more meaningful names for this identifier.\n"
    "Return a single JSON object mapping originalName -> newName.\n"
    "Example:\n"
    "{{ \"func_1\": \"testYearEnd\" }}\n\n"
    "Important:\n"
    "- Use ONLY the listed identifier as key.\n"
    "- Do NOT introduce new identifiers.\n"
    "- Do NOT include any keys that were not listed.\n"
    "- Do NOT output anything except the JSON object (no backticks, no text).\n"
)
