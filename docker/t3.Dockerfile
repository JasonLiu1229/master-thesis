FROM python:3.13.9-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential curl ca-certificates zstd\
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

COPY requirements/requirements_t3.txt /tmp/requirements.txt

RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY ../code/rename_pipeline app/
COPY ../code/llm_client.py app/
COPY ../code/logger.py app/
COPY ../code/prompts.py app/

WORKDIR /app

# Single
# CMD ["bash", "-lc", "ollama serve & python3", "t3.py", "--mode", "single", "--file", "pipeline/assets/randoop_example_unit_test_bank.java", "--force", "--output", "out/java/"] 

# # Folder
CMD ["bash", "-lc", "ollama serve & python3", "t3.py", "--mode", "dir", "--dir", "pipeline/assets/", "--force", "--output", "out/java/"] 
