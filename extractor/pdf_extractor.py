from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

from extractor.base import BaseExtractor, ExtractionResult


class PdfExtractor(BaseExtractor):
    def extract(self, path: Path) -> ExtractionResult:
        result = ExtractionResult(file_path=str(path))

        try:
            with open(path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF'):
                    result.errors.append("PDF read skipped: invalid PDF header")
                    result.text = self._fallback_text(path)
                    result.metadata = {"fallback": "non-pdf content"}
                    return result
                f.seek(0)
                reader = PdfReader(f)

                pages_text = []
                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text() or ""
                        if text.strip():
                            pages_text.append(f"[PAGE {i + 1}]\n{text}")
                    except Exception as exc:
                        result.errors.append(f"PDF page {i + 1} failed: {exc}")

                result.text = "\n\n".join(pages_text)
                result.metadata = {
                    "pages": len(reader.pages),
                }
            return result
        except Exception as exc:
            result.errors.append(f"PDF read failed: {exc}")
            return result

    def _fallback_text(self, path: Path) -> str:
        for encoding in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
            try:
                with open(path, "r", encoding=encoding, errors="ignore") as f:
                    data = f.read()
                if "<html" in data.lower() or "<!doctype" in data.lower():
                    soup = BeautifulSoup(data, "html.parser")
                    for tag in soup(["script", "style", "noscript"]):
                        tag.decompose()
                    return soup.get_text(separator="\n", strip=True)
                return data
            except Exception:
                continue
        return ""
