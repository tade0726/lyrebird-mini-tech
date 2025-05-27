FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy pyproject.toml
COPY pyproject.toml .

# Copy uv lock file
COPY uv.lock .

# Copy .env file for secrets
COPY .env.docker .env

# Install dependencies using UV
RUN uv sync --locked

# Copy the frontend code
COPY frontend /app/frontend

# Expose port for the Streamlit application
EXPOSE 8501

# Set environment variable for the API URL (will be overridden by docker-compose)
ENV API_BASE_URL=http://backend:8000

# Command to run the Streamlit application
CMD ["uv", "run", "streamlit", "run", "frontend/lyrebird_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
