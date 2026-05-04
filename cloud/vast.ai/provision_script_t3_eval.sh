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
SPARSE_PATHS="${SPARSE_PATHS:-docker/t3_eval.Dockerfile docker/api.Dockerfile docker/codereader.Dockerfile docker/t3_eval_oracle.Dockerfile code/rename_pipeline code/app code/codereader_app code/llm_client.py code/logger.py code/model.py code/prompts.py requirements/requirements_t3.txt requirements/requirements_api.txt compose.yaml}"

USE_TMUX="${USE_TMUX:-1}"
TMUX_SESSION="${TMUX_SESSION:-t3_eval}"

# ===== HELPERS =====
wait_for_apt() {
  while sudo fuser /var/lib/apt/lists/lock /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
    log "Waiting for apt lock to be released..."
    sleep 5
  done
}

ensure_pkg() {
  local pkg="$1"
  if ! dpkg -s "$pkg" >/dev/null 2>&1; then
    wait_for_apt
    sudo apt-get update -y
    sudo apt-get install -y "$pkg"
  fi
}

# ===== DEPENDENCIES =====
if ! command -v git >/dev/null 2>&1; then
  log "Installing git..."
  ensure_pkg git
fi

if ! command -v docker >/dev/null 2>&1; then
  log "Installing Docker + compose plugin..."
  wait_for_apt
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg lsb-release

  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

  wait_for_apt
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
else
  log "Docker already installed."
fi

setup_nvidia_toolkit() {
  log "Installing/configuring NVIDIA container toolkit..."
  wait_for_apt

  # Add NVIDIA container toolkit repo if not already present
  if ! apt-cache show nvidia-container-toolkit >/dev/null 2>&1; then
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey |
      sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list |
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' |
      sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
    wait_for_apt
    sudo apt-get update -y
  fi

  sudo apt-get install -y nvidia-container-toolkit

  # Configure Docker daemon to use nvidia runtime
  sudo nvidia-ctk runtime configure --runtime=docker

  # Restart Docker to pick up the new runtime config
  log "Restarting Docker daemon to apply nvidia runtime..."
  sudo systemctl restart docker

  # Wait for Docker to come back up
  local retries=10
  while ! sudo docker info >/dev/null 2>&1; do
    retries=$((retries - 1))
    if [ "$retries" -eq 0 ]; then
      log "ERROR: Docker did not come back up after restart."
      exit 1
    fi
    sleep 2
  done
  log "Docker is back up."
}

verify_gpu_passthrough() {
  # Actually run a container to verify GPU is visible — much more reliable than `docker info`
  log "Verifying GPU passthrough into containers..."
  if sudo docker run --rm --gpus all nvidia/cuda:12.6.3-base-ubuntu24.04 nvidia-smi >/dev/null 2>&1; then
    log "GPU passthrough verified successfully."
    return 0
  else
    log "GPU passthrough test failed."
    return 1
  fi
}

if ! verify_gpu_passthrough 2>/dev/null; then
  log "GPU not accessible in containers — setting up NVIDIA container toolkit..."
  setup_nvidia_toolkit

  # Verify again after setup
  if ! verify_gpu_passthrough; then
    log "WARNING: GPU passthrough still not working after toolkit setup."
    log "  Check that the host has a NVIDIA GPU and drivers installed:"
    log "    nvidia-smi"
    log "  Continuing anyway — containers may run on CPU."
  fi
else
  log "GPU passthrough already working."
fi

# ===== REPO SETUP (sparse checkout) =====
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

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log "Updating existing repo..."
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

# ===== OUTPUT DIR =====
mkdir -p "$REPO_DIR/out"

# ===== ENV FILE CHECK =====
if [ ! -f "$REPO_DIR/.env" ]; then
  log "WARNING: No .env file found at $REPO_DIR/.env"
  log "  t3_eval + api require API_KEY, API_URL, and SERVER_SECRET."
  log "  Either copy your .env file here, or set them manually:"
  log "    echo 'API_KEY=sk-...'         >> $REPO_DIR/.env"
  log "    echo 'API_URL=https://...'    >> $REPO_DIR/.env"
  log "    echo 'SERVER_SECRET=...'      >> $REPO_DIR/.env"
fi

# ===== RUN =====
CMD="sudo docker compose --profile $PROFILE up --build"

log "Running profile: $PROFILE"
log "Sparse paths:    $SPARSE_PATHS"
log "Command:         $CMD"

if [ "$USE_TMUX" = "1" ]; then
  ensure_pkg tmux
  tmux has-session -t "$TMUX_SESSION" 2>/dev/null && tmux kill-session -t "$TMUX_SESSION" || true
  tmux new-session -d -s "$TMUX_SESSION" "cd '$REPO_DIR' && $CMD |& tee -a out/provision_${PROFILE}.log"
  log "Started tmux session '$TMUX_SESSION'."
  log "  View logs:  tmux attach -t $TMUX_SESSION"
  log "  Follow log: tail -f $REPO_DIR/out/provision_${PROFILE}.log"
else
  bash -lc "cd '$REPO_DIR' && $CMD"
fi
