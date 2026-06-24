FROM python:3.11.9-slim

WORKDIR /app

# Create non-root user for security
RUN addgroup --system appgroup && adduser --system --create-home --ingroup appgroup appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader vader_lexicon

COPY . .

# Ensure data dir exists and is writable by app user
RUN mkdir -p /app/data && chown -R appuser:appgroup /app/data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/healthz').raise_for_status()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]