from model import tokenizer


def format(data: dict) -> str:
    """
    Format the input data into a string for the model.
    Args:
        data (dict): Dictionary containing 'prompt' and 'response' keys.
    Returns:
        str: Formatted string for the model.
    """
    assert (
        "prompt" in data and "response" in data
    ), "Data must contain prompt and response keys."

    return f"You are a java identifier renamer. \n \
        ### Obfuscated Java code: {data['prompt']} \n \
        ### Output Java code: {data['response']}"


def tokenize(data: dict):
    """
    Tokenize the input data for the model.
    Args:
        data (dict): Dictionary containing 'prompt' and 'response' keys.
    Returns:
        dict: Tokenized input and labels for the model.
    """

    assert (
        "prompt" in data and "response" in data
    ), "Data must contain 'prompt' and 'response' keys."

    text = format(data)
    tokens = tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=1024,
        return_tensors="pt",
    )
    tokens["labels"] = tokens["input_ids"].copy()
    return tokens


def preprocess(data: list):
    """
    Preprocess the data for training.

    Args:
        data (list): List of dictionaries containing the data to preprocess. So each dictionary should have 'prompt' and 'response' keys.
    """
    return [tokenize(item) for item in data]
