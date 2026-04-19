from __future__ import annotations

from pathlib import Path
import threading
import numpy as np
import cv2

from PIL import Image

from extractor.base import BaseExtractor, ExtractionResult


class ImageExtractor(BaseExtractor):
    _reader = None
    _reader_lock = threading.Lock()

    @classmethod
    def _get_reader(cls):
        with cls._reader_lock:
            if cls._reader is None:
                import easyocr
                try:
                    import torch
                    gpu_available = torch.cuda.is_available()
                except Exception:
                    gpu_available = False

                try:
                    cls._reader = easyocr.Reader(["ru", "en"], gpu=gpu_available)
                except Exception:
                    cls._reader = easyocr.Reader(["ru", "en"], gpu=False)
        return cls._reader

    def _preprocess_image(self, img_cv: np.ndarray) -> np.ndarray:
        """Предобработка изображения для лучшего распознавания текста"""
        if img_cv is None or img_cv.size == 0:
            return img_cv

        # Конвертация в grayscale
        if len(img_cv.shape) == 3:
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_cv

        # Увеличение контраста
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Увеличение размера для мелкого текста
        height, width = enhanced.shape
        if height < 300 or width < 300:
            scale_factor = max(300 / height, 300 / width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

        # Шумоподавление
        enhanced = cv2.medianBlur(enhanced, 3)

        return enhanced

    def extract(self, path: Path) -> ExtractionResult:
        result = ExtractionResult(file_path=str(path))

        try:
            # Сначала проверяем через PIL
            with Image.open(path) as img:
                result.metadata["image_size"] = img.size
                result.metadata["image_mode"] = img.mode
                result.metadata["image_format"] = img.format

                # Проверяем на пустое изображение
                if img.size[0] < 10 or img.size[1] < 10:
                    result.errors.append("Image too small")
                    return result

        except Exception as exc:
            result.errors.append(f"Image open failed: {exc}")
            return result

        try:
            # Читаем через numpy для обработки
            img_array = np.fromfile(str(path), np.uint8)
            img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img_cv is None:
                result.errors.append("Failed to decode image")
                return result

            # Предобработка
            processed = self._preprocess_image(img_cv)

            # OCR
            reader = self._get_reader()
            ocr_lines = reader.readtext(processed, detail=0, paragraph=True)

            result.text = "\n".join(ocr_lines)
            result.metadata["ocr_lines"] = len(ocr_lines)

            return result

        except Exception as exc:
            result.errors.append(f"Image OCR failed: {exc}")
            return result