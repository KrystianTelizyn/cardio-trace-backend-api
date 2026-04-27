FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim
WORKDIR /app
ENV UV_NO_DEV=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY . .
ENTRYPOINT ["/entrypoint.sh"]
