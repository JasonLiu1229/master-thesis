FROM nvidia/cuda:13.0.1-cudnn-runtime-ubuntu24.04

# ---- install Python 3.8 + pip ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        build-essential \
        curl \
        ca-certificates && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.8 python3.8-dev python3.8-distutils python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.8 /usr/local/bin/python && \
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
    python3.8-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ---- Python deps ----
RUN apt-get update && apt-get install -y --no-install-recommends python3.8-venv && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential python3.8-dev cmake ninja-build \
    && rm -rf /var/lib/apt/lists/*
    
# # Create an isolated venv and use that pip
RUN python3.8 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Make sure Python 3.8 uses its own pip
RUN python3.8 -m ensurepip --upgrade || curl -sS https://bootstrap.pypa.io/get-pip.py | python3.8
RUN python3.8 -m pip install --upgrade "pip<24" "setuptools<70" wheel "pybind11>=2.10,<2.12"

ENV PIP_CONFIG_FILE=/dev/null

# IDK WHY THIS NEEDS TO BE DIFFERENT THAN T1 BECAUSE ELSE IT KEEPS RUNNING INFINITE (SHIT PYTHON)
WORKDIR /tmp/fastwer-build
RUN python3.8 -m pip download fastwer==0.1.3 --no-binary :all: \
 && tar -xzf fastwer-0.1.3.tar.gz \
 && cd fastwer-0.1.3 \
 && sed -i '1i #include <cstdint>' src/fastwer.hpp \
 && sed -i '2i #include <cstdint>' src/fastwer.cpp \
 && python3.8 -m pip install --no-build-isolation --no-use-pep517 --no-index --no-deps .

# Sanity check
RUN python3.8 -c "import fastwer; print('fastwer imported OK')"

COPY ../requirements/requirements_t2.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu124

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
COPY ../rep_package_previous/lp_model /app/lp_model
COPY ../rep_package_previous/pretrain_model /app/pretrain_model
COPY ../rep_package_previous/tg_model /app/tg_model
COPY ../rep_package_previous/code/Dataset/T2 /app/code/Dataset/T2
COPY ../rep_package_previous/code/Models/T2 /app/code/Models/T2
COPY ../rep_package_previous/code/Techniques/T2 /app/code/Techniques/T2
COPY ../rep_package_previous/code/Techniques/__init__.py /app/code/Techniques
COPY ../rep_package_previous/code/Utils /app/code/Utils
COPY ../rep_package_previous/code/run_t2.py /app/code/run_t2.py

WORKDIR /app/code

CMD ["python3.8", "executioner.py", "--pretty", "--out", "../benchmark_out/t2_benchmark_results.json"]
