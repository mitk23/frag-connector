ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION} AS builder

ENV UV_SYSTEM_PYTHON=true \
  UV_LINK_MODE=copy

WORKDIR /app
COPY pyproject.toml uv.lock README.md /app/

RUN pip install --upgrade pip && \
  pip install uv && \
  uv export --frozen --no-dev --format requirements-txt > requirements.txt && \
  uv pip install -r requirements.txt 


FROM python:${PYTHON_VERSION}-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

WORKDIR /
