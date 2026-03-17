FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src

RUN pip3 install --no-cache-dir -U pip && pip3 install --no-cache-dir ".[api,queue]"

EXPOSE 8000
CMD ["python3", "-m", "uvicorn", "ytranscribe.apps.api_queue_app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

