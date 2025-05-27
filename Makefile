format:
	black .

test:
	uv run pytest -s -v api/tests

start-service:
	docker compose -f docker-compose.yaml up --build -d

stop-service:
	docker compose -f docker-compose.yaml down

remove-volumes:
	docker compose -f docker-compose.yaml down --volumes

start-service-local:
	docker compose -p lyrebird-mini-tech-local -f docker-compose-local.yaml up --build -d

stop-service-local:
	docker compose -p lyrebird-mini-tech-local -f docker-compose-local.yaml down

remove-volumes-local:
	docker compose -p lyrebird-mini-tech-local -f docker-compose-local.yaml down --volumes

update-prompts:
	PYTHONPATH=. uv run python -m api.llm.sync_prompt

dev-fastapi:
	uv run fastapi dev api/main.py

init-db:
	uv run alembic upgrade head

dev-frontend:
	uv run streamlit run frontend/lyrebird_app.py