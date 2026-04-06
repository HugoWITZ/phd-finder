# PhD Lab Scraper

Open-source Python project to maintain a university labs index and keep it fresh.

Current target universities:
- ETHZ
- EPFL

## Problem solved

When a university is requested, the system:
1. Quickly checks if the memorized lab list is still up to date (fingerprint on source pages).
2. Reuses cached labs when up to date.
3. Re-scrapes and updates the local database when stale.

This makes later PhD-list extraction faster and more reliable because lab links stay curated.

## Architecture

- `src/main.py`: CLI (`ensure`, `list`, `export`)
- `src/service.py`: orchestration and refresh logic
- `src/freshness.py`: source fingerprint checks
- `src/db.py`: SQLite storage (`labs`, `uni_state`)
- `src/adapters/`: per-university extractors
- `src/llm_fallback.py`: optional fallback extraction using `OPENAI_API_KEY`
- `src/sources.yaml`: official source pages per university

## Quick start

```bash
uv sync --dev
uv run python -m src.main ensure --universities ETHZ EPFL
uv run python -m src.main export --universities ETHZ EPFL
uv run python -m src.main list --universities ETHZ
```

Generated exports:
- `output/labs_ethz_epfl.json`
- `output/labs_ethz_epfl.csv`

Local database:
- `data/labs.db`

## Environment variables

- `OPENAI_API_KEY` (optional): enable LLM fallback extraction
- `OPENAI_BASE_URL` (optional, default: `https://api.openai.com/v1`)
- `OPENAI_MODEL` (optional, default: `gpt-4.1-mini`)

## Engineering practices

- Deterministic adapters first, LLM fallback optional.
- Typed model (`LabEntry`) + normalization and dedup.
- Persistent state in SQLite with source fingerprints and last update timestamps.
- Separation of concerns: adapters, service layer, persistence, CLI.

## Open-source contribution

1. Fork the repo
2. Create a branch
3. Run formatting:
   - `uv run ruff format src`
4. Open a PR with:
   - what changed
   - sample output impact
   - any source pages added/updated

See `BACKLOG.md` for roadmap.

## License

MIT (see `LICENSE`).

