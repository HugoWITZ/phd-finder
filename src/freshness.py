from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json

import yaml

from src.http_client import build_session


def load_sources(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)["universities"]


def compute_source_fingerprint(seed_pages: list[str], timeout_s: int = 20) -> str:
    session = build_session()
    hasher = sha256()
    for url in sorted(seed_pages):
        hasher.update(url.encode("utf-8"))
        try:
            resp = session.get(url, timeout=timeout_s)
            resp.raise_for_status()
            body = resp.text
        except Exception:
            body = ""
        # Lightweight fingerprint from beginning of page body.
        hasher.update(body[:50000].encode("utf-8", errors="ignore"))
    return hasher.hexdigest()


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
