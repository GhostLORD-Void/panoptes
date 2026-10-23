.PHONY: install lint format typecheck test check clean

install:
	uv sync --all-groups

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy --strict src/panoptes

test:
	uv run pytest

check: lint
	uv run ruff format --check .
	uv run mypy --strict src/panoptes
	uv run pytest

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build
