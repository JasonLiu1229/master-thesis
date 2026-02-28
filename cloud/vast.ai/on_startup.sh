#!/bin/bash
set -e

apt-get update -y
apt-get install -y curl git

curl -fsSL https://raw.githubusercontent.com/JasonLiu1229/master-thesis/refs/heads/main/cloud/vast.ai/provision_script.sh -o /root/provision_script.sh

chmod +x /root/provision_script.sh

PROFILE=tune USE_TMUX=0 /root/provision_script.sh
