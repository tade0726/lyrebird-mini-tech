# Lyrebird - AI-Powered Medical Transcription Platform

> Transform audio recordings into professional clinical documentation with intelligent formatting that learns from your preferences.

![Lyrebird Function Page](./assets/function_page.png)

## Overview

**Lyrebird** is an AI-powered medical transcription and clinical documentation platform that converts audio recordings into structured, professional clinical notes. The system learns from user edits to continuously improve formatting preferences, creating personalized documentation that matches each clinician's style.

### Key Features

- 🎤 **Live Audio Recording** - Record directly in the browser or upload audio files
- 🤖 **AI-Powered Transcription** - OpenAI Whisper for accurate speech-to-text
- 📋 **Clinical Formatting** - GPT-4 transforms transcripts into structured medical notes
- 🧠 **Adaptive Learning** - System learns from your edits to improve future outputs
- 👥 **Multi-User Support** - Secure authentication with personalized preferences
- 📊 **Observability** - LangSmith integration for AI operation monitoring

### How It Works

1. **Record or Upload** - Capture audio through microphone or upload files (WAV, MP3, M4A, OGG)
2. **Transcribe** - OpenAI Whisper converts speech to text
3. **Format** - GPT-4 structures the transcript into professional clinical notes
4. **Edit & Learn** - Make edits and the system learns your formatting preferences
5. **Improve** - Future transcriptions automatically apply your learned preferences

## Technology Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Robust relational database with SQLAlchemy ORM
- **OpenAI API** - Whisper for transcription, GPT-4 for formatting
- **LangSmith** - LLM observability and prompt management
- **JWT Authentication** - Secure user authentication

### Frontend
- **Streamlit** - Interactive web application framework
- **Real-time Audio** - Browser-based microphone recording
- **File Upload** - Multi-format audio file support

### Infrastructure
- **Docker** - Containerized deployment with docker-compose
- **Alembic** - Database migration management
- **uv** - Fast Python package management

## Quick Start

### Docker Compose (Recommended)

The fastest way to get started with mock data included:

1. **Environment Setup**
   ```bash
   # Copy and configure environment variables
   cp .env.example .env.docker
   # Edit .env.docker with your OpenAI API key and other settings
   ```

2. **Start Services**
   ```bash
   make start-service
   ```

3. **Access Applications**
   - **Frontend**: http://localhost:8501
   - **Backend API**: http://localhost:8000/docs
   - **Login**: Use `1@2.com` / password: `1`

### Local Development

For development with live reload:

1. **Install Dependencies**
   ```bash
   # Install uv package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment and install dependencies
   uv sync
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Database Setup**
   ```bash
   # Start PostgreSQL
   make start-service-local
   
   # Run migrations
   make init-db
   ```

4. **Start Development Servers**
   ```bash
   # Terminal 1: Backend API
   make dev-fastapi
   
   # Terminal 2: Frontend
   make dev-frontend
   ```

## API Documentation

### Authentication

All API endpoints (except health check) require JWT authentication:

```bash
# Register new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=your-password"
```

### Core Endpoints

#### Upload Audio for Transcription
```bash
POST /dictations
Content-Type: multipart/form-data
Authorization: Bearer <jwt-token>

# Upload audio file (max 10MB)
curl -X POST "http://localhost:8000/dictations" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -F "file=@recording.wav"
```

#### Submit Edits for Learning
```bash
POST /dictations/preference_extract
Content-Type: application/json
Authorization: Bearer <jwt-token>

{
  "original_text": "Original AI output...",
  "edited_text": "Your edited version..."
}
```

#### Get User Preferences
```bash
GET /dictations/preferences
Authorization: Bearer <jwt-token>
```

For complete API documentation, visit http://localhost:8000/docs when running locally.

## Development Workflow

### Available Commands

```bash
# Development
make dev-fastapi          # Start FastAPI development server
make dev-frontend         # Start Streamlit frontend
make init-db             # Initialize database with migrations

# Docker Services
make start-service        # Start all services with Docker
make stop-service         # Stop all services
make remove-volumes       # Remove Docker volumes (fresh start)

# Code Quality
make format              # Format code with Black
make test               # Run pytest test suite

# AI/LLM
make update-prompts      # Sync prompts with LangSmith
```

### Project Structure

```
lyrebird-mini-tech/
├── api/                 # FastAPI backend
│   ├── core/           # Core configuration and database
│   ├── src/            # API routes and services
│   │   ├── dictations/ # Transcription and formatting logic
│   │   └── users/      # User management
│   ├── llm/            # LLM integration and prompts
│   └── main.py         # FastAPI application entry
├── frontend/           # Streamlit web application
├── alembic/            # Database migrations
├── docs/               # Documentation
└── docker-compose.yaml # Service orchestration
```

### Database Schema

The application uses PostgreSQL with the following main tables:

- **users** - User accounts and authentication
- **dictations** - Audio transcriptions and formatted outputs  
- **user_edits** - User modifications for learning
- **user_preferences** - Extracted formatting preferences

## Environment Variables

Key environment variables for configuration:

```bash
# Database
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/app
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=lyrebird
POSTGRES_DB=app

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# LangSmith (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=lyrebird-mini-tech

# Security
SECRET_KEY=your-secret-key-for-jwt
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
uv run pytest --cov=api --cov-report=html

# Run specific test file
uv run pytest api/tests/test_dictations.py -v
```

## Troubleshooting

### Common Issues

**Database Connection Errors**
- Ensure PostgreSQL is running: `make start-service-local`
- Check DATABASE_URL in your .env file
- Verify database exists: `make init-db`

**OpenAI API Errors**
- Verify OPENAI_API_KEY is set in .env
- Check API quota and billing
- Ensure audio files are under 10MB

**Audio Upload Issues**
- Supported formats: WAV, MP3, M4A, OGG
- Maximum file size: 10MB
- Check browser permissions for microphone access

**Docker Issues**
- Clean rebuild: `make remove-volumes && make start-service`
- Check disk space and Docker daemon status
- Review docker-compose logs for service errors

### Getting Help

1. Check the [FastAPI documentation](http://localhost:8000/docs) when running locally
2. Review application logs in Docker: `docker compose logs -f`
3. Verify environment variables are correctly set
4. Ensure all required services are healthy

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Format code: `make format`
5. Run tests: `make test`
6. Submit a pull request

## License

This project is for educational and demonstration purposes.