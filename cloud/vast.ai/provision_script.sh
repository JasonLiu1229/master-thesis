#!/usr/bin/env bash
set -euo pipefail

log() { echo -e "\n[provision] $*\n"; }

# ===== CONFIG =====
REPO_URL="https://github.com/JasonLiu1229/master-thesis.git"
REPO_DIR="$HOME/master-thesis"

# Choose what to run:
#   tune          -> runs "tuner"
#   tune_process  -> runs "tuner_preprocess"
PROFILE="${PROFILE:-tune}"

# If you want compose to keep running after provisioning returns,
# we run it inside tmux (recommended on Vast VMs).
USE_TMUX="${USE_TMUX:-1}"
TMUX_SESSION="${TMUX_SESSION:-tuning}"

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

# ===== 3) Clone/pull repo =====
if [ ! -d "$REPO_DIR/.git" ]; then
  log "Cloning repo..."
  git clone "$REPO_URL" "$REPO_DIR"
else
  log "Updating repo..."
  git -C "$REPO_DIR" pull --ff-only
fi

cd "$REPO_DIR"

# ===== 4) Optional: create out/ so volume mount always works =====
mkdir -p out

# ===== 5) Run compose with profile =====
CMD="sudo docker compose --profile $PROFILE up --build"

log "Running: $CMD"

if [ "$USE_TMUX" = "1" ]; then
  sudo apt-get update && sudo apt-get install -y tmux || true
  tmux has-session -t "$TMUX_SESSION" 2>/dev/null && tmux kill-session -t "$TMUX_SESSION" || true
  tmux new-session -d -s "$TMUX_SESSION" "cd '$REPO_DIR' && $CMD |& tee -a out/provision_${PROFILE}.log"
  log "Started tmux session '$TMUX_SESSION'. To view logs: tmux attach -t $TMUX_SESSION"
else
  bash -lc "$CMD"
fi
