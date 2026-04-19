from __future__ import annotations

from pathlib import Path


OUTPUT_DIR = Path("output")
RESULT_TEXT_CSV = OUTPUT_DIR / "result_text.csv"
RESULT_MEDIA_CSV = OUTPUT_DIR / "result_video.csv"
RESULT_CSV = OUTPUT_DIR / "result.csv"


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
        else:
            print(f"[INFO] File not found: {csv_file}")
    
    all_rows.sort()
    
    with open(RESULT_CSV, 'w', encoding='utf-8') as f:
        f.write("size,time,name\n")
        for row in all_rows:
            f.write(row + "\n")
    
    print(f"Merged {len(all_rows)} entries into {RESULT_CSV.resolve()}")


if __name__ == "__main__":
    merge_results()
