FROM nvidia/cuda:13.1.1-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV OLLAMA_HOST=0.0.0.0:11434

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    curl ca-certificates zstd \
  && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

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
CMD ["bash", "-lc", "ollama serve & uvicorn api:app --host 0.0.0.0 --port 8080"]
