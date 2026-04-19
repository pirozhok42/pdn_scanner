from __future__ import annotations

from pathlib import Path

from extractor.base import BaseExtractor, ExtractionResult


class TextFallbackExtractor(BaseExtractor):
    def extract(self, path: Path) -> ExtractionResult:
        result = ExtractionResult(file_path=str(path))

        # Проверяем размер файла - слишком маленькие файлы пропускаем
        if path.stat().st_size < 10:
            result.errors.append("File too small")
            return result

        # Проверяем, является ли файл бинарным (содержит null байты)
        try:
            with open(path, "rb") as f:
                sample = f.read(1024)
                if b'\x00' in sample:
                    result.errors.append("Binary file detected")
                    return result
        except Exception:
            result.errors.append("Cannot read file")
            return result

        for encoding in ["utf-8", "utf-8-sig", "cp1251", "latin-1"]:
            try:
                with open(path, "r", encoding=encoding, errors="ignore") as f:
                    text = f.read()
                    if text.strip():  # Проверяем, что есть непустой текст
                        result.text = text
                        result.metadata = {"encoding": encoding}
                        return result
            except Exception:
                pass

        result.errors.append("Text fallback failed - no readable text")
        return result