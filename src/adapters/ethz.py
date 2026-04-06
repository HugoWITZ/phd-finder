from __future__ import annotations

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import requests

from src.http_client import build_session
from src.schema import LabEntry, canonicalize_url, is_valid_http_url, normalize_lab_name


def _is_allowed_domain(url: str, allowed_domains: set[str]) -> bool:
    domain = urlparse(url).netloc.lower()
    return any(domain.endswith(d) for d in allowed_domains)


def _looks_like_lab(name: str, url: str, keywords: list[str]) -> bool:
    low_name = name.lower()
    low_url = url.lower()
    excluded_tokens = {
        "navigation",
        "content",
        "footer",
        "homepage",
        "contact",
        "sitemap",
        "departments",
        "department",
        "guidelines",
        "pdf",
        "research contracts",
    }
    if any(token in low_name for token in excluded_tokens):
        return False
    if low_url.endswith(".pdf"):
        return False

    keyword_match = any(k in low_name or k in low_url for k in keywords)
    # Keep external or center/lab pages that are likely entity homepages.
    strong_url_pattern = bool(
        re.search(r"(lab|labs|laboratory|center|centre|institute|group|\.ethz\.ch)", low_url)
    )
    return keyword_match and strong_url_pattern


def _parse_links(html: str, base_url: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[tuple[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"].strip())
        name = normalize_lab_name(anchor.get_text(" ", strip=True))
        if not name:
            continue
        links.append((name, href))
    return links


def collect_ethz_labs(
    seed_pages: list[str],
    allowed_domains: list[str],
    keywords: list[str],
    timeout_s: int = 20,
) -> list[LabEntry]:
    allowed = set(allowed_domains)
    entries: list[LabEntry] = []
    visited_pages: set[str] = set()
    seen_websites: set[str] = set()
    session = build_session()

    queue = list(seed_pages)
    max_pages = 35

    while queue and len(visited_pages) < max_pages:
        page = queue.pop(0)
        if page in visited_pages:
            continue
        visited_pages.add(page)

        try:
            response = session.get(page, timeout=timeout_s)
            response.raise_for_status()
        except requests.RequestException:
            continue

        links = _parse_links(response.text, page)
        for name, url in links:
            if not is_valid_http_url(url):
                continue
            if not _is_allowed_domain(url, allowed):
                continue

            # Crawl likely "index" pages one level deep for more groups.
            if re.search(
                r"(departments?|research|institutes?|units|organisation|centres?|centers?)",
                url.lower(),
            ):
                if url not in visited_pages and url not in queue and len(queue) < 200:
                    queue.append(url)

            if not _looks_like_lab(name, url, keywords):
                continue

            website = canonicalize_url(url)
            if website in seen_websites:
                continue
            seen_websites.add(website)

            entries.append(
                LabEntry(
                    university="ETHZ",
                    lab_name=name,
                    lab_website=website,
                    source_page=page,
                    extraction_method="selector",
                )
            )
            if len(entries) >= 500:
                return entries

    return entries
