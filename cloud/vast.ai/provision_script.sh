#!/usr/bin/env bash
set -euo pipefail

log() { echo -e "\n[provision] $*\n"; }

# ===== CONFIG =====
REPO_URL="https://github.com/JasonLiu1229/master-thesis.git"
REPO_DIR="${REPO_DIR:-$HOME/master-thesis}"
BRANCH="${BRANCH:-main}"

# Choose what to run:
#   tune          -> runs "tuner"
#   tune_process  -> runs "tuner_preprocess"
PROFILE="${PROFILE:-tune}"

# Sparse-checkout paths (space-separated).
#   SPARSE_PATHS="docker code requirements compose.yaml" ./provision_script.sh
SPARSE_PATHS="${SPARSE_PATHS:-docker/tuner.Dockerfile code/tuner code/logger.py code/model.py code/prompts.py requirements/requirements_tuner.txt compose.yaml out/data_preprocessed}"

# If you want compose to keep running after provisioning returns,
USE_TMUX="${USE_TMUX:-1}"
TMUX_SESSION="${TMUX_SESSION:-tuning}"

# ===== 0) Base deps =====
if ! command -v git >/dev/null 2>&1; then
  log "Installing git..."
  sudo apt-get update
  sudo apt-get install -y git
fi

# ===== 1) Docker + compose plugin =====
if ! command -v docker >/dev/null 2>&1; then
  log "Installing Docker + compose plugin..."
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg lsb-release

  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
else
  log "Docker already installed."
fi

# ===== 2) NVIDIA container toolkit (for GPU in docker) =====
if ! docker info 2>/dev/null | grep -qi nvidia; then
  log "Installing NVIDIA container toolkit (best-effort)..."
  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit || true
  sudo nvidia-ctk runtime configure --runtime=docker || true
  sudo systemctl restart docker || true
else
  log "Docker already reports NVIDIA runtime."
fi

# ===== 3) Sparse clone/pull repo =====
log "Ensuring repo exists with sparse checkout..."
if [ ! -d "$REPO_DIR/.git" ]; then
  log "Cloning repo (filtered, no checkout)..."
  git clone --filter=blob:none --no-checkout --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"


  git sparse-checkout init --no-cone
  # shellcheck disable=SC2086
  git sparse-checkout set $SPARSE_PATHS

  log "Checking out branch '$BRANCH'..."
  git checkout "$BRANCH"
else
  cd "$REPO_DIR"

  # If the repo existed from a previous run, enforce sparse paths again
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log "Updating repo..."
    git fetch --all --prune
    git sparse-checkout init --no-cone || true
    # shellcheck disable=SC2086
    git sparse-checkout set $SPARSE_PATHS
    git checkout "$BRANCH"
    git pull --ff-only
  else
    log "ERROR: $REPO_DIR exists but is not a git repo."
    exit 1
  fi
fi

# ===== 4) Optional: create out/ so volume mount always works =====
mkdir -p out

# ===== 5) Run compose with profile =====
CMD="sudo docker compose --profile $PROFILE up --build"

log "Running: $CMD"
log "Sparse paths: $SPARSE_PATHS"

if [ "$USE_TMUX" = "1" ]; then
  sudo apt-get update && sudo apt-get install -y tmux || true
  tmux has-session -t "$TMUX_SESSION" 2>/dev/null && tmux kill-session -t "$TMUX_SESSION" || true
  tmux new-session -d -s "$TMUX_SESSION" "cd '$REPO_DIR' && $CMD |& tee -a out/provision_${PROFILE}.log"
  log "Started tmux session '$TMUX_SESSION'. To view logs: tmux attach -t $TMUX_SESSION"
else
  bash -lc "$CMD"
fi
