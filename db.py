# file: db.py
import sqlite3
from constants import BLOOD_TYPES, iso_now

class DB:
    def __init__(self, path: str = "blood_bank.db"):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id TEXT NOT NULL,
            donor_name TEXT NOT NULL,
            blood_type TEXT NOT NULL CHECK(blood_type IN ({",".join([repr(bt) for bt in BLOOD_TYPES])})),
            donation_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('available','dispensed','emergency_dispensed')) DEFAULT 'available'
        );
        """)
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS dispensations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blood_type TEXT NOT NULL CHECK(blood_type IN ({",".join([repr(bt) for bt in BLOOD_TYPES])})),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            dispensation_date TEXT NOT NULL,
            mode TEXT NOT NULL CHECK(mode IN ('routine','emergency'))
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_donations_type_status ON donations(blood_type, status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);")
        self.conn.commit()

    # ---- Donations CRUD ----
    def add_donation(self, donor_id: str, donor_name: str, blood_type: str, donation_date_iso: str):
        self.conn.execute("""
            INSERT INTO donations(donor_id, donor_name, blood_type, donation_date, status)
            VALUES (?,?,?,?, 'available');
        """, (donor_id, donor_name, blood_type, donation_date_iso))
        self.conn.commit()

    def count_available(self, blood_type: str) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM donations WHERE blood_type=? AND status='available';", (blood_type,))
        return cur.fetchone()[0]

    def available_ids(self, blood_type: str, limit: int) -> list[int]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id FROM donations
            WHERE blood_type=? AND status='available'
            LIMIT ?;
        """, (blood_type, limit))
        return [r[0] for r in cur.fetchall()]

    def mark_dispensed_ids(self, ids: list[int], mode: str) -> int:
        if not ids:
            return 0
        qmarks = ",".join(["?"] * len(ids))
        status = 'emergency_dispensed' if mode == 'emergency' else 'dispensed'
        self.conn.execute(f"UPDATE donations SET status='{status}' WHERE id IN ({qmarks});", ids)
        self.conn.commit()
        return len(ids)

    # ---- Dispensation log ----
    def log_dispensation(self, blood_type: str, qty: int, mode: str):
        self.conn.execute("""
            INSERT INTO dispensations(blood_type, quantity, dispensation_date, mode)
            VALUES (?,?,?,?);
        """, (blood_type, qty, iso_now(), mode))
        self.conn.commit()

    def close(self):
        self.conn.close()
