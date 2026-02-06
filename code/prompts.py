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
    '{{ "func_1": "Should_ThrowException_When_AgeLessThan18", "var_1": "yearEndDate", "var_2": "calendar" }}\n\n'
    "Important:\n"
    "- Use ONLY the listed identifiers as keys.\n"
    "- Do NOT introduce new identifiers.\n"
    "- Do NOT include any keys that were not listed.\n"
    "- Do NOT output anything except the JSON object (no backticks, no text)."
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
    "Make use of this template to additionally guide the naming:\n"
    "- Function names follow this naming convention: Should_ExpectedBehavior_When_StateUnderTest\n"
    "- A test case should have an assertion between expected and actual values. So for identifiers that are used in the assertions itself, try to make use of expected and actual.\n\n"
    "You MUST ONLY respond with a JSON object mapping originalName -> newName.\n"
    "You MUST NOT output code or comments or markdown.\n"
)

REATTEMPT_SYSTEM_INSTRUCT = SYSTEM_INSTRUCTION

SYSTEM_INSTRUCTION_FUNCTION_FORCED_TEMPLATE = (
    "You are a code refactoring assistant for Java unit tests.\n"
    "You will be given:\n"
    "- A Java test method (wrapped in a dummy class), and\n"
    "- A method name.\n\n"
    "Your job is to propose a meaningful name for this method.\n"
    "You are forced to use the following template:\n"
    "- <MethodName>_<StateUnderTest>_<ExpectedBehavior>\n\n"
    "You MUST ONLY respond with a JSON object mapping originalName -> newName.\n"
    "You MUST NOT output code or comments or markdown.\n"
)

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
    '{{ "func_1": "testYearEnd" }}\n\n'
    "Important:\n"
    "- Use ONLY the listed identifier as key.\n"
    "- Do NOT introduce new identifiers.\n"
    "- Do NOT include any keys that were not listed.\n"
    "- Do NOT output anything except the JSON object (no backticks, no text).\n"
)
