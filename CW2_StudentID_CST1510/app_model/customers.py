"""
customers.py
------------
Customer record queries (CW2 Video 03). Parameterized throughout.
Returns pandas DataFrames where the UI wants tabular data.
"""

import pandas as pd


def get_all_customers(conn) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM customers ORDER BY name", conn)


def get_customer(conn, customer_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    return cur.fetchone()


def search_customers(conn, term) -> pd.DataFrame:
    like = f"%{term}%"
    return pd.read_sql(
        "SELECT * FROM customers "
        "WHERE name LIKE ? OR email LIKE ? OR city LIKE ? "
        "ORDER BY name",
        conn, params=(like, like, like),
    )


def add_customer(conn, name, email, phone, city, tier="Bronze"):
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(customer_id), 0) + 1 FROM customers")
    new_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO customers (customer_id, name, email, phone, city, "
        "loyalty_tier, lifetime_orders, lifetime_spend_gbp, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 0, 0, datetime('now'))",
        (new_id, name, email, phone, city, tier),
    )
    conn.commit()
    return new_id


def update_customer(conn, customer_id, **fields):
    if not fields:
        return False
    cols = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [customer_id]
    cur = conn.cursor()
    cur.execute(f"UPDATE customers SET {cols} WHERE customer_id = ?", params)
    conn.commit()
    return cur.rowcount > 0


def delete_customer(conn, customer_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
    conn.commit()
    return cur.rowcount > 0
