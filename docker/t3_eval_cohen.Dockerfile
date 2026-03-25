FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
  git build-essential curl \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel --no-cache-dir

COPY requirements/requirements_t3.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

RUN pip install --no-cache-dir scipy numpy

COPY ../code/rename_pipeline /app/
COPY ../code/llm_client.py   /app/
COPY ../code/logger.py       /app/
COPY ../code/prompts.py      /app/

ENV TOKENIZERS_PARALLELISM=false

WORKDIR /app

CMD ["python3", "t3.py", "--mode", "eval", "--dir", "in/test", "--force", "--output", "out/java/", "--cohen"]
