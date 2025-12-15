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
    "{{ \"func_1\": \"testYearEnd\" }}\n\n"
    "Important:\n"
    "- Use ONLY the listed identifier as key.\n"
    "- Do NOT introduce new identifiers.\n"
    "- Do NOT include any keys that were not listed.\n"
    "- Do NOT output anything except the JSON object (no backticks, no text).\n"
)

REASON_PROMPT = (
    "Here is the Java code that we want to analyse.\n"
    "\n"
    "CODE:\n"
    "{code}\n"
)


REASON_SYSTEM = (
    "You are an expert in Java static analysis.\n"
    "\n"
    "You will receive a Java code snippet.\n"
    "\n"
    "Your tasks:\n"
    "1. Analyze why this snippet is large or verbose.\n"
    "2. Decide whether simplification is needed WITHOUT changing:\n"
    "   - its behavior,\n"
    "   - its logical structure,\n"
    "   - the contextual information needed to understand identifiers and their roles.\n"
    "\n"
    "3. Output a STRICT JSON object with these fields:\n"
    "   - \"approx_line_count\": integer\n"
    "   - \"size_reasons\": array of strings explaining why the code is large\n"
    "   - \"should_simplify\": boolean\n"
    "   - \"simplification_goals\": array describing WHAT to shorten/remove (not how)\n"
    "   - \"notes\": short guidance needed when performing simplification\n"
    "\n"
    "Rules:\n"
    "- 'should_simplify' must be true only when the code contains size bloat that does NOT contribute to logic or identifier meaning.\n"
    "- Examples of safe-to-remove bloat include: very long string literals, long generic type declarations, huge initializers, repetitive boilerplate, long headers.\n"
    "- If unsure whether simplification is safe, set 'should_simplify' to false.\n"
)

SIMPLIFY_PROMPT = (
    "Here is the original Java code and the analysis from the previous step.\n"
    "\n"
    "SIMPLIFICATION_GOALS:\n"
    "{simplification_goals}\n"
    "\n"
    "NOTES:\n"
    "{notes}\n"
    "\n"
    "CODE:\n"
    "{code}\n"
)


SIMPLIFY_SYSTEM = (
    "You are a Java developer performing safe, context-preserving code simplification.\n"
    "\n"
    "Simplify ONLY when it does not change:\n"
    "- Behavior\n"
    "- Control-flow structure\n"
    "- Class, method, or field names\n"
    "- Parameter names, order, or types\n"
    "- Identifier context used by a renaming model\n"
    "\n"
    "Allowed simplifications:\n"
    "1. Shorten long generic type declarations (e.g., List<Map<String, Foo.Bar>> → List<?>).\n"
    "2. Shorten very long literals by keeping a meaningful prefix and replacing the rest with \"...\".\n"
    "3. Reduce large array or collection initializers (keep a few elements + comment).\n"
    "4. Collapse repeated boilerplate blocks into one or a few examples with a comment.\n"
    "5. Remove or shrink irrelevant long comments or headers.\n"
    "\n"
    "Forbidden changes:\n"
    "- Do NOT rename identifiers.\n"
    "- Do NOT remove meaningful method calls, field uses, or logic.\n"
    "- Do NOT change return types or parameter types in any way that alters semantics.\n"
    "- Do NOT break syntax.\n"
    "\n"
    "Output ONLY the simplified Java code.\n"
)
