# Contributing

Thanks for contributing.

## Development setup

```bash
uv sync --dev
```

## Quality gate

Before opening a PR:

```bash
uv run ruff format src
uv run ruff check src tests
uv run pytest
uv run python -m src.main ensure --universities ETHZ EPFL
```

## Pull request checklist

- Keep changes scoped and documented.
- If you modify sources, update `src/sources.yaml` with rationale.
- If you change extraction logic, include before/after sample output.
- Keep public API stable (`ensure`, `list`, `export`) unless discussed first.

## Roadmap

See `BACKLOG.md`.

