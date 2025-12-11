#!/bin/bash
#SBATCH --job-name=thesis-llm
#SBATCH -A ap_vsc21168
#SBATCH --partition=ampere_gpu         # Tier-2 Vaughan GPU partition
#SBATCH --gres=gpu:1                   # number of GPUs
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-task=4G
#SBATCH --time=36:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# -----------------------------
# 1. Modules & basic setup
# -----------------------------
module --force purge
module load calcua/2024a
# Check with "module avail Python" on the cluster if this exact version exists:
module load Python/3.12.3-GCCcore-13.3.0

# -----------------------------
# 2. Project paths
# -----------------------------
PROJECT_ROOT="$VSC_DATA/thesis_llm"
CODE_DIR="$PROJECT_ROOT/code"
VENV_DIR="$PROJECT_ROOT/venv"
DATA_DIR="$PROJECT_ROOT/data"
RAW_DATA_DIR="$DATA_DIR/raw"
ARROW_DIR="$DATA_DIR/arrow"
FINAL_MODELS_DIR="$PROJECT_ROOT/models"

# Scratch paths for this job
RUN_ROOT="$VSC_SCRATCH/thesis_llm/run_${SLURM_JOB_ID}"
OUTPUT_DIR="$RUN_ROOT/out"
CHECKPOINT_DIR="$RUN_ROOT/checkpoints"
ADAPTER_DIR="$RUN_ROOT/adapters"
HF_CACHE_DIR="$VSC_SCRATCH/thesis_llm/hf_cache"
HF_DATASETS_DIR="$VSC_SCRATCH/thesis_llm/hf_datasets"

mkdir -p "$CODE_DIR" "$DATA_DIR" "$RAW_DATA_DIR" "$ARROW_DIR" \
         "$FINAL_MODELS_DIR" "$RUN_ROOT" "$OUTPUT_DIR" \
         "$CHECKPOINT_DIR" "$ADAPTER_DIR" "$HF_CACHE_DIR" \
         "$HF_DATASETS_DIR" logs

cd "$CODE_DIR"

# -----------------------------
# 3. Python virtual environment
# -----------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo ">>> Creating virtual environment in $VENV_DIR"
    python -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo ">>> Using existing virtual environment in $VENV_DIR"
    source "$VENV_DIR/bin/activate"
fi

# -----------------------------
# 4. Environment variables for your code
# -----------------------------
# These MUST match the keys you use in config.yml
export INPUT_DIR="$ARROW_DIR"
export OUTPUT_DIR="$OUTPUT_DIR"
export SAVE_MODEL_PATH="$CHECKPOINT_DIR"
export ADAPTER_SAVE_PATH="$ADAPTER_DIR"
export LOG_DIR="$OUTPUT_DIR"    
export ARROW_DIR="$ARROW_DIR"

export TRANSFORMERS_CACHE="$HF_CACHE_DIR"
export HF_DATASETS_CACHE="$HF_DATASETS_DIR"

echo ">>> ENVIRONMENT"
echo "PROJECT_ROOT      = $PROJECT_ROOT"
echo "CODE_DIR          = $CODE_DIR"
echo "INPUT_DIR         = $INPUT_DIR"
echo "OUTPUT_DIR        = $OUTPUT_DIR"
echo "SAVE_MODEL_PATH   = $SAVE_MODEL_PATH"
echo "ADAPTER_SAVE_PATH = $ADAPTER_SAVE_PATH"
echo "LOG_DIR           = $LOG_DIR"
echo "ARROW_DIR         = $ARROW_DIR"

# -----------------------------
# 5. Run your pipeline
# -----------------------------

# Optional: if you have a preprocessing step
# echo '>>> Running preprocessing'
# python main.py --preprocess

echo '>>> Starting training'
# If you actually start from tuner.py directly, change this:
python main.py --tune

TRAIN_EXIT_CODE=$?

# -----------------------------
# 6. Copy final model to persistent storage
# -----------------------------
if [ $TRAIN_EXIT_CODE -eq 0 ]; then
    echo ">>> Training finished successfully, copying final model to \$VSC_DATA"

    JOB_MODEL_DIR="$FINAL_MODELS_DIR/run_${SLURM_JOB_ID}"
    mkdir -p "$JOB_MODEL_DIR"

    # Adjust this if your script saves with different names/structure
    cp -r "$CHECKPOINT_DIR" "$JOB_MODEL_DIR/"

    echo ">>> Final model stored in: $JOB_MODEL_DIR"
else
    echo ">>> Training failed with exit code $TRAIN_EXIT_CODE, not copying model."
fi

exit $TRAIN_EXIT_CODE
