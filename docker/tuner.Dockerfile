FROM nvcr.io/nvidia/pytorch:25.06-py3

WORKDIR /workspace

ENV TOKENIZERS_PARALLELISM=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel packaging ninja

RUN pip install psutil

RUN pip install flash_attn --no-build-isolation

COPY requirements/requirements_tuner.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY ../code/tuner /app
COPY ../code/model.py /app
COPY ../code/logger.py /app
COPY ../code/prompts.py /app

COPY ../tools/java-dataset-converter-llm/dataset/train/jsonl /app/in/train
COPY ../tools/java-dataset-converter-llm/dataset/val/jsonl   /app/in/val
COPY ../tools/java-dataset-converter-llm/dataset/test/jsonl  /app/in/test

WORKDIR /app

CMD ["python3", "main.py", "--preprocess", "--tune"]
# CMD ["python3", "main.py", "--preprocess"]
