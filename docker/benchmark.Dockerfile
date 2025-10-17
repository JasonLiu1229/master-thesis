FROM python:3.13.9-slim-bookworm

# ---- system prerequisites ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash zip unzip ca-certificates git build-essential gcc g++ \
 && rm -rf /var/lib/apt/lists/*

COPY ../code/benchmarking/benchmark.py /app/code/benchmark.py
COPY ../out /app/code/out/

WORKDIR /app/code/

CMD ["python", "benchmark.py"]
