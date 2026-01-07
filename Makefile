.PHONY: install run lint test clean

install:
	poetry install
	poetry run pre-commit install

run:
	poetry run uvicorn backend.app.main:app --reload

lint:
	poetry run ruff check .
	poetry run ruff format . --check
	poetry run mypy backend

test:
	poetry run pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .mypy_cache
