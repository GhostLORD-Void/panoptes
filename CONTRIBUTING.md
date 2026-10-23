# Contributing

## Development setup

Use Python 3.12 or 3.13 and install [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-groups
uv run pre-commit install
```

## Before submitting

Run the same checks used in CI:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/panoptes
uv run pytest
```

Tests must be deterministic and must not make live network requests. Keep coverage at or above 85%.

## Change process

- Work in a focused branch and keep each pull request phase-scoped.
- Use Conventional Commit messages, for example `feat: add passive DNS provider` or `fix: handle empty provider responses`.
- Add or update tests and documentation with behavior changes.
- Add type annotations to public interfaces and keep strict mypy checks clean.
- Do not add active collection without explicit scope controls and tests.
