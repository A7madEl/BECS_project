import argparse
from becs.auth import hash_password
from becs.db import get_conn
from becs.migrate_sqlite import ensure_schema

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="../becs.db")
    ap.add_argument("--username", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--first", required=True)
    ap.add_argument("--last", required=True)
    ap.add_argument("--role", choices=["admin","medical","student"], required=True)
    args = ap.parse_args()

    with get_conn(args.db) as conn:
        ensure_schema(conn)
        ph = hash_password(args.password)
        conn.execute(
            "INSERT INTO users(username,password_hash,first_name,last_name,role) VALUES (?,?,?,?,?)",
            (args.username, ph, args.first, args.last, args.role)
        )
        conn.commit()
    print(f"User {args.username} ({args.role}) created.")

if __name__ == "__main__":
    main()
