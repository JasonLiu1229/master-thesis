FROM pytorch/pytorch:2.11.0-cuda13.0-cudnn9-runtime

RUN pip install --upgrade pip setuptools wheel --no-cache-dir --break-system-packages

RUN pip install --no-cache-dir --break-system-packages \
  "fastapi[standard]>=0.113.0,<0.114.0" \
  httpx==0.28.1 \
  pydantic-settings==2.11.0 \
  python-dotenv==1.1.1 \
  pydantic==2.12.3 \
  hf-xet==1.2.0 \
  peft==0.18.1

RUN pip install --no-cache-dir --break-system-packages \
  transformers==4.55.2 \
  accelerate==1.10.0 \
  bitsandbytes

WORKDIR /app

COPY ../code/app      /app
COPY ../code/model.py /app
COPY ../code/logger.py /app
COPY ../code/prompts.py /app

ENV TOKENIZERS_PARALLELISM=false
ENV ATTN_IMPLEMENTATION=eager

CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
