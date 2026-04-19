from __future__ import annotations

from scanner.types import FileKind
from extractor.base import BaseExtractor
from extractor.csv_extractor import CsvExtractor
from extractor.docx_extractor import DocxExtractor
from extractor.html_extractor import HtmlExtractor
from extractor.image_extractor import ImageExtractor
from extractor.json_extractor import JsonExtractor
from extractor.parquet_extractor import ParquetExtractor
from extractor.pdf_extractor import PdfExtractor
from extractor.text_fallback import TextFallbackExtractor
from extractor.video_extractor import VideoExtractor


def get_extractor(kind: FileKind) -> BaseExtractor:
    mapping: dict[FileKind, BaseExtractor] = {
        FileKind.CSV: CsvExtractor(),
        FileKind.JSON: JsonExtractor(),
        FileKind.PARQUET: ParquetExtractor(),
        FileKind.PDF: PdfExtractor(),
        FileKind.DOCX: DocxExtractor(),
        FileKind.HTML: HtmlExtractor(),
        FileKind.IMAGE: ImageExtractor(),
        FileKind.VIDEO: VideoExtractor(frame_step_sec=5, max_frames=15, min_text_length=10),
    }
    return mapping.get(kind, TextFallbackExtractor())