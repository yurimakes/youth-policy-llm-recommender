FROM python:3.10-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    API_HOST=0.0.0.0 PORT=8000 POLICY_DB_PATH=/data/policies.sqlite3 \
    API_CORS_ORIGINS="" POLICY_EXPLANATION_AI_ENABLED=0
COPY requirements-api.txt requirements-service.txt ./
RUN python -m pip install --no-cache-dir -r requirements-service.txt
COPY api.py ./
COPY src/ ./src/
COPY demo/ ./demo/
COPY scripts/run_intake_api.py scripts/check_readiness.py ./scripts/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "scripts/check_readiness.py"]
CMD ["python", "scripts/run_intake_api.py"]
