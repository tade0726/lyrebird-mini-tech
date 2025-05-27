format:
	black .

test:
	uv run pytest -s -v api/tests

start-service:
	docker compose up --build -d

stop-service:
	docker compose down

remove-volumes:
	docker compose down --volumes

update-prompts:
	PYTHONPATH=. uv run python -m api.core.llm.sync_prompt

dev-fastapi:
	uv run fastapi dev api/main.py