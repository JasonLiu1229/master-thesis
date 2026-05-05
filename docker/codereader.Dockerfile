FROM ollama/ollama:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_NUM_PARALLEL=1

RUN apt-get update && apt-get install -y --no-install-recommends \
  python3 python3-pip python3-venv \
  curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python -m pip install --no-cache-dir -U pip setuptools wheel

RUN python -m pip install --no-cache-dir \
  codereader \
  fastapi uvicorn pydantic

WORKDIR /app
COPY ../code/codereader_app/main.py /app/api.py
COPY ../code/codereader_app/codereader.yml /app

EXPOSE 11434 8080

ENTRYPOINT []
CMD ["bash", "-lc", "\
  set -euo pipefail; \
  start_ollama() { \
  while true; do \
  echo '[watchdog] Starting ollama serve...'; \
  ollama serve & \
  OLLAMA_PID=$!; \
  wait $OLLAMA_PID; \
  echo '[watchdog] Ollama died (exit $?), restarting in 3s...'; \
  sleep 3; \
  done; \
  }; \
  start_ollama & \
  until curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; do sleep 2; done; \
  echo 'Ollama is up'; \
  if [ ! -f /root/.ollama/.codereader_inited ]; then \
  codereader init -c ${CODEREADER_CONFIG_FILE} && touch /root/.ollama/.codereader_inited; \
  fi; \
  until curl -sf http://localhost:11434/api/tags | grep -q 'models'; do \
  echo 'Waiting for models...'; sleep 5; \
  done; \
  exec uvicorn api:app --host 0.0.0.0 --port 8080 \
  "]
