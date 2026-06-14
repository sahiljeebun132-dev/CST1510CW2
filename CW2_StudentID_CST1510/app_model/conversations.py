"""
conversations.py
----------------
Omnichannel message feed inside a ticket (CW2 Video 03). Parameterized CRUD.
"""

from datetime import datetime
import pandas as pd


def get_thread(conn, ticket_id, include_notes=True) -> pd.DataFrame:
    """Return all messages for a ticket in chronological order."""
    sql = "SELECT * FROM conversations WHERE ticket_id = ?"
    params = [ticket_id]
    if not include_notes:
        sql += " AND is_internal_note = 0"
    sql += " ORDER BY sent_at ASC"
    return pd.read_sql(sql, conn, params=params)


def add_message(conn, ticket_id, customer_id, channel, direction, sender,
                body, is_internal_note=0):
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(message_id), 0) + 1 FROM conversations")
    new_id = cur.fetchone()[0]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        """INSERT INTO conversations
           (message_id, ticket_id, customer_id, channel, direction, sender,
            body, sent_at, is_internal_note)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (new_id, ticket_id, customer_id, channel, direction, sender, body,
         now, is_internal_note),
    )
    # touch the parent ticket's updated_at
    cur.execute("UPDATE tickets SET updated_at = ? WHERE ticket_id = ?",
                (now, ticket_id))
    conn.commit()
    return new_id


def reply(conn, ticket, agent_username, body):
    """Convenience: agent replies to the customer on a ticket."""
    return add_message(conn, ticket["ticket_id"], ticket["customer_id"],
                       ticket["channel"], "Outbound", agent_username, body, 0)


def add_note(conn, ticket, agent_username, body):
    """Convenience: internal (agent-only) note."""
    return add_message(conn, ticket["ticket_id"], ticket["customer_id"],
                       "Internal", "Note", agent_username, body, 1)


def delete_message(conn, message_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM conversations WHERE message_id = ?", (message_id,))
    conn.commit()
    return cur.rowcount > 0
