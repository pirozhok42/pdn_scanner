from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


def format_mtime(ts: float) -> str:
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%b %d %H:%M").lower()


def write_result_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["size", "time", "name"])
        writer.writeheader()

        for row in rows:
            writer.writerow({
                "size": row["size"],
                "time": row["time"],
                "name": row["name"],
            })