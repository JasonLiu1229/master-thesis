# Utility folder

This is a set of external tools (not really for the thesis) for analysis and optimization.

## Utils

In the utils we have a sorting function, that sorts the dataset based on file size. Makes it easier to understand what files are big and small.

I also included a sorting function based on if there is any identifiers to rename in the test. Technically you can still include these files because renaming method names is also important (up to you). We also filter out test that simply can not be parsed, meaning that our renamer can not even find the identifiers so these will be excluded.

Next, we have some other optimization code that simplifies the bigger java files. Only for the things that do not impact the renaming context will be simplified.
Note that this feature will use OpenAI gpt, so in case you want to use this, make sure the right API key are set for you.

## Note

Because this is a set of functions and not really have any like specific use case, there will also be no docker file created for this. There is a requirements file in [requirements](../../requirements/) folder. It is developed for **Python 3.12.4**, so keep that in mind when trying to run this code.
