FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mcp_graylog/ ./mcp_graylog/
COPY entrypoint.sh ./entrypoint.sh

RUN pip install --no-cache-dir . \
    && chmod +x ./entrypoint.sh \
    && useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 8000), timeout=5).close()" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["mcp-graylog", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000", "--path", "/mcp"]
