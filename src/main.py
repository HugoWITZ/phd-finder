from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.service import LabSyncService


def main() -> None:
    parser = argparse.ArgumentParser(description="Maintain and query labs index per university.")
    parser.add_argument(
        "command",
        choices=["ensure", "export", "list"],
        help="ensure: refresh if stale, export: write JSON/CSV, list: print DB entries",
    )
    parser.add_argument(
        "--universities",
        nargs="+",
        default=["ETHZ", "EPFL"],
        help="Universities to process (default: ETHZ EPFL).",
    )
    parser.add_argument(
        "--sources",
        default=str(Path(__file__).with_name("sources.yaml")),
        help="Path to sources YAML file.",
    )
    parser.add_argument(
        "--db-path",
        default=str(Path(__file__).resolve().parents[1] / "data" / "labs.db"),
        help="Path to sqlite database.",
    )
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parents[1] / "output"))
    args = parser.parse_args()

    universities = [u.upper() for u in args.universities]
    service = LabSyncService(sources_path=Path(args.sources), db_path=Path(args.db_path))
    try:
        if args.command == "ensure":
            report = [service.ensure_up_to_date(uni) for uni in universities]
            print(json.dumps(report, indent=2))
        elif args.command == "export":
            service.export(universities=universities, output_dir=Path(args.output_dir))
            print(json.dumps({"status": "exported", "output_dir": args.output_dir}, indent=2))
        elif args.command == "list":
            payload = {uni: [e.to_dict() for e in service.get_labs(uni)] for uni in universities}
            print(json.dumps(payload, indent=2, ensure_ascii=False))
    finally:
        service.close()


if __name__ == "__main__":
    main()
