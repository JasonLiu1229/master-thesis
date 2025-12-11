# VSC

This directory consists of files needed to run on the VSC infrastruture for cloud computing

## Folder layout on CalcUA

```txt
$VSC_DATA/
  thesis_llm/
    code/        # git repository with this project
    venv/        # Python virtual environment
    data/
      raw/       # original/raw data
      arrow/     # Arrow / preprocessed datasets
    models/      # final/best models per job

$VSC_SCRATCH/
  thesis_llm/
    run_<JOBID>/
      output/        # logs, metrics, etc.
      checkpoints/   # training checkpoints
      adapters/      # LoRA / PEFT adapters if applicable
    hf_cache/        # HuggingFace transformers cache
    hf_datasets/     # HuggingFace datasets cache
```

## Initial one-time setup

### Log in 

```bash
    ssh vscXXXXX@login1.calcua.uantwerpen.be
```

### Create base dir

```bash
    mkdir -p "$VSC_DATA/thesis_llm"
    mkdir -p "$VSC_DATA/thesis_llm/code"
    mkdir -p "$VSC_DATA/thesis_llm/data/raw"
    mkdir -p "$VSC_DATA/thesis_llm/data/arrow"
    mkdir -p "$VSC_DATA/thesis_llm/models"
    mkdir -p "$VSC_SCRATCH/thesis_llm"
```

### Copy your project into `code/`

```bash
    scp -r code/tuner/ vscXXXXX@login1.calcua.uantwerpen.be:$VSC_DATA/thesis_llm/code
    scp -r code/model.py vscXXXXX@login1.calcua.uantwerpen.be:$VSC_DATA/thesis_llm/code
    scp -r code/prompts.py vscXXXXX@login1.calcua.uantwerpen.be:$VSC_DATA/thesis_llm/code
    scp -r code/logger.py vscXXXXX@login1.calcua.uantwerpen.be:$VSC_DATA/thesis_llm/code
```

### Requirements file

```bash
    scp -r requirements/requirements_tuner.txt vscXXXXX@login1.calcua.uantwerpen.be:$VSC_DATA/thesis_llm/code/requirements.txt
```

## Copy data / Arrow files to the cluster

### Raw data

If you still have to process the data, and you want to do this in the vsc space. We will not cover this and this will also not be included in the `.slum` file.

### Arrow data

```bash
    scp -r out/data_preprocessed/ vscXXXXX@login1.calcua.uantwerpen.be:$VSC_DATA/thesis_llm/data/arrow
```
