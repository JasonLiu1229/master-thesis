# T1 image (e.g., your GNN env)
FROM nvidia/cuda:13.0.1-cudnn-runtime-ubuntu24.04

# ---- install Python 3.7 + pip ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        build-essential \
        curl \
        ca-certificates && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.7 python3.7-dev python3.7-distutils python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.7 /usr/local/bin/python && \
    ln -sf /usr/bin/pip3 /usr/local/bin/pip

# Sanity check
RUN python --version && pip --version

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# ---- system prerequisites ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash zip unzip ca-certificates git \
 && rm -rf /var/lib/apt/lists/*

USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3.7-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ---- Python deps ----
RUN apt-get update && apt-get install -y --no-install-recommends python3.7-venv && \
    rm -rf /var/lib/apt/lists/*
    
# # Create an isolated venv and use that pip
RUN python3.7 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip3 install --upgrade "pip<24" "setuptools<70" wheel
RUN pip3 install "pybind11>=2.10,<2.12"

WORKDIR /tmp/fastwer-build
RUN pip3 download fastwer==0.1.3 --no-binary :all: \
 && tar -xzf fastwer-0.1.3.tar.gz \
 && cd fastwer-0.1.3 \
 && sed -i '1i #include <cstdint>' src/fastwer.hpp \
 && sed -i '2i #include <cstdint>' src/fastwer.cpp \
 && pip3 install --no-build-isolation .

COPY ../requirements/requirements_t1.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# ---- SDKMAN! + Java ----
ARG JAVA_DIST=12.0.2.hs-adpt

ENV SDKMAN_DIR=/usr/local/sdkman \
    SDKMAN_AUTO_SELF_UPDATE=false \
    SDKMAN_ASSUME_YES=true

RUN curl -s https://get.sdkman.io | bash && \
    bash -lc "source ${SDKMAN_DIR}/bin/sdkman-init.sh && sdk install java ${JAVA_DIST} && sdk flush archives && sdk flush temp"

ENV JAVA_HOME=${SDKMAN_DIR}/candidates/java/current
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Sanity check
RUN java -version

# ---- App code ----
COPY ../rep_package_previous/GGNN /app/GGNN
COPY ../rep_package_previous/code/Dataset/T1 /app/code/Dataset/T1
COPY ../rep_package_previous/code/Models/T1 /app/code/Models/T1
COPY ../rep_package_previous/code/Techniques/T1 /app/code/Techniques/T1
COPY ../rep_package_previous/code/Techniques/__init__.py /app/code/Techniques
COPY ../rep_package_previous/code/Utils /app/code/Utils
COPY ../rep_package_previous/code/run_t1.py /app/code/run_t1.py

COPY ../code/benchmarking/t1_executioner.py /app/code/t1_executioner.py
COPY ../code/benchmarking/t1_parser.py /app/code/t1_parser.py

WORKDIR /app/code

CMD ["python3.7", "t1_executioner.py", "--run-args", "test"]
