FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency resolution (optional but nice)
RUN pip install --no-cache-dir uv

COPY pyproject.toml requirements.txt README.md ./
RUN uv pip install --system --no-cache -e .

COPY src ./src

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV GODMOD3_MCP_TRANSPORT=stdio

# Default stdio entrypoint; override for HTTP with transport + port env/command
ENTRYPOINT ["python", "-m", "godmod3_mcp.server"]
CMD ["--transport", "stdio"]
