help:
	@echo "make run Запустить приложении"

run:
	uv run -m src.main

sync:
	uv sync --frozen

format:
	uv run ruff format .
	uv run ruff check . --fix
