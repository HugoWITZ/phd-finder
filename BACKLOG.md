# Backlog

## P0
- Improve ETHZ coverage by adding department-level research/lab pages.
- Add robust URL health checks with retry budget and status caching.
- Add unit tests for adapters and dedup logic.

## P1
- Add support for dynamic university onboarding via config templates.
- Add incremental diff report (new/removed labs on refresh).
- Add CI (format + tests + smoke run).

## P2
- Add API server (`GET /labs/{uni}`, `POST /refresh/{uni}`).
- Add plugin system for community-contributed adapters.
- Add quality scoring for extraction confidence.

## Future (PhD pipeline)
- Reuse lab links to crawl PhD openings.
- Add topic filtering (embeddings + optional LLM ranking).
- Add notification channel (email/Slack/Telegram) for new relevant calls.

