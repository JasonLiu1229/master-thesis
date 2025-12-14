# VSC

This directory consists of files needed to run on the VSC infrastruture for cloud computing

## Folder layout on CalcUA

```txt
$VSC_HOME/project/
├── code/
│   ├── main.py
│   ├── tuner.py
│   ├── data_preprocess.py
│   ├── config.yml
│   └── ... (any other .py modules)
├── requirements_tuner.txt
└── containers/
    ├── tuner.def
    ├── requirements_tuner.txt   # copy of requirements used for image build
    ├── build_tuner_sif.slurm
    ├── tuner_run.slurm
    └── tuner.sif                # produced by the build job


$VSC_DATA/tuner_dataset/arrow/
├── train/
├── val/
└── test/    # optional (not really needed)

$VSC_SCRATCH/
├── appt_cache/                   # apptainer cache
└── tuner_runs/
    └── <jobid>/
        ├── model/
        ├── adapter/
        └── logs/

```

## Needed files

Files you need to create/add manually

Put these files in $VSC_HOME/project/containers/:

1. tuner.def
2. build_tuner_sif.slurm
3. tuner_run.slurm
4. requirements_tuner.txt (copy of your project requirements used for the image build)

Your existing code stays in:

- $VSC_HOME/project/code/…
- $VSC_HOME/project/requirements_tuner.txt (optional to keep both; the one in containers is what build uses)

Your dataset must exist in:

- $VSC_DATA/tuner_dataset/arrow/{train,val,test}

## Commands

1. Build the Apptainer sif image

```bash
sbatch build_tuner_sif.slurm
```

2. Submit the run jon

```bash
sbatch tuner_run.slurm
```
