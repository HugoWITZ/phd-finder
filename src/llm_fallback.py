from __future__ import annotations

import json
import os
from typing import Any

import requests

from src.schema import LabEntry, canonicalize_url, is_valid_http_url, normalize_lab_name


def extract_labs_with_llm(university: str, source_page: str, page_text: str) -> list[LabEntry]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    prompt = (
        "Extract laboratory entries from the text below.\n"
        "Return ONLY valid JSON array. Each object must include keys: "
        '"lab_name", "lab_website". Do not include markdown.\n'
        "Keep only actual labs/research groups with specific homepage URLs.\n\n"
        f"University: {university}\n"
        f"Source: {source_page}\n\n"
        f"Text:\n{page_text[:12000]}"
    )
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(
            f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        items = json.loads(text)
    except Exception:
        return []

    results: list[LabEntry] = []
    if not isinstance(items, list):
        return results

    for item in items:
        if not isinstance(item, dict):
            continue
        name = normalize_lab_name(str(item.get("lab_name", "")).strip())
        website = canonicalize_url(str(item.get("lab_website", "")).strip())
        if not name or not is_valid_http_url(website):
            continue
        results.append(
            LabEntry(
                university=university,
                lab_name=name,
                lab_website=website,
                source_page=source_page,
                extraction_method="llm_fallback",
            )
        )
    return results
