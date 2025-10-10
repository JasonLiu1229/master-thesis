# T1 image (e.g., your GNN env)
FROM python:3.8.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/code

# Python deps needs to be fixed
RUN python -m pip install --upgrade "pip<24" "setuptools<70" wheel
RUN pip install pybind11==2.4.3
RUN pip install fastwer==0.1.3

COPY ../requirements/requirements_t2.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu124

# Install Java 12 using SDKMAN
ENV SDKMAN_DIR=/usr/local/sdkman SDKMAN_AUTO_SELF_UPDATE=false SDKMAN_ASSUME_YES=true
RUN curl -s https://get.sdkman.io | bash && \
    bash -lc "source ${SDKMAN_DIR}/bin/sdkman-init.sh && sdk install java 12.0.2.hs-adpt"
ENV JAVA_HOME=${SDKMAN_DIR}/candidates/java/current
ENV PATH="${JAVA_HOME}/bin:${PATH}"
RUN java -version

COPY ../rep_package_previous/lp_model /app/lp_model
COPY ../rep_package_previous/pretrain_model /app/pretrain_model
COPY ../rep_package_previous/tg_model /app/tg_model
COPY ../rep_package_previous/code/Dataset/T2 /app/code/Dataset/T2
COPY ../rep_package_previous/code/Models/T2 /app/code/Models/T2
COPY ../rep_package_previous/code/Techniques/T1 /app/code/Techniques/T2
COPY ../rep_package_previous/code/Techniques/__init__.py /app/code/Techniques
COPY ../rep_package_previous/code/Utils /app/code/Utils
COPY ../rep_package_previous/code/run_t2.py /app/code/run_t2.py

CMD ["python", "run_t2.py", \
    "--lp_model", "../lp_model", \
    "--tg_model", "../tg_model", \
    "--pretrain_model", "../pretrain_model", \
    "--test_json", "Dataset/T2/test/test.json"\
    ]
