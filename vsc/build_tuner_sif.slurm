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

OUT="$VSC_SCRATCH/containers"
mkdir -p "$OUT"

export APPTAINER_CACHEDIR="$VSC_SCRATCH/appt_cache"
export APPTAINER_TMPDIR="$VSC_SCRATCH/appt_tmp"
mkdir -p "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"

touch "$APPTAINER_TMPDIR/.write_test" && rm -f "$APPTAINER_TMPDIR/.write_test"
touch "$APPTAINER_CACHEDIR/.write_test" && rm -f "$APPTAINER_CACHEDIR/.write_test"

apptainer build "$OUT/tuner.sif" tuner.def

echo "Built: $OUT/tuner.sif"
