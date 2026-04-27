#!/usr/bin/env bash
set -euo pipefail

log() { echo -e "\n[provision] $*\n"; }

# ===== CONFIG =====
REPO_URL="https://github.com/JasonLiu1229/master-thesis.git"
REPO_DIR="${REPO_DIR:-$HOME/master-thesis}"
BRANCH="${BRANCH:-main}"

# Profile to run — t3_eval needs: api + codereader_ollama + t3_eval
PROFILE="${PROFILE:-t3_eval}"

# Sparse-checkout paths for t3_eval + api + codereader_ollama services
SPARSE_PATHS="${SPARSE_PATHS:-docker/t3_eval.Dockerfile docker/api.Dockerfile docker/codereader.Dockerfile code/rename_pipeline code/llm_client.py code/logger.py code/prompts.py requirements/requirements_t3.txt requirements/requirements_api.txt compose.yaml}"

USE_TMUX="${USE_TMUX:-1}"
TMUX_SESSION="${TMUX_SESSION:-t3_eval}"

# ===== HELPERS =====
ensure_pkg() {
  local pkg="$1"
  if ! dpkg -s "$pkg" >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y "$pkg"
  fi
}

# ===== DEPENDENCIES =====
if ! command -v git >/dev/null 2>&1; then
  log "Installing git..."
  ensure_pkg git
fi

if ! command -v git-lfs >/dev/null 2>&1; then
  log "Installing git-lfs..."
  ensure_pkg git-lfs
fi

if ! command -v docker >/dev/null 2>&1; then
  log "Installing Docker + compose plugin..."
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg lsb-release

  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
else
  log "Docker already installed."
fi

# NVIDIA container toolkit (needed for GPU passthrough into containers)
if ! docker info 2>/dev/null | grep -qi nvidia; then
  log "Installing NVIDIA container toolkit (best-effort)..."
  sudo apt-get update -y
  sudo apt-get install -y nvidia-container-toolkit || true
  sudo nvidia-ctk runtime configure --runtime=docker || true
  sudo systemctl restart docker || true
else
  log "Docker already reports NVIDIA runtime."
fi

# ===== REPO SETUP (sparse checkout) =====
log "Ensuring repo exists with sparse checkout..."
if [ ! -d "$REPO_DIR/.git" ]; then
  log "Cloning repo (filtered, no checkout)..."
  git clone --filter=blob:none --no-checkout --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"

  git lfs install --local || true

  git sparse-checkout init --no-cone
  # shellcheck disable=SC2086
  git sparse-checkout set $SPARSE_PATHS

  log "Checking out branch '$BRANCH'..."
  git checkout "$BRANCH"
else
  cd "$REPO_DIR"

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log "Updating existing repo..."
    git fetch --all --prune

    git lfs install --local || true

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

# ===== LFS PULL =====
log "Pulling Git LFS files (include: '$LFS_INCLUDE'${LFS_EXCLUDE:+, exclude: '$LFS_EXCLUDE'})..."
if [ -n "$LFS_EXCLUDE" ]; then
  git lfs pull --include="$LFS_INCLUDE" --exclude="$LFS_EXCLUDE"
else
  git lfs pull --include="$LFS_INCLUDE"
fi

# ===== ENV FILE CHECK =====
if [ ! -f "$REPO_DIR/.env" ]; then
  log "WARNING: No .env file found at $REPO_DIR/.env"
  log "  t3_eval + api require API_KEY, API_URL, and SERVER_SECRET."
  log "  Either copy your .env file here, or set them manually:"
  log "    echo 'API_KEY=sk-...' >> $REPO_DIR/.env"
  log "    echo 'API_URL=https://...' >> $REPO_DIR/.env"
  log "    echo 'SERVER_SECRET=...' >> $REPO_DIR/.env"
fi

mkdir -p "$REPO_DIR/out"

# ===== RUN =====
CMD="sudo docker compose --profile $PROFILE up --build"

log "Running profile: $PROFILE"
log "Sparse paths: $SPARSE_PATHS"
log "LFS include:  $LFS_INCLUDE"
log "Command:      $CMD"

if [ "$USE_TMUX" = "1" ]; then
  sudo apt-get update -y && sudo apt-get install -y tmux || true
  tmux has-session -t "$TMUX_SESSION" 2>/dev/null && tmux kill-session -t "$TMUX_SESSION" || true
  tmux new-session -d -s "$TMUX_SESSION" "cd '$REPO_DIR' && $CMD |& tee -a out/provision_${PROFILE}.log"
  log "Started tmux session '$TMUX_SESSION'."
  log "  View logs:  tmux attach -t $TMUX_SESSION"
  log "  Follow log: tail -f $REPO_DIR/out/provision_${PROFILE}.log"
else
  bash -lc "cd '$REPO_DIR' && $CMD"
fi
