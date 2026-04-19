from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from extractor.base import BaseExtractor, ExtractionResult


def flatten_json(obj: Any, prefix: str = "") -> list[str]:
    lines: list[str] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else str(k)
            lines.extend(flatten_json(v, new_prefix))
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:300]):
            new_prefix = f"{prefix}[{i}]"
            lines.extend(flatten_json(item, new_prefix))
    else:
        lines.append(f"{prefix}: {obj}")

    return lines


def collect_json_keys(obj: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else str(k)
            keys.append(full_key)
            keys.extend(collect_json_keys(v, full_key))
    elif isinstance(obj, list):
        for item in obj[:300]:
            keys.extend(collect_json_keys(item, prefix))

    return keys


class JsonExtractor(BaseExtractor):
    def extract(self, path: Path) -> ExtractionResult:
        result = ExtractionResult(file_path=str(path))

        encodings = ["utf-8", "utf-8-sig", "cp1251", "latin-1"]
        last_error = None

        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    data = json.load(f)

                flat_lines = flatten_json(data)
                result.text = "\n".join(flat_lines[:10000])
                result.metadata = {
                    "encoding": encoding,
                    "top_type": type(data).name,
                    "json_keys": collect_json_keys(data),
                }
                return result
            except Exception as exc:
                last_error = exc

        result.errors.append(f"JSON read failed: {last_error}")
        return result