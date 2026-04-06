from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from urllib.parse import urlparse, urlunparse


@dataclass(frozen=True)
class LabEntry:
    university: str
    lab_name: str
    lab_website: str
    source_page: str
    extraction_method: str

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_lab_name(name: str) -> str:
    collapsed = re.sub(r"\s+", " ", name).strip()
    return collapsed


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        parsed = urlparse(f"https://{url.strip()}")
    clean = parsed._replace(fragment="")
    path = clean.path.rstrip("/")
    if path:
        clean = clean._replace(path=path)
    return urlunparse(clean)


def is_valid_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def deduplicate_labs(entries: Iterable[LabEntry]) -> list[LabEntry]:
    deduped: dict[tuple[str, str, str], LabEntry] = {}
    for entry in entries:
        key = (
            entry.university.strip().upper(),
            normalize_lab_name(entry.lab_name).lower(),
            urlparse(entry.lab_website).netloc.lower(),
        )
        if key not in deduped:
            deduped[key] = entry
    return list(deduped.values())
