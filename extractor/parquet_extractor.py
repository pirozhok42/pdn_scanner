from __future__ import annotations

from pathlib import Path

import pandas as pd

from extractor.base import BaseExtractor, ExtractionResult


class ParquetExtractor(BaseExtractor):
    def extract(self, path: Path) -> ExtractionResult:
        result = ExtractionResult(file_path=str(path))

        try:
            df = pd.read_parquet(path)
            df = df.fillna("").astype(str)

            result.metadata = {
                "rows": int(df.shape[0]),
                "cols": int(df.shape[1]),
                "columns": list(map(str, df.columns.tolist())),
            }

            pieces = []
            pieces.append("COLUMNS: " + " | ".join(map(str, df.columns.tolist())))
            for _, row in df.head(300).iterrows():
                pieces.append(" | ".join(map(str, row.tolist())))

            result.text = "\n".join(pieces)
            return result
        except Exception as exc:
            result.errors.append(f"Parquet read failed: {exc}")
            return result