"""
seed.py
-------
CSV -> SQLite migration using pandas (CW2 Video 03).

Reads each CSV in DATA/ and loads it into the matching SQLite table with
DataFrame.to_sql(). Also creates two default agent accounts so you can log in
straight away on demo day.

This module is idempotent-ish: call init_database() and it will create tables,
seed default users, and migrate the CSVs only if the tables are empty.
"""

import os
import pandas as pd

from . import db, schema, security

DATA_DIR = db.DATA_DIR

# username, password, full name, role
DEFAULT_USERS = [
    ("admin", "admin123", "System Administrator", "admin"),
    ("sarah.lee", "password1", "Sarah Lee", "supervisor"),
    ("james.okafor", "password1", "James Okafor", "agent"),
    ("priya.nair", "password1", "Priya Nair", "agent"),
    ("tom.becker", "password1", "Tom Becker", "agent"),
]


def _table_is_empty(conn, table) -> bool:
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return cur.fetchone()[0] == 0
    except Exception:
        return True


def seed_default_users(conn):
    """Insert the default agent accounts (hashed passwords) if missing."""
    cur = conn.cursor()
    for username, pw, full_name, role in DEFAULT_USERS:
        cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO users (username, password_hash, full_name, role) "
                "VALUES (?, ?, ?, ?)",
                (username, security.generate_hash(pw), full_name, role),
            )
    conn.commit()


def migrate_csv(conn, csv_name, table_name):
    """Load one CSV file into one SQLite table using pandas."""
    path = os.path.join(DATA_DIR, csv_name)
    if not os.path.exists(path):
        print(f"  ! {csv_name} not found, skipping")
        return 0
    data = pd.read_csv(path)
    data.to_sql(table_name, conn, if_exists="append", index=False)
    return len(data)


# --- named migrations, mirroring the CW2 brief's migrate_cyber_incidents() --
# Each follows the exact pattern taught in Video 03:
#   data = pd.read_csv(...);  data.to_sql(table, conn)
def migrate_customers(conn):
    return migrate_csv(conn, "customers.csv", "customers")


def migrate_tickets(conn):
    return migrate_csv(conn, "tickets.csv", "tickets")


def migrate_conversations(conn):
    return migrate_csv(conn, "conversations.csv", "conversations")


def migrate_canned_responses(conn):
    return migrate_csv(conn, "canned_responses.csv", "canned_responses")


def init_database(force: bool = False):
    """
    One-call setup used by the Streamlit app and the CLI.
    Creates tables, seeds users, and migrates CSVs if the DB is empty.
    """
    conn = db.get_connection()
    if force:
        schema.drop_all_tables(conn)
    schema.create_all_tables(conn)
    seed_default_users(conn)

    migrations = [
        ("customers.csv", "customers"),
        ("tickets.csv", "tickets"),
        ("conversations.csv", "conversations"),
        ("canned_responses.csv", "canned_responses"),
    ]
    for csv_name, table in migrations:
        if force or _table_is_empty(conn, table):
            n = migrate_csv(conn, csv_name, table)
            if n:
                print(f"  migrated {n:>4} rows  {csv_name} -> {table}")
    conn.close()


if __name__ == "__main__":
    print("Initialising HelpHub database...")
    init_database(force=True)
    print("Done. Database ready at:", db.DB_PATH)
