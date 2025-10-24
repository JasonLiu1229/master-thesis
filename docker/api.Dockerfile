FROM python:3.13.9-slim-bookworm

# ---- system prerequisites ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash zip unzip ca-certificates git build-essential gcc g++ \
 && rm -rf /var/lib/apt/lists/*

# ---- poetry ----
RUN curl -sSL https://install.python-poetry.org | python3 -

ARG POETRY_ENV

ENV POETRY_ENV=${POETRY_ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  POETRY_VERSION=2.1.1

COPY ../poetry.lock ../pyproject.toml

RUN poetry install $(test "$POETRY_ENV" == production && echo "--only=main") --no-interaction --no-ansi

# ---- code ---- 
WORKDIR /code

COPY ../code/api /code/
