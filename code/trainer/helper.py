from datasets import DatasetDict

def save_dataset_dict(ds_dict: DatasetDict, out_dir: str):
    """
    Saves arrow shards to out_dir.
    """
    ds_dict.save_to_disk(out_dir)


def load_dataset_dict(in_dir: str) -> DatasetDict:
    """
    Load previously saved dataset dict.
    """
    return DatasetDict.load_from_disk(in_dir)
