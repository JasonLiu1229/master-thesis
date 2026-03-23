FROM nvcr.io/nvidia/pytorch:25.06-py3

RUN truncate -s 0 /etc/pip/constraint.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
  git build-essential curl \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel --no-cache-dir

COPY requirements/requirements_api.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

WORKDIR /app

COPY ../code/app      /app
COPY ../code/model.py /app
COPY ../code/logger.py /app
COPY ../code/prompts.py /app

ENV TOKENIZERS_PARALLELISM=false
ENV ATTN_IMPLEMENTATION=flash_attention_2

CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
