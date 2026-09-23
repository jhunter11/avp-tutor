FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen
COPY *.py *.g4 ./
COPY api/ ./api/
COPY tutor/ ./tutor/
COPY harness/ ./harness/
COPY knowledge/ ./knowledge/
COPY data/ ./data/
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1
CMD ["uv", "run", "--no-sync", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
