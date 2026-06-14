"""
events.py
---------
Lightweight per-ticket activity log (audit trail).

Every meaningful action on a ticket — status change, reassignment, priority
change, reply, internal note, CSAT — is recorded here so the conversation's
History tab can show a full timeline of how the ticket was handled.

Every function ensures its table exists first, so the History feature is
self-healing and works even if the database was created by an older version.
"""

from datetime import datetime
import pandas as pd

_COLUMNS = ["event_id", "ticket_id", "event_type", "detail", "actor", "created_at"]


def create_events_table(conn):
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS ticket_events (
            event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id  INTEGER,
            event_type TEXT,
            detail     TEXT,
            actor      TEXT,
            created_at TEXT,
            FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id)
        );
    """)
    conn.commit()


def log_event(conn, ticket_id, event_type, detail, actor):
    create_events_table(conn)        # ensure the table exists before writing
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ticket_events (ticket_id, event_type, detail, actor, "
        "created_at) VALUES (?, ?, ?, ?, ?)",
        (ticket_id, event_type, detail, actor,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    return cur.lastrowid


def get_events(conn, ticket_id) -> pd.DataFrame:
    """Return this ticket's events. Self-healing: never raises if the table or
    database is missing/older — returns an empty frame instead."""
    try:
        create_events_table(conn)    # ensure the table exists before reading
        return pd.read_sql(
            "SELECT * FROM ticket_events WHERE ticket_id = ? "
            "ORDER BY created_at ASC, event_id ASC",
            conn, params=(ticket_id,))
    except Exception:
        return pd.DataFrame(columns=_COLUMNS)
