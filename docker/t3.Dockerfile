FROM python:3.13.9-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/requirements_t3.txt /tmp/requirements.txt

RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY ../code/rename_pipeline app/
COPY ../code/llm_client.py app/pipeline/
COPY ../code/logger.py app/

CMD ["python3", "t3.py"]
