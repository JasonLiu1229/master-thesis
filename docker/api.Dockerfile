FROM python:3.13.9-slim-bookworm

# ---- system prerequisites ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash zip unzip ca-certificates git build-essential gcc g++ \
 && rm -rf /var/lib/apt/lists/*

# ---- Python dependencies ----
COPY requirements/requirements_api.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

# ---- application code ----
WORKDIR /app

# still needs to be decided what files needs to be copied
COPY code/app /app

# ---- expose port ----
EXPOSE 8000

# ---- start server ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
