from __future__ import annotations

from pathlib import Path
import concurrent.futures
import threading
import logging

from config import DATASET_DIR
from detectors.scanner import detect_pdn, has_personal_data
from extractor.factory import get_extractor
from reports.result_writer import format_mtime, write_result_csv
from scanner.discovery import iter_files
from scanner.types import FileKind


# Подавляем предупреждения от pypdf
logging.getLogger("pypdf").setLevel(logging.ERROR)


OUTPUT_DIR = Path("output")
RESULT_TEXT_CSV = OUTPUT_DIR / "result_text.csv"
RESULT_MEDIA_CSV = OUTPUT_DIR / "result_video.csv"


# Глобальный кэш экстракторов для многопоточной обработки
_extractor_cache = {}
_extractor_cache_lock = threading.Lock()


def get_cached_extractor(kind: FileKind):
    """Получить экстрактор из кэша или создать новый"""
    # Для каждого потока создаем свой экземпляр, чтобы избежать проблем с thread-safety
    thread_id = threading.get_ident()
    cache_key = f"{kind}_{thread_id}"
    
    with _extractor_cache_lock:
        if cache_key not in _extractor_cache:
            _extractor_cache[cache_key] = get_extractor(kind)
        return _extractor_cache[cache_key]


def build_result_row(task) -> dict[str, str]:
    stat = task.path.stat()

    return {
        "size": str(stat.st_size),
        "time": format_mtime(stat.st_mtime),
        "name": task.path.name,
    }


MEDIA_KINDS = {FileKind.IMAGE, FileKind.VIDEO}


def process_single_task(task):
    """Обработка одного файла"""
    try:
        extractor = get_cached_extractor(task.kind)
        extraction = extractor.extract(task.path)
        
        # Пропускаем файлы без текста (но не логируем для обычных случаев)
        if not extraction.text or not extraction.text.strip():
            return None
        
        # Пропускаем пустые шаблоны (файлы с малым количеством текста)
        text_length = len(extraction.text.strip())
        if text_length < 200:  # Слишком маленький текст - скорее всего шаблон
            return None
        
        detection = detect_pdn(
            extraction.text,
            kind=task.kind,
            metadata=extraction.metadata,
        )

        # Требуем надежное обнаружение персональных данных
        if has_personal_data(detection) and _is_real_data_leak(detection, extraction.text):
            row = build_result_row(task)
            if row["size"] and row["time"] and row["name"]:
                return row

    except Exception as exc:
        # Логируем только серьезные ошибки, пропускаем обычные проблемы с файлами
        error_msg = str(exc).lower()
        if not any(skip in error_msg for skip in ['no text', 'binary file', 'file too small', 'cannot read']):
            print(f"[ERROR] Failed to process {task.rel_path}: {type(exc).__name__}: {exc}")
    
    return None


def _is_real_data_leak(detection, text: str) -> bool:
    """Проверка, что это реальная утечка данных, а не шаблон"""
    # Исключаем типичные названия шаблонов и форм
    template_keywords = [
        'анкета', 'форма', 'шаблон', 'образец', 'пример', 'бланк',
        'questionnaire', 'form', 'template', 'sample', 'blank',
        'заполните', 'введите', 'укажите',
        'fill', 'enter', 'specify'
    ]
    
    text_lower = text.lower()
    if any(kw in text_lower for kw in template_keywords):
        return False
    
    # Требуем наличие нескольких типов персональных данных или высокий процент совпадений
    category_count = len(detection.categories)
    
    # Если это одни ФИО без остальных данных - скорее всего не утечка
    if category_count == 1 and 'FIO' in detection.categories:
        return False
    
    # Требуем минимум 2 разных категории или высокое количество совпадений в одной категории
    if category_count >= 2:
        return True
    
    if category_count == 1:
        # Для одной категории требуем достаточно много совпадений
        count = list(detection.categories.values())[0]
        return count >= 5  # Минимум 5 совпадений одного типа данных
    
    return False


def process_tasks_parallel(tasks, output_path: Path, description: str, max_workers: int = 4) -> None:
    print(f"Processing {description}: {len(tasks)} files with {max_workers} workers")

    result_rows: list[dict[str, str]] = []
    processed = 0
    matched = 0
    failed = 0
    
    lock = threading.Lock()

    def update_progress():
        nonlocal processed, matched, failed
        with lock:
            processed += 1
            if processed % 50 == 0:
                print(f"Processed: {processed}/{len(tasks)} | Matched: {matched} | Failed: {failed}")

    def process_and_collect(task):
        result = process_single_task(task)
        update_progress()
        
        if result:
            nonlocal matched
            with lock:
                matched += 1
                result_rows.append(result)
        else:
            nonlocal failed
            with lock:
                failed += 1

    # Используем ThreadPoolExecutor для параллельной обработки
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_and_collect, task) for task in tasks]
        concurrent.futures.wait(futures)

    result_rows.sort(key=lambda x: x["name"].lower())
    write_result_csv(result_rows, output_path)

    print(f"{description} done.")
    print(f"Processed: {processed}")
    print(f"Matched: {matched}")
    print(f"Failed: {failed}")
    print(f"Saved to: {output_path.resolve()}")


def process_tasks(tasks, output_path: Path, description: str) -> None:
    """Обертка для выбора режима обработки"""
    # Для небольшого количества файлов используем последовательную обработку
    if len(tasks) < 20:
        process_tasks_sequential(tasks, output_path, description)
    else:
        # Для большого количества - параллельную (меньше воркеров для стабильности)
        max_workers = min(4, len(tasks) // 20 + 1)  # Адаптивное количество воркеров
        process_tasks_parallel(tasks, output_path, description, max_workers)


def process_tasks_sequential(tasks, output_path: Path, description: str) -> None:
    """Последовательная обработка для небольшого количества файлов"""
    print(f"Processing {description}: {len(tasks)} files sequentially")

    result_rows: list[dict[str, str]] = []
    processed = 0
    matched = 0
    failed = 0

    for task in tasks:
        processed += 1

        try:
            extractor = get_cached_extractor(task.kind)
            extraction = extractor.extract(task.path)
            
            if not extraction.text.strip():
                failed += 1
                continue
            
            detection = detect_pdn(
                extraction.text,
                kind=task.kind,
                metadata=extraction.metadata,
            )

            if has_personal_data(detection) and _is_real_data_leak(detection, extraction.text):
                row = build_result_row(task)
                if row["size"] and row["time"] and row["name"]:
                    result_rows.append(row)
                    matched += 1
                else:
                    failed += 1
            else:
                failed += 1

        except Exception as exc:
            failed += 1
            print(f"[WARN] Failed to process {task.rel_path}: {exc}")

        if processed % 100 == 0:
            print(
                f"Processed: {processed}/{len(tasks)} | "
                f"Matched: {matched} | Failed: {failed}"
            )

    result_rows.sort(key=lambda x: x["name"].lower())
    write_result_csv(result_rows, output_path)

    print(f"{description} done.")
    print(f"Processed: {processed}")
    print(f"Matched: {matched}")
    print(f"Failed: {failed}")
    print(f"Saved to: {output_path.resolve()}")


def merge_results() -> None:
    print("Merging result_text.csv and result_video.csv...")
    
    all_rows = []
    
    for csv_file in [RESULT_TEXT_CSV, RESULT_MEDIA_CSV]:
        if csv_file.exists():
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[1:]
                    all_rows.extend([line.strip() for line in lines if line.strip()])
            except Exception as exc:
                print(f"[WARN] Failed to read {csv_file}: {exc}")
    
    all_rows.sort()
    
    final_csv = OUTPUT_DIR / "result.csv"
    with open(final_csv, 'w', encoding='utf-8') as f:
        f.write("size,time,name\n")
        for row in all_rows:
            f.write(row + "\n")
    
    print(f"Merged {len(all_rows)} entries into {final_csv.resolve()}")


def main() -> None:
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset directory not found: {DATASET_DIR}")

    all_tasks = list(iter_files(DATASET_DIR))
    
    # Фильтруем файлы: пропускаем слишком маленькие (меньше 100 байт)
    tasks = [task for task in all_tasks if task.size_bytes >= 100]
    
    print(f"Total files found: {len(all_tasks)}")
    print(f"Files after filtering: {len(tasks)} (skipped {len(all_tasks) - len(tasks)} small files)")

    text_tasks = [task for task in tasks if task.kind not in MEDIA_KINDS]
    media_tasks = [task for task in tasks if task.kind in MEDIA_KINDS]

    process_tasks(text_tasks, RESULT_TEXT_CSV, "text files")
    process_tasks(media_tasks, RESULT_MEDIA_CSV, "images and video")
    
    merge_results()


if __name__ == "__main__":
    main()
