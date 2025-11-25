# Code

This folder consist of all the different code parts of the project. While some were made seperatly in a different repository, so do visit the [tools](../tools/) folder. ALso check out [Arno's](https://www.dropbox.com/scl/fo/fd9hhq7ejo743297hgv26/AA82GK-zdu4689E0ZeZwGHo?rlkey=vreei6ybneqkfqjpsywli0dt0&e=1&st=ol319nja&dl=0) work, this is the essentially the continuation of his work.

## Tuner

This consists of the code for LLM tuning. You can find a seperate [README](tuner/README.md) for more information.

## App

This consists of the code for the api. I chose an api pipeline for this project, because this would make it easy to replace the LLM with any LLM without changing much of the code. As long as the api works based on the OpenAI specifications of 25/11/2025.

This api is developed using [fastapi](https://fastapi.tiangolo.com/), please checkout this api package, because this will help you understand the code, if interested.

## Benchmarking

This folder consists of simple parsing and formatting code of the different methods I will evaluate in this project. Why a seperate code? This is because everything is containerized in a docker container, so we need to somehow extract the output of these and save it somewhere. The methods also have different outputting schemes, so it is good to make seperate code for it.

At the end we combine it in a nice `.csv` format.

Note: Code is rather rough because it was just for simple parsing and formatting.

## Pipeline (rename_pipeline folder)

TODO
