from pathlib import Path

from src.db import LabDatabase
from src.schema import LabEntry


def test_replace_and_fetch_university_labs(tmp_path: Path) -> None:
    db_path = tmp_path / "labs.db"
    db = LabDatabase(db_path)

    entries = [
        LabEntry(
            university="ETHZ",
            lab_name="Robotics Lab",
            lab_website="https://ethz.example/robotics",
            source_page="https://ethz.example/labs",
            extraction_method="adapter",
        ),
        LabEntry(
            university="ETHZ",
            lab_name="Vision Lab",
            lab_website="https://ethz.example/vision",
            source_page="https://ethz.example/labs",
            extraction_method="adapter",
        ),
    ]

    db.replace_university_labs("ETHZ", entries, source_fingerprint="abc")

    fetched = db.get_university_labs("ETHZ")
    state = db.get_university_state("ETHZ")

    assert [e.lab_name for e in fetched] == ["Robotics Lab", "Vision Lab"]
    assert state is not None
    assert state["source_fingerprint"] == "abc"

    db.close()
