# file: export.py
import csv, json
from typing import List, Dict

def to_csv(path: str, rows: List[Dict]):
    # אם אין נתונים – ניצור קובץ ריק עם כותרת מינימלית (או נשאיר ריק)
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            pass
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def to_json(path: str, rows: List[Dict]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
