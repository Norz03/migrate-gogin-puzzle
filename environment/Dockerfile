FROM python:3.13-slim@sha256:7f481c5a93edb3e40409a80be2a0953f938b5561a3ec95eb1df6777cf0faed90

WORKDIR /app

# Install system dependencies (tmux & asciinema are required)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       asciinema \
       ca-certificates \
       git \
    golang-go \
       tmux \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast offline venv management
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

# Copy environment files into the container
COPY . /app/

# Pre-build verifier environment using uv venv (offline isolation)
RUN uv venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir pytest==8.3.2 pytest-json-ctrf==0.1.1

RUN python /app/scripts/init_db.py