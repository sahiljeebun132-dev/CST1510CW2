"""
tickets.py
----------
Support-ticket CRUD and analytics queries (CW2 Video 03).

This is the heart of the customer-service platform: each ticket is one case.
All writes are parameterized. Read helpers return pandas DataFrames so the
Streamlit dashboard can chart them directly.
"""

from datetime import datetime
import pandas as pd

STATUSES = ["Open", "Pending", "On Hold", "Resolved", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]
CATEGORIES = ["Order Status", "Returns & Refunds", "Delivery Issue",
              "Sizing & Fit", "Faulty Item", "Payment", "Account",
              "Promo / Discount", "Product Question", "Complaint"]
CHANNELS = ["Email", "Live Chat", "WhatsApp", "Instagram DM", "X / Twitter",
            "Facebook", "Phone", "SMS"]
SLA_BY_PRIORITY = {"Urgent": 2, "High": 4, "Medium": 12, "Low": 24}


# ------------------------------------------------------------------ READ ----
def get_all_tickets(conn) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM tickets ORDER BY created_at DESC", conn)


def get_ticket(conn, ticket_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    return cur.fetchone()


def filter_tickets(conn, status=None, priority=None, category=None,
                   channel=None, agent=None, search=None) -> pd.DataFrame:
    """Flexible inbox filter. Builds a parameterized WHERE clause safely."""
    clauses, params = [], []
    if status and status != "All":
        clauses.append("status = ?"); params.append(status)
    if priority and priority != "All":
        clauses.append("priority = ?"); params.append(priority)
    if category and category != "All":
        clauses.append("category = ?"); params.append(category)
    if channel and channel != "All":
        clauses.append("channel = ?"); params.append(channel)
    if agent and agent != "All":
        clauses.append("assigned_agent = ?"); params.append(agent)
    if search:
        like = f"%{search}%"
        clauses.append("(subject LIKE ? OR customer_name LIKE ? "
                       "OR order_ref LIKE ?)")
        params += [like, like, like]
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM tickets{where} ORDER BY created_at DESC"
    return pd.read_sql(sql, conn, params=params)


def tickets_for_customer(conn, customer_id) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM tickets WHERE customer_id = ? ORDER BY created_at DESC",
        conn, params=(customer_id,))


# ---------------------------------------------------------------- CREATE ----
def create_ticket(conn, customer_id, customer_name, channel, category,
                  subject, order_ref, product, priority, agent):
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(ticket_id), 0) + 1 FROM tickets")
    new_id = cur.fetchone()[0]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sla_hours = SLA_BY_PRIORITY.get(priority, 12)
    cur.execute(
        """INSERT INTO tickets
           (ticket_id, customer_id, customer_name, channel, category, subject,
            order_ref, product, priority, status, sentiment, assigned_agent,
            sla_target_hours, sla_due_at, first_response_mins, csat_score,
            created_at, updated_at, resolved_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', 'Neutral', ?, ?,
                   datetime('now', ?), NULL, '', ?, ?, '')""",
        (new_id, customer_id, customer_name, channel, category, subject,
         order_ref, product, priority, agent, sla_hours,
         f"+{sla_hours} hours", now, now),
    )
    conn.commit()
    return new_id


# ---------------------------------------------------------------- UPDATE ----
def update_status(conn, ticket_id, status):
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resolved = now if status in ("Resolved", "Closed") else ""
    cur.execute(
        "UPDATE tickets SET status = ?, updated_at = ?, resolved_at = ? "
        "WHERE ticket_id = ?",
        (status, now, resolved, ticket_id))
    conn.commit()
    return cur.rowcount > 0


def assign_ticket(conn, ticket_id, agent):
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET assigned_agent = ?, "
                "updated_at = datetime('now') WHERE ticket_id = ?",
                (agent, ticket_id))
    conn.commit()
    return cur.rowcount > 0


def set_priority(conn, ticket_id, priority):
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET priority = ?, "
                "updated_at = datetime('now') WHERE ticket_id = ?",
                (priority, ticket_id))
    conn.commit()
    return cur.rowcount > 0


def set_csat(conn, ticket_id, score):
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET csat_score = ? WHERE ticket_id = ?",
                (str(score), ticket_id))
    conn.commit()
    return cur.rowcount > 0


# ---------------------------------------------------------------- DELETE ----
def delete_ticket(conn, ticket_id):
    """Delete a ticket and all of its conversation messages (cascade)."""
    cur = conn.cursor()
    cur.execute("DELETE FROM conversations WHERE ticket_id = ?", (ticket_id,))
    cur.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))
    conn.commit()
    return cur.rowcount > 0


# -------------------------------------------------------------- ANALYTICS ---
def stats(conn) -> dict:
    """Headline numbers for the dashboard KPI cards."""
    df = get_all_tickets(conn)
    open_states = ("Open", "Pending", "On Hold")
    total = len(df)
    open_count = int(df["status"].isin(open_states).sum()) if total else 0
    resolved = int(df["status"].isin(("Resolved", "Closed")).sum()) if total else 0

    # SLA breaches: open tickets whose sla_due_at is in the past
    breaches = 0
    if total:
        now = datetime.now()
        for _, r in df[df["status"].isin(open_states)].iterrows():
            try:
                due = datetime.strptime(r["sla_due_at"], "%Y-%m-%d %H:%M:%S")
                if due < now:
                    breaches += 1
            except (ValueError, TypeError):
                pass

    csat_vals = pd.to_numeric(df["csat_score"], errors="coerce").dropna()
    avg_csat = round(csat_vals.mean(), 2) if len(csat_vals) else None
    frt = pd.to_numeric(df["first_response_mins"], errors="coerce").dropna()
    avg_frt = round(frt.mean(), 1) if len(frt) else None

    return {
        "total": total,
        "open": open_count,
        "resolved": resolved,
        "sla_breaches": breaches,
        "avg_csat": avg_csat,
        "avg_first_response_mins": avg_frt,
        "resolution_rate": round(100 * resolved / total, 1) if total else 0,
    }


def count_by(conn, column) -> pd.DataFrame:
    """Group-by count for charts (status, channel, category, priority...)."""
    df = get_all_tickets(conn)
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=[column, "count"])
    out = df.groupby(column).size().reset_index(name="count")
    return out.sort_values("count", ascending=False)
