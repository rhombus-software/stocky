FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies for wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata first to leverage Docker layer caching
COPY pyproject.toml /app/

RUN pip install --upgrade pip

# Install runtime dependencies. Add any additional packages here if needed.
RUN pip install "uvicorn[standard]" gunicorn "fastapi[standard]" pydantic yfinance

# Copy application source
COPY . /app

EXPOSE 8000

# Use Gunicorn with Uvicorn workers. Render will provide $PORT at runtime.
CMD gunicorn -k uvicorn.workers.UvicornWorker src.app:app --bind 0.0.0.0:${PORT:-8000} --workers 2
