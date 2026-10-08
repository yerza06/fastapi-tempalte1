.PHONY: help run sync format test test-unit test-integration create-user

help:
	@echo "make run               Запустить приложении"
	@echo "make sync              Установить зависимости"
	@echo "make format            Форматировать код (ruff)"
	@echo "make test              Запустить все тесты"
	@echo "make test-unit         Запустить только unit-тесты"
	@echo "make test-integration  Запустить интеграционные тесты (нужен PostgreSQL)"
	@echo "make create-user       Создать нового пользователя"

run:
	uv run -m src.main

sync:
	uv sync --frozen

format:
	uv run ruff format .
	uv run ruff check . --fix

test:
	uv run pytest -v

test-unit:
	uv run pytest -v tests/unit

test-integration:
	uv run pytest -v tests/integration

create-user:
	uv run -m scripts.create_user
