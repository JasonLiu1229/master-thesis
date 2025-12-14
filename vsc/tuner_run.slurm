#!/bin/bash -l
#SBATCH --job-name=tuner
#SBATCH --partition=arcturus_gpu
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=72:00:00
#SBATCH --output=stdout.%j
#SBATCH --error=stderr.%j

module --force purge
module load calcua/all

export APPTAINER_CACHEDIR="$VSC_SCRATCH/appt_cache"
mkdir -p "$APPTAINER_CACHEDIR"

SIF="$SLURM_SUBMIT_DIR/tuner.sif"

HOST_APP_DIR="$SLURM_SUBMIT_DIR/../code"
HOST_TRAIN_DIR="$SLURM_SUBMIT_DIR/../tools/java-dataset-converter-llm/dataset/train/jsonl"
HOST_VAL_DIR="$SLURM_SUBMIT_DIR/../tools/java-dataset-converter-llm/dataset/val/jsonl"
HOST_TEST_DIR="$SLURM_SUBMIT_DIR/../tools/java-dataset-converter-llm/dataset/test/jsonl"

apptainer run --nv \
  --bind "$HOST_APP_DIR:/app" \
  --bind "$HOST_TRAIN_DIR:/app/in/train" \
  --bind "$HOST_VAL_DIR:/app/in/val" \
  --bind "$HOST_TEST_DIR:/app/in/test" \
  "$SIF"
