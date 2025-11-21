# Multi-stage build for CasualMarket MCP Server
FROM python:3.12-slim AS builder

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY README.md LICENSE ./

# Install dependencies to /app/.venv
RUN uv sync --frozen --no-dev

# Final stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src ./src
COPY README.md ./
COPY LICENSE ./

# Copy data directory if exists
COPY src/data ./src/data

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose SSE port
EXPOSE 8000

# Health check - check if port 8000 is listening using Python
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 8000), timeout=2)" || exit 1

# Run the SSE server by default
CMD ["python", "-m", "src.sse_server"]
