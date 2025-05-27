FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install PostgreSQL client libraries required for psycopg
RUN apt-get update && apt-get install -y libpq-dev gcc postgresql-client postgresql-client-common && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pyproject.toml
COPY pyproject.toml .

# Copy uv lock file
COPY uv.lock .

# Install dependencies using UV
RUN uv sync --locked

# Copy necessary files for migrations
COPY alembic.ini .
COPY alembic /app/alembic
COPY api /app/api

# Copy .env file for secrets
COPY .env .

# Create script to run migrations and load SQL dumps
COPY <<EOF /app/init-db.sh
#!/bin/bash
set -e

echo "Running database migrations..."
uv run alembic upgrade head

echo "Loading SQL dump files..."
PGPASSWORD=${POSTGRES_PASSWORD:-lyrebird} psql -h postgres -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-app} -f /sql_dump/alembic_version.sql
PGPASSWORD=${POSTGRES_PASSWORD:-lyrebird} psql -h postgres -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-app} -f /sql_dump/users.sql
PGPASSWORD=${POSTGRES_PASSWORD:-lyrebird} psql -h postgres -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-app} -f /sql_dump/dictations.sql
PGPASSWORD=${POSTGRES_PASSWORD:-lyrebird} psql -h postgres -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-app} -f /sql_dump/user_edits.sql
PGPASSWORD=${POSTGRES_PASSWORD:-lyrebird} psql -h postgres -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-app} -f /sql_dump/user_preferences.sql

echo "Database initialization completed successfully!"
EOF

# Make the script executable
RUN chmod +x /app/init-db.sh

# Install PostgreSQL client for SQL dump loading
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Run the initialization script
CMD ["/app/init-db.sh"]
