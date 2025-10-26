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

# still needs to be decided what files needs to be copied
COPY ../code/app /app
COPY ../code/model.py /app

# ---- expose port ----
EXPOSE 8000

# ---- start server ----
CMD ["fastapi", "run", "main.py", "--port", "8000"]
