# ---- InterviewHub production image ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend
COPY scripts ./scripts

# Run as an unprivileged user (security validation requirement SR-8)
RUN useradd --create-home appuser && mkdir -p /data && chown appuser /data
USER appuser

ENV DATABASE_URL=sqlite:////data/interviewhub.db
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/api/health')"
CMD ["sh", "-c", "python -m scripts.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
