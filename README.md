# PANOPTES

**PANOPTES** is a passive-first, graph-native, temporally aware reconnaissance framework for professional bug bounty hunters and authorized security teams.

## Project status

Pre-alpha. The repository is being delivered in small, phase-scoped pull requests. P0 establishes the packaging, developer workflow, and continuous-integration baseline; reconnaissance capabilities will arrive in later approved phases.

## Design principles

- **Passive-first:** prefer public, low-impact data sources and make active checks explicit.
- **Graph-native:** represent assets and their relationships as first-class graph data.
- **Temporal:** retain observations with timestamps so changes can be reasoned about over time.
- **Composable:** use typed models and plugin boundaries as features are introduced.
- **Operationally safe:** scope and authorization are prerequisites for any future active collection.

## Requirements

- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/) for environment and dependency management

## Install for development

```bash
uv sync --all-groups
uv run panoptes --version
```

Run quality checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/panoptes
uv run pytest
```

## Current CLI

```text
panoptes --help
panoptes --version
```

The bootstrap CLI intentionally does not perform network reconnaissance.

## Scope and responsible use

PANOPTES is intended for assets you own or are explicitly authorized to assess. P0 contains no scanning, exploitation, or payload functionality. Any future active collection must have explicit scope controls, conservative defaults, rate limits, and documented detection/hardening guidance.

## Roadmap

See [CHANGELOG.md](CHANGELOG.md) for the phase history and [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow.
