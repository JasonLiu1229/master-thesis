# T1 image (e.g., your GNN env)
FROM python:3.7-slim

# System deps (extend if you need graph libs, e.g., libopenblas, graph-tool, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps needs to be fixed
RUN python -m pip install --upgrade "pip<24" "setuptools<70" wheel
RUN pip install pybind11==2.4.3
RUN pip install fastwer==0.1.3

COPY ../requirements/requirements_t1.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# TODO: Add database files, models, and code

CMD ["python", "run_t1.py", "test"]
