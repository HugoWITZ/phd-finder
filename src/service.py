from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from src.adapters.epfl import collect_epfl_labs
from src.adapters.ethz import collect_ethz_labs
from src.db import LabDatabase
from src.freshness import compute_source_fingerprint, load_sources
from src.llm_fallback import extract_labs_with_llm
from src.schema import (
    LabEntry,
    canonicalize_url,
    deduplicate_labs,
    is_valid_http_url,
    normalize_lab_name,
)


def _ensure_entry_shape(entries: list[LabEntry]) -> list[LabEntry]:
    clean: list[LabEntry] = []
    for e in entries:
        name = normalize_lab_name(e.lab_name)
        website = canonicalize_url(e.lab_website)
        if not name or not is_valid_http_url(website):
            continue
        clean.append(
            LabEntry(
                university=e.university,
                lab_name=name,
                lab_website=website,
                source_page=e.source_page,
                extraction_method=e.extraction_method,
            )
        )
    return deduplicate_labs(clean)


class LabSyncService:
    def __init__(self, sources_path: Path, db_path: Path) -> None:
        self.sources = load_sources(sources_path)
        self.db = LabDatabase(db_path)

    def close(self) -> None:
        self.db.close()

    def _collect_for_uni(self, uni: str, config: dict) -> list[LabEntry]:
        if uni == "EPFL":
            entries = collect_epfl_labs(seed_pages=config["seed_pages"])
        elif uni == "ETHZ":
            entries = collect_ethz_labs(
                seed_pages=config["seed_pages"],
                allowed_domains=config["allowed_domains"],
                keywords=config["keywords"],
            )
        else:
            entries = []

        if not entries:
            for source in config["seed_pages"]:
                llm_entries = extract_labs_with_llm(uni, source, "")
                entries.extend(llm_entries)
        return _ensure_entry_shape(entries)

    def ensure_up_to_date(self, university: str) -> dict:
        uni = university.upper()
        config = self.sources[uni]
        fingerprint = compute_source_fingerprint(config["seed_pages"])
        state = self.db.get_university_state(uni)

        if state and state["source_fingerprint"] == fingerprint:
            return {
                "university": uni,
                "status": "up_to_date",
                "last_updated_at": state["last_updated_at"],
                "labs_count": len(self.db.get_university_labs(uni)),
            }

        entries = self._collect_for_uni(uni, config)
        self.db.replace_university_labs(uni, entries, fingerprint)
        return {
            "university": uni,
            "status": "updated",
            "labs_count": len(entries),
        }

    def get_labs(self, university: str) -> list[LabEntry]:
        return self.db.get_university_labs(university.upper())

    def export(self, universities: list[str], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        rows: list[dict] = []
        for uni in universities:
            rows.extend(asdict(e) for e in self.get_labs(uni))

        json_path = output_dir / "labs_ethz_epfl.json"
        csv_path = output_dir / "labs_ethz_epfl.csv"
        run_log = output_dir / "run_log.json"

        json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "university",
                    "lab_name",
                    "lab_website",
                    "source_page",
                    "extraction_method",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

        stats = {
            "total": len(rows),
            "counts_by_uni": {u.upper(): len(self.get_labs(u)) for u in universities},
        }
        run_log.write_text(json.dumps(stats, indent=2), encoding="utf-8")
