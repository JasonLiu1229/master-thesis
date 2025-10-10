# T1 image (e.g., your GNN env)
FROM python:3.7-slim

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

COPY ../requirements/requirements_t1.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Install Java 12 using SDKMAN
ENV SDKMAN_DIR=/usr/local/sdkman SDKMAN_AUTO_SELF_UPDATE=false SDKMAN_ASSUME_YES=true
RUN curl -s https://get.sdkman.io | bash && \
    bash -lc "source ${SDKMAN_DIR}/bin/sdkman-init.sh && sdk install java 12.0.2.hs-adpt"
ENV JAVA_HOME=${SDKMAN_DIR}/candidates/java/current
ENV PATH="${JAVA_HOME}/bin:${PATH}"
RUN java -version

COPY ../rep_package_previous/GGNN /app/GGNN
COPY ../rep_package_previous/code/Dataset/T1 /app/code/Dataset/T1
COPY ../rep_package_previous/code/Models/T1 /app/code/Models/T1
COPY ../rep_package_previous/code/Techniques/T1 /app/code/Techniques/T1
COPY ../rep_package_previous/code/Techniques/__init__.py /app/code/Techniques
COPY ../rep_package_previous/code/Utils /app/code/Utils
COPY ../rep_package_previous/code/run_t1.py /app/code/run_t1.py

CMD ["python", "run_t1.py", "test"]
