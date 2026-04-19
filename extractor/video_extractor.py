from __future__ import annotations

from pathlib import Path
import tempfile
import time
import numpy as np

import cv2

from extractor.base import BaseExtractor, ExtractionResult
from extractor.image_extractor import ImageExtractor


class VideoExtractor(BaseExtractor):
    def __init__(self, frame_step_sec: int = 5, max_frames: int = 15, min_text_length: int = 10):
        self.frame_step_sec = frame_step_sec
        self.max_frames = max_frames
        self.min_text_length = min_text_length
        self.image_extractor = ImageExtractor()

    def init(self, frame_step_sec: int = 3, max_frames: int = 20):
        """Legacy method for compatibility"""
        self.frame_step_sec = frame_step_sec
        self.max_frames = max_frames
        self.min_text_length = 10
        self.image_extractor = ImageExtractor()

    def extract(self, path: Path) -> ExtractionResult:
        result = ExtractionResult(file_path=str(path))
        start_time = time.time()

        # Use resolve() to get absolute path with proper encoding
        abs_path = path.resolve()
        cap = cv2.VideoCapture(str(abs_path))
        if not cap.isOpened():
            result.errors.append("Video open failed")
            return result

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            result.metadata.update({
                "fps": fps,
                "total_frames": total_frames,
                "duration_sec": duration,
                "codec": cap.get(cv2.CAP_PROP_FOURCC),
            })

            # Оптимизируем интервал кадров
            frame_interval = max(int(fps * self.frame_step_sec), 1)

            # Распределяем кадры равномерно по видео
            if total_frames > 0 and self.max_frames > 0:
                step = max(total_frames // self.max_frames, frame_interval)
                frame_positions = list(range(0, total_frames, step))[:self.max_frames]
            else:
                frame_positions = []

            texts = []
            processed_frames = 0

            with tempfile.TemporaryDirectory() as tmpdir:
                for frame_pos in frame_positions:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                    ok, frame = cap.read()
                    if not ok:
                        continue

                    # Проверяем качество кадра
                    if self._is_good_frame(frame):
                        frame_path = Path(tmpdir) / f"frame_{processed_frames:04d}.jpg"
                        cv2.imwrite(str(frame_path), frame)

                        sub_result = self.image_extractor.extract(frame_path)
                        if sub_result.text and len(sub_result.text.strip()) >= self.min_text_length:
                            timestamp = frame_pos / fps if fps > 0 else frame_pos
                            texts.append(f"[FRAME {processed_frames} - {timestamp:.1f}s]\n{sub_result.text}")

                        processed_frames += 1

                        # Прогресс
                        if processed_frames % 5 == 0:
                            print(f"  Processed {processed_frames}/{len(frame_positions)} frames")

            result.text = "\n\n".join(texts)
            result.metadata.update({
                "frames_processed": processed_frames,
                "processing_time_sec": time.time() - start_time,
            })

        finally:
            cap.release()

        return result

    def _is_good_frame(self, frame: np.ndarray) -> bool:
        """Проверяет, является ли кадр подходящим для OCR"""
        if frame is None or frame.size == 0:
            return False

        # Проверяем на слишком темный кадр
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = cv2.mean(gray)[0]
        if mean_brightness < 30:  # слишком темный
            return False

        # Проверяем на размытость (простая метрика)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 100:  # слишком размытый
            return False

        return True