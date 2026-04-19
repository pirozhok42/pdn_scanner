from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from extractor.base import BaseExtractor, ExtractionResult


class HtmlExtractor(BaseExtractor):
    def extract(self, path: Path) -> ExtractionResult:
        result = ExtractionResult(file_path=str(path))

        encodings = ["utf-8", "utf-8-sig", "cp1251", "latin-1"]
        last_error = None

        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding, errors="ignore") as f:
                    html = f.read()

                soup = BeautifulSoup(html, "html.parser")

                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)
                result.text = text
                result.metadata = {"encoding": encoding, "title": soup.title.string.strip() if soup.title and soup.title.string else ""}
                return result
            except Exception as exc:
                last_error = exc

        result.errors.append(f"HTML read failed: {last_error}")
        return result