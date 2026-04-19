from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_ROOT / "dataset"

SUPPORTED_KINDS = {
    "csv", "json", "parquet",
    "pdf", "doc", "docx", "rtf", "xls", "xlsx",
    "html", "image", "video"
}