FROM python:3.13.9-slim-bookworm

# ---- system prerequisites ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash zip unzip ca-certificates git build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# ---- Python dependencies ----
COPY requirements/requirements_api.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

RUN pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# ---- application code ----
WORKDIR /app

COPY ../code/app /app
COPY ../code/model.py /app
COPY ../../out/model/checkpoint-* /app/model/
COPY ../code/logger.py /app

CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
