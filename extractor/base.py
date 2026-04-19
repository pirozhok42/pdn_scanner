from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ExtractionResult:
    file_path: str
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    tables: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BaseExtractor:
    def extract(self, path: Path) -> ExtractionResult:
        raise NotImplementedError