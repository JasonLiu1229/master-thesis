FROM python:3.13.9-slim-bookworm

# ---- system prerequisites ----
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# ---- Python dependencies ----
COPY requirements/requirements_tuner.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

RUN pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128

COPY ../code/tuner /app
COPY ../code/model.py /app
COPY ../tools/java-dataset-converter-llm/dataset/test/jsonl /app/in/test
COPY ../tools/java-dataset-converter-llm/dataset/train/jsonl /app/in/train
COPY ../tools/java-dataset-converter-llm/dataset/val/jsonl /app/in/val

WORKDIR /app

CMD ["python3", "main.py", "--tune", "--preprocess"]
