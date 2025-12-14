#!/bin/bash -l
#SBATCH --job-name=build_tuner_sif
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=build_stdout.%j
#SBATCH --error=build_stderr.%j

set -euo pipefail

module --force purge
module load calcua/all

export APPTAINER_TMPDIR="$VSC_SCRATCH_NODE/$USER/appt_tmp"
export APPTAINER_CACHEDIR="$VSC_SCRATCH/appt_cache"
mkdir -p "$APPTAINER_TMPDIR" "$APPTAINER_CACHEDIR"

cd "$SLURM_SUBMIT_DIR"

apptainer build --fakeroot tuner.sif tuner.def

echo "Built: $SLURM_SUBMIT_DIR/tuner.sif"
