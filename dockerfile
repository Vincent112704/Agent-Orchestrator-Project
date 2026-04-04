FROM python:3.10-slim

WORKDIR /app

RUN mkdir -p /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .
COPY scripts/entrypoint.sh /app/scripts/entrypoint.sh
COPY .vscode/launch.json /app/.vscode/launch.json

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('/app/data/orchestrator.db').cursor().execute('SELECT 1')" || exit 1

CMD ["./scripts/entrypoint.sh"]
