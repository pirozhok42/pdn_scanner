from __future__ import annotations

from pathlib import Path
from typing import Iterator

from scanner.types import FileKind, FileTask


EXTENSION_MAP = {
    ".csv": FileKind.CSV,
    ".json": FileKind.JSON,
    ".parquet": FileKind.PARQUET,
    ".pdf": FileKind.PDF,
    ".doc": FileKind.DOC,
    ".docx": FileKind.DOCX,
    ".rtf": FileKind.RTF,
    ".xls": FileKind.XLS,
    ".xlsx": FileKind.XLSX,
    ".html": FileKind.HTML,
    ".htm": FileKind.HTML,
    ".tif": FileKind.IMAGE,
    ".tiff": FileKind.IMAGE,
    ".mp4": FileKind.VIDEO,
}

# Файлы, которые нужно обрабатывать (исключаем JPG, PNG, GIF, BMP)
FOCUSED_EXTENSIONS = {".csv", ".json", ".parquet", ".pdf", ".tif", ".tiff", ".mp4"}


def detect_file_kind(path: Path) -> FileKind:
    return EXTENSION_MAP.get(path.suffix.lower(), FileKind.UNKNOWN)


def iter_files(root: Path) -> Iterator[FileTask]:
    root = root.resolve()

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        # Фильтруем файлы - обрабатываем только нужные расширения
        if path.suffix.lower() not in FOCUSED_EXTENSIONS:
            continue

        try:
            stat = path.stat()
            yield FileTask(
                path=path,
                rel_path=str(path.relative_to(root)),
                ext=path.suffix.lower(),
                kind=detect_file_kind(path),
                size_bytes=stat.st_size,
            )
        except Exception as exc:
            print(f"[WARN] Failed to inspect file: {path} :: {exc}")