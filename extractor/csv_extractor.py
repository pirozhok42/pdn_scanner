from __future__ import annotations

from pathlib import Path

import pandas as pd

from extractor.base import BaseExtractor, ExtractionResult


class CsvExtractor(BaseExtractor):
    def extract(self, path: Path) -> ExtractionResult:
        result = ExtractionResult(file_path=str(path))

        encodings = ["utf-8", "utf-8-sig", "cp1251", "latin-1"]
        sep_candidates = [",", ";", "\t", "|"]

        last_error = None

        for encoding in encodings:
            for sep in sep_candidates:
                try:
                    df = pd.read_csv(path, encoding=encoding, sep=sep, dtype=str, nrows=5000)
                    df = df.fillna("")
                    result.metadata = {
                        "rows": int(df.shape[0]),
                        "cols": int(df.shape[1]),
                        "columns": list(map(str, df.columns.tolist())),
                        "encoding": encoding,
                        "separator": sep,
                    }

                    pieces = []
                    pieces.append("COLUMNS: " + " | ".join(map(str, df.columns.tolist())))

                    for _, row in df.head(300).iterrows():
                        pieces.append(" | ".join(map(str, row.tolist())))

                    result.text = "\n".join(pieces)
                    return result
                except Exception as exc:
                    last_error = exc

        result.errors.append(f"CSV read failed: {last_error}")
        return result