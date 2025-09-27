from typing import Dict, List, Tuple, Optional
from datetime import datetime
import sqlite3, json
from .db import tx

# Recipient -> ordered compatible donor list (most-preferred first)
COMPATIBILITY: Dict[str, List[str]] = {
    "O-":  ["O-"],
    "O+":  ["O+", "O-"],
    "A-":  ["A-", "O-"],
    "A+":  ["A+", "O+", "A-", "O-"],
    "B-":  ["B-", "O-"],
    "B+":  ["B+", "O+", "B-", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
    "AB+": ["AB+", "A+", "B+", "O+", "AB-", "A-", "B-", "O-"],
}
ALL_TYPES = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]

# Approximate population distribution weights (smaller = rarer, preferred to preserve)
RARITY_WEIGHTS: Dict[str, int] = {
    "O-":  6,  "O+": 37,
    "A-":  6,  "A+": 34,
    "B-":  2,  "B+":  9,
    "AB-": 1,  "AB+": 5,
}

def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")

def log_action(conn: sqlite3.Connection, actor: str, action: str,
               entity: str, entity_id: Optional[str], details: dict) -> None:
    """
    Store audit details as plain JSON text (avoid relying on SQLite json() func).
    """
    conn.execute(
        "INSERT INTO audit_log(at, actor, action, entity, entity_id, details_json) VALUES(?,?,?,?,?,?)",
        (_now_iso(), actor, action, entity, entity_id, json.dumps(details, ensure_ascii=False))
    )

def add_donor(conn: sqlite3.Connection, first_name: str, last_name: str, pid: str,
              blood_type: str, donated_at: Optional[str] = None, actor: str = "system") -> int:
    if blood_type not in ALL_TYPES:
        raise ValueError(f"Invalid blood type: {blood_type}")
    donated_at = donated_at or _now_iso()
    with tx(conn):
        cur = conn.execute(
            "INSERT INTO donations(first_name,last_name,pid,blood_type,donated_at) VALUES(?,?,?,?,?)",
            (first_name, last_name, pid, blood_type, donated_at)
        )
        did = cur.lastrowid
        log_action(conn, actor, "Insert Donation", "donations", str(did), {
            "first_name": first_name, "last_name": last_name, "pid": pid,
            "blood_type": blood_type, "donated_at": donated_at
        })
        return did

def get_counts_by_type(conn: sqlite3.Connection) -> Dict[str, int]:
    counts = {bt: 0 for bt in ALL_TYPES}
    for row in conn.execute("SELECT blood_type, COUNT(*) as c FROM donations GROUP BY blood_type"):
        counts[row["blood_type"]] = row["c"]
    return counts

def check_inventory(conn: sqlite3.Connection, recipient_bt: str) -> List[Tuple[str, int]]:
    if recipient_bt not in COMPATIBILITY:
        raise ValueError(f"Invalid recipient type: {recipient_bt}")
    result: List[Tuple[str, int]] = []
    for bt in COMPATIBILITY[recipient_bt]:
        row = conn.execute("SELECT COUNT(*) AS c FROM donations WHERE blood_type = ?", (bt,)).fetchone()
        result.append((bt, row["c"]))
    return result

def _pop_one(conn: sqlite3.Connection, bt: str) -> Optional[int]:
    row = conn.execute(
        "SELECT id FROM donations WHERE blood_type = ? ORDER BY donated_at ASC, id ASC LIMIT 1",
        (bt,)
    ).fetchone()
    if not row:
        return None
    conn.execute("DELETE FROM donations WHERE id = ?", (row["id"],))
    return row["id"]

def extract_emergency_o_neg(conn: sqlite3.Connection, units: int = 1, actor: str = "system") -> int:
    extracted = 0
    with tx(conn):
        for _ in range(units):
            did = _pop_one(conn, "O-")
            if did is None:
                break
            extracted += 1
            log_action(conn, actor, "Emergency Extract", "donations", str(did), {"blood_type": "O-"})
    return extracted

def extract_surgery(conn: sqlite3.Connection, recipient_bt: str, units: int, actor: str = "system") -> Dict[str, int]:
    if recipient_bt not in COMPATIBILITY:
        raise ValueError(f"Invalid recipient type: {recipient_bt}")
    remaining = units
    per_type: Dict[str, int] = {}
    with tx(conn):
        for donor_bt in COMPATIBILITY[recipient_bt]:
            while remaining > 0:
                did = _pop_one(conn, donor_bt)
                if did is None:
                    break
                per_type[donor_bt] = per_type.get(donor_bt, 0) + 1
                remaining -= 1
                log_action(conn, actor, "Surgery Extract", "donations", str(did), {
                    "recipient": recipient_bt, "donor_type": donor_bt
                })
            if remaining == 0:
                break
        if remaining > 0:
            log_action(conn, actor, "Surgery Shortfall", "donations", None, {
                "recipient": recipient_bt, "requested": units,
                "fulfilled": units - remaining, "shortfall": remaining
            })
    return per_type

def suggest_alternative(conn: sqlite3.Connection, recipient_bt: str) -> Optional[str]:
    """
    Return a rarity-aware compatible alternative when the exact recipient type is out of stock.
    - If requested type has stock -> None (no suggestion needed).
    - Otherwise pick among compatible types with stock > 0, preferring rarer blood types
      (smaller RARITY_WEIGHTS). Tie-break by compatibility priority order.
    """
    if recipient_bt not in COMPATIBILITY:
        return None
    # Build counts for all compatible types
    counts: Dict[str, int] = {}
    for bt in COMPATIBILITY[recipient_bt]:
        row = conn.execute("SELECT COUNT(*) AS c FROM donations WHERE blood_type = ?", (bt,)).fetchone()
        counts[bt] = row["c"]

    if counts.get(recipient_bt, 0) > 0:
        return None  # exact is available

    candidates = [bt for bt, c in counts.items() if c > 0]
    if not candidates:
        return None

    # Sort: rarer first (smaller weight), then original compatibility order
    candidates.sort(key=lambda bt: (RARITY_WEIGHTS.get(bt, 100),
                                    COMPATIBILITY[recipient_bt].index(bt)))
    return candidates[0]
