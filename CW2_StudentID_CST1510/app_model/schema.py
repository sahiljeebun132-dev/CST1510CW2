"""
schema.py
---------
Table creation / DDL (CW2 Video 03).

All tables use CREATE TABLE IF NOT EXISTS so running this repeatedly is safe.
Relationships are expressed with FOREIGN KEY constraints.
"""

from . import users as users_model


def create_all_tables(conn):
    cur = conn.cursor()

    # --- Agents / staff accounts: use the canonical create_user_table (Video 03)
    users_model.create_user_table(conn)

    # --- Customers ----------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id        INTEGER PRIMARY KEY,
            name               TEXT NOT NULL,
            email              TEXT,
            phone              TEXT,
            city               TEXT,
            loyalty_tier       TEXT,
            lifetime_orders    INTEGER,
            lifetime_spend_gbp REAL,
            created_at         TEXT
        );
    """)

    # --- Tickets (one support case) ----------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id          INTEGER PRIMARY KEY,
            customer_id        INTEGER,
            customer_name      TEXT,
            channel            TEXT,
            category           TEXT,
            subject            TEXT,
            order_ref          TEXT,
            product            TEXT,
            priority           TEXT,
            status             TEXT,
            sentiment          TEXT,
            assigned_agent     TEXT,
            sla_target_hours   INTEGER,
            sla_due_at         TEXT,
            first_response_mins INTEGER,
            csat_score         TEXT,
            created_at         TEXT,
            updated_at         TEXT,
            resolved_at        TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        );
    """)

    # --- Conversations (messages inside a ticket - the omnichannel feed) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            message_id      INTEGER PRIMARY KEY,
            ticket_id       INTEGER,
            customer_id     INTEGER,
            channel         TEXT,
            direction       TEXT,    -- Inbound | Outbound | Note
            sender          TEXT,
            body            TEXT,
            sent_at         TEXT,
            is_internal_note INTEGER DEFAULT 0,
            FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id)
        );
    """)

    # --- Canned responses (saved replies / macros) -------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS canned_responses (
            canned_id  INTEGER PRIMARY KEY,
            category   TEXT,
            title      TEXT,
            body       TEXT
        );
    """)

    conn.commit()


def drop_all_tables(conn):
    """Utility for a clean re-seed during development."""
    cur = conn.cursor()
    for t in ("conversations", "tickets", "canned_responses",
              "customers", "users"):
        cur.execute(f"DROP TABLE IF EXISTS {t}")
    conn.commit()
