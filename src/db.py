from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3

from src.schema import LabEntry


class LabDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS labs (
              university TEXT NOT NULL,
              lab_name TEXT NOT NULL,
              lab_website TEXT NOT NULL,
              source_page TEXT NOT NULL,
              extraction_method TEXT NOT NULL,
              UNIQUE(university, lab_name, lab_website)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS uni_state (
              university TEXT PRIMARY KEY,
              last_updated_at TEXT NOT NULL,
              source_fingerprint TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def replace_university_labs(
        self, university: str, entries: list[LabEntry], source_fingerprint: str
    ) -> None:
        self.conn.execute("DELETE FROM labs WHERE university = ?", (university,))
        self.conn.executemany(
            """
            INSERT INTO labs (university, lab_name, lab_website, source_page, extraction_method)
            VALUES (:university, :lab_name, :lab_website, :source_page, :extraction_method)
            """,
            [asdict(e) for e in entries],
        )
        self.conn.execute(
            """
            INSERT INTO uni_state (university, last_updated_at, source_fingerprint)
            VALUES (?, ?, ?)
            ON CONFLICT(university) DO UPDATE SET
              last_updated_at = excluded.last_updated_at,
              source_fingerprint = excluded.source_fingerprint
            """,
            (
                university,
                datetime.now(timezone.utc).isoformat(),
                source_fingerprint,
            ),
        )
        self.conn.commit()

    def get_university_labs(self, university: str) -> list[LabEntry]:
        rows = self.conn.execute(
            """
            SELECT university, lab_name, lab_website, source_page, extraction_method
            FROM labs
            WHERE university = ?
            ORDER BY lab_name ASC
            """,
            (university,),
        ).fetchall()
        return [LabEntry(**dict(r)) for r in rows]

    def get_university_state(self, university: str) -> dict | None:
        row = self.conn.execute(
            """
            SELECT university, last_updated_at, source_fingerprint
            FROM uni_state
            WHERE university = ?
            """,
            (university,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def export_json(self, output_path: Path, universities: list[str]) -> None:
        payload = {}
        for uni in universities:
            payload[uni] = [asdict(e) for e in self.get_university_labs(uni)]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
