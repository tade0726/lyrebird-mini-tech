# Lyrebird Mini Tech

## What has implemented 

- **Backend API** with table models, integrated with PostgreSQL
  - API routes: `/api/src/users/routes.py` and `/api/src/dictations/routes.py`
  - Database models: `/api/src/users/models.py` and `/api/src/dictations/models.py`
  - Database connection: `/api/core/database.py`
- **Alembic migration** database initialization
  - Migration scripts: `/alembic/versions/`
- **Langsmith trace** integration
  - Implementation: `/api/src/dictations/service.py`
  - OpenAI client wrapper: `_langsmith_trace_wrapper()` method
  - Configuration: `/api/core/config.py`
- **Langsmith prompt management**, supporting further iteration and evaluation with Langsmith toolkit
  - Prompt synchronization: `/api/llm/sync_prompt.py`
  - Prompt usage: `/api/src/dictations/service.py`
- **Streamlit front-end** application
  - Implementation: `/frontend/streamlit_app.py`


## How to setup


I have created a Makefile to help you setup the environment with commands.

### Prepare python environment

1. install uv

https://docs.astral.sh/uv/getting-started/installation/

2. create virtual environment


https://docs.astral.sh/uv/pip/environments/


### Prepare .env file
1. copy .env.example to .env, use this template to fill in the .env file


### Prepare database

1. start docker

```bash
make start-service
```

2. init db with alembic
```bash
make init-db
```


### Start the dev server
```bash
make dev-fastapi
```

### Start the dev frontend
```bash
make dev-frontend
```


## TODO

- [x] docker
- [x] database ORM
- [x] prompts
- [x] service
- [x] fix preference logic, need an edit obj creation then preferences creation
    -  [x] create user edit
    -  [x] create user preferences
- [ ] env frame work
- [ ] frontend

