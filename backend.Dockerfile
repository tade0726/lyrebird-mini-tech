FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install PostgreSQL client libraries required for psycopg
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pyproject.toml   
COPY pyproject.toml .

# Copy uv lock file
COPY uv.lock .

# Install dependencies using uv
RUN uv sync --locked

# Copy the application code
COPY api /app/api
COPY alembic.ini .
COPY alembic /app/alembic

# Copy .env file for secrets
COPY .env .

# Expose port for the FastAPI application
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
