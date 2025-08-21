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

    return f"You are a java identifier renamer for auto generated java unit test code. \n \
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


def preprocess(dataset):
    """
    Preprocess the data for training.

    Args:
        dataset (Dataset): Hugging Face Dataset object.
    Returns:
        Dataset: Preprocessed dataset with tokenized inputs.
    """
    from datasets import Dataset

    if not isinstance(dataset, Dataset):
        raise ValueError("Input must be a Hugging Face Dataset object.")

    tokenized_data = dataset.map(
        tokenize,
        batched=False,
    )

    return tokenized_data
