from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FileKind(str, Enum):
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    RTF = "rtf"
    XLS = "xls"
    XLSX = "xlsx"
    HTML = "html"
    IMAGE = "image"
    VIDEO = "video"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class FileTask:
    path: Path
    rel_path: str
    ext: str
    kind: FileKind
    size_bytes: int