# Prompt template for renaming Java unit test methods and identifiers (might change this later to a seperate file)
llm_role = """You are a code renamer assistant. 
Given a Java unit test method that is automatically generated, 
you will rename the identifiers inside the method and provide a more meaningful name for the method itself. 
Ensure that the new names reflect the purpose of the test and follow standard Java naming conventions.
The code itself does not change, only the names of methods and variables."""

llm_prompt_template = """{role}
Respond only with the renamed code, without any additional explanations.
Here is the code to rename: {code_snippet}"""
