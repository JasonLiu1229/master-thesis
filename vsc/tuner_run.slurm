#!/bin/bash -l
#SBATCH --job-name=tuner
#SBATCH --partition=ampere_gpu
#SBATCH --gpus=1
#SBATCH --mem=32G
#SBATCH --time=72:00:00
#SBATCH --account=ap_ansymo_sd_thesis
#SBATCH --output=stdout.%j
#SBATCH --error=stderr.%j

set -euo pipefail

module --force purge
module load calcua/all

export APPTAINER_CACHEDIR="$VSC_SCRATCH/appt_cache"
mkdir -p "$APPTAINER_CACHEDIR"


PROJECT_ROOT="$(cd "$SLURM_SUBMIT_DIR/.." && pwd)"
HOST_CODE_DIR="$PROJECT_ROOT/code"

# === IMPORTANT: set this to where YOU stored Arrow in $VSC_DATA ===
HOST_ARROW_DIR="$VSC_DATA/tuner_dataset/arrow"

RUN_ID="model_v1_141225" # 14-12-2025

RUN_OUT="$VSC_SCRATCH/tuner_runs/${RUN_ID}"
mkdir -p "$RUN_OUT"/{model,adapter,logs}

SIF="$VSC_SCRATCH/containers/tuner.sif"

echo "PROJECT_ROOT   : $PROJECT_ROOT"
echo "HOST_CODE_DIR  : $HOST_CODE_DIR"
echo "HOST_ARROW_DIR : $HOST_ARROW_DIR"
echo "SIF            : $SIF"
echo "RUN_OUT        : $RUN_OUT"

# Run the container
apptainer exec --nv \
  --bind "$HOST_CODE_DIR:/app" \
  --bind "$HOST_ARROW_DIR:/mnt" \
  --bind "$RUN_OUT:/out" \
  --pwd /app \
  "$SIF" \
  bash -lc '
    set -euo pipefail
    export ARROW_DIR=/mnt

    export SAVE_MODEL_PATH=/out/model
    export ADAPTER_SAVE_PATH=/out/adapter
    export LOG_DIR=/out/logs

    python3 main.py --tune
  '

echo "Done. Outputs in: $RUN_OUT"

FINAL_MODEL_DIR="$VSC_DATA/trained_models/tuner_${SLURM_JOB_ID}"
mkdir -p "$FINAL_MODEL_DIR"

cp -r "$RUN_OUT/model" "$FINAL_MODEL_DIR"

echo "Done. Final model also saved in: $FINAL_MODEL_DIR"
