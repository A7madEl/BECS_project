# file: constants.py
from datetime import datetime

# 8 הסוגים הסטנדרטיים
BLOOD_TYPES = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']

# תאימות: donor -> recipients (מי יכול לתרום למי)
COMPATIBILITY = {
    'O-':  ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'],  # תורם אוניברסלי
    'O+':  ['O+', 'A+', 'B+', 'AB+'],
    'A-':  ['A+', 'A-', 'AB+', 'AB-'],
    'A+':  ['A+', 'AB+'],
    'B-':  ['B+', 'B-', 'AB+', 'AB-'],
    'B+':  ['B+', 'AB+'],
    'AB-': ['AB+', 'AB-'],
    'AB+': ['AB+']  # מקבל אוניברסלי
}

# התפלגות באוכלוסייה (גבוה = פחות נדיר → נעדיף להשתמש בהם קודם כדי לשמור על נדירים)
POPULATION_PERCENT = {
    'O+': 32, 'A+': 34, 'B+': 9,  'AB+': 3,
    'O-': 7,  'A-': 6,  'B-': 2,  'AB-': 1
}

def iso_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_ddmmyyyy_or_iso(s: str) -> str:
    s = (s or "").strip()
    try:
        d = datetime.strptime(s, "%d/%m/%Y")
        return d.strftime("%Y-%m-%d 00:00:00")
    except Exception:
        return iso_now()
