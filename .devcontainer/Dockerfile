FROM debian:bookworm-slim as builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl

# ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh

FROM mcr.microsoft.com/vscode/devcontainers/base:bookworm

ENV CARGO_HOME="/opt/.cargo/bin"
ENV PATH="$CARGO_HOME/:$PATH"

COPY --from=builder /root/.local/bin/uv $CARGO_HOME/uv

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
