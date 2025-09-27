import argparse
import sqlite3
from pathlib import Path
from .auth import hash_password
from .db import get_conn

USERS_SQL = '''
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  role TEXT NOT NULL CHECK(role IN ('admin','medical','student')) DEFAULT 'admin',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
'''

DONATIONS_SQL = '''
CREATE TABLE IF NOT EXISTS donations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  pid TEXT NOT NULL,
  blood_type TEXT NOT NULL CHECK(blood_type IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  donated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
'''

AUDIT_SQL = '''
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL DEFAULT (datetime('now')),
  actor TEXT,
  action TEXT NOT NULL,
  entity TEXT,
  entity_id TEXT,
  details_json TEXT
);
'''

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
    "CREATE INDEX IF NOT EXISTS idx_donations_bt ON donations(blood_type);",
    "CREATE INDEX IF NOT EXISTS idx_donations_donatedat ON donations(donated_at);",
    "CREATE INDEX IF NOT EXISTS idx_audit_at ON audit_log(at);"
]

def ensure_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    # Base tables
    cur.execute(USERS_SQL)
    cur.execute(DONATIONS_SQL)
    cur.execute(AUDIT_SQL)

    # Ensure 'at' column exists (handles older DBs created without it)
    cur.execute("PRAGMA table_info(audit_log)")
    rows = cur.fetchall()
    # Row factory returns dicts; fall back to tuple indexing just in case
    cols = [(r["name"] if isinstance(r, dict) and "name" in r else r[1]) for r in rows]
    if "at" not in cols:
        cur.execute("ALTER TABLE audit_log ADD COLUMN at TEXT")
        cur.execute("UPDATE audit_log SET at = datetime('now') WHERE at IS NULL")

    # Indexes
    for stmt in INDEXES:
        cur.execute(stmt)

    conn.commit()

def upsert_admin(conn: sqlite3.Connection, username: str, password: str, first_name: str, last_name: str):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    ph = hash_password(password)
    if row:
        # When using dict row factory, row['id']; if not, row[0]
        user_id = row["id"] if isinstance(row, dict) and "id" in row else row[0]
        cur.execute(
            "UPDATE users SET password_hash=?, first_name=?, last_name=?, role='admin' WHERE id=?",
            (ph, first_name, last_name, user_id)
        )
        print(f"Updated existing admin password for '{username}'.")
    else:
        cur.execute(
            "INSERT INTO users(username, password_hash, first_name, last_name, role) VALUES(?,?,?,?, 'admin')",
            (username, ph, first_name, last_name)
        )
        print(f"Created admin user '{username}'.")
    conn.commit()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="becs.db")
    ap.add_argument("--set-admin", nargs=4, metavar=("USERNAME","PASSWORD","FIRST","LAST"))
    args = ap.parse_args()

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    with get_conn(args.db) as conn:
        ensure_schema(conn)
        if args.set_admin:
            upsert_admin(conn, *args.set_admin)
    print("Migration complete.")

if __name__ == "__main__":
    main()
