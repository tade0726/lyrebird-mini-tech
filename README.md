# Lyrebird Mini Tech

Lyrebird Mini Tech is a small demo application that showcases a speech dictation workflow built with **FastAPI** and **Streamlit**. Audio is transcribed using OpenAI's `whisper-1` model, formatted with user preferences and stored in PostgreSQL. The project integrates with **LangSmith** for prompt management and tracing.

![Function Page](./assets/function_page.png)

## Features

- **FastAPI backend** with authentication and PostgreSQL models
- **Streamlit frontend** for uploading audio and viewing formatted results
- **OpenAI Whisper** audio transcription and GPT formatting
- **User preference extraction** from edited text
- **LangSmith integration** for tracing and prompt storage
- **Alembic migrations** for database setup

## Getting Started

### Docker Compose (recommended)

1. Copy `.env.docker.example` to `.env.docker` and adjust the values.
2. Start the services:

```bash
make start-service
```

The UI will be available at [http://localhost:8501](http://localhost:8501) and the API docs at [http://localhost:8000/docs](http://localhost:8000/docs).
Use `1@2.com` with password `1` to sign in to the demo.

### Local Development

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and create a virtual environment:

```bash
uv venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
uv pip install -r uv.lock
```

3. Copy `.env.docker.example` to `.env` and update the environment variables. A minimal configuration looks like:

```env
PROJECT_NAME="Lyrebird Mini Tech API"
ENV=local
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=lyrebird
JWT_SECRET="change-me-in-production"
OPENAI_API_KEY="your-openai-api-key"
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY="your-langsmith-api-key"
LANGSMITH_PROJECT="your-langsmith-project"
API_BASE_URL="http://backend:8000"
```

4. Start the local Postgres service (this only creates the database instance):

```bash
make start-service-local
```

5. Initialize the database schema:

```bash
make init-db
```

6. Run the development servers:

```bash
make dev-fastapi
```

In a separate terminal:

```bash
make dev-frontend
```

