"""
canned_responses.py
-------------------
Saved replies / macros CRUD (CW2 Video 03). Parameterized.

Bodies may contain {name}, {oid}, {product} placeholders that the UI fills in
from the active ticket before inserting.
"""

import pandas as pd


def get_all(conn) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM canned_responses ORDER BY category, title",
                       conn)


def get_by_category(conn, category) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM canned_responses WHERE category = ? ORDER BY title",
        conn, params=(category,))


def get(conn, canned_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM canned_responses WHERE canned_id = ?",
                (canned_id,))
    return cur.fetchone()


def add(conn, category, title, body):
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(canned_id), 0) + 1 FROM canned_responses")
    new_id = cur.fetchone()[0]
    cur.execute("INSERT INTO canned_responses (canned_id, category, title, body)"
                " VALUES (?, ?, ?, ?)", (new_id, category, title, body))
    conn.commit()
    return new_id


def update(conn, canned_id, category, title, body):
    cur = conn.cursor()
    cur.execute("UPDATE canned_responses SET category = ?, title = ?, body = ? "
                "WHERE canned_id = ?", (category, title, body, canned_id))
    conn.commit()
    return cur.rowcount > 0


def delete(conn, canned_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM canned_responses WHERE canned_id = ?", (canned_id,))
    conn.commit()
    return cur.rowcount > 0


def fill_placeholders(body, *, name="there", oid="your order", product="item"):
    """Replace {name}/{oid}/{product} tokens with ticket context."""
    return (body.replace("{name}", str(name))
                .replace("{oid}", str(oid))
                .replace("{product}", str(product)))
