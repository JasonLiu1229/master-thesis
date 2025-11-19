# Tuner information

This tuner is made for a Qwen model. Adapt it if you are using a different model and want to make use of this tuner code.

## Requirements

The requirements are noted in the `requirements/requirements_tuner.txt`. This is deveoloped in Python 3.12.4, so note that some things might be different in case you are using a different version of Python.

## Config settings

In the config setting several constants are defined, these are important to change in case file or directory naming is different. Here we also define some parameters that can be changed for training phase.

Important note: because of hardware limitations it is recomended to train on a smaller dataset, you can configure this too in the `.yml` file. Here we can set the fraction of how much we want to use of the original dataset.

## How does it work

So the main code consist of argparse arguments. So check these out to know what options are available. The main thing is preproccing, if the dataset is not available or generated yet. If it is, you can enable the tune command to tune the chosen model. Also be aware that you need to generate the dataset yourself first before running this code and setting the right pathing too.

The second thing is the tuning of the code. After the preprocessing is done, the tuning will start on it's how if you use the docker container provided for this section of code.

## Run

There is a docker file made for this. So make use of the docker file, to make the run work seaminglisly. If you want to run it locally, you can check the requirements file and download it manually.

`docker compose --profile tune up` is the main command to run it all. By default it will generate the dataset and tune it afterwards.
