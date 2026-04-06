from __future__ import annotations

from bs4 import BeautifulSoup
from urllib.parse import urlparse

from src.http_client import build_session
from src.schema import LabEntry, canonicalize_url, is_valid_http_url, normalize_lab_name


def collect_epfl_labs(seed_pages: list[str], timeout_s: int = 20) -> list[LabEntry]:
    entries: list[LabEntry] = []
    seen_urls: set[str] = set()
    session = build_session()

    for source in seed_pages:
        response = session.get(source, timeout=timeout_s)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            text = normalize_lab_name(anchor.get_text(" ", strip=True))
            if not text:
                continue
            if text.lower() in {"fr", "en", "de", "it"} or len(text) <= 2:
                continue
            if "epfl.ch/labs/" not in href:
                continue
            parsed = urlparse(href)
            if not parsed.path.startswith("/labs/"):
                continue
            # Keep only canonical lab homepages like /labs/<slug>/.
            path_parts = [p for p in parsed.path.split("/") if p]
            if len(path_parts) != 2 or path_parts[0] != "labs":
                continue

            canonical = canonicalize_url(href)
            if canonical in seen_urls or not is_valid_http_url(canonical):
                continue

            seen_urls.add(canonical)
            entries.append(
                LabEntry(
                    university="EPFL",
                    lab_name=text,
                    lab_website=canonical,
                    source_page=source,
                    extraction_method="selector",
                )
            )

    return entries
