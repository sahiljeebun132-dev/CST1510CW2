"""
users.py
--------
Agent account CRUD + register / login logic (CW2 Videos 02, 03, 07).

This module keeps the EXACT canonical functions taught in the video series
(create_user_table, add_user, get_all_users, get_user, update_user,
delete_user) and layers friendlier helpers on top (register_user, login_user,
update_password, update_role) used by the Streamlit app.

Security: every query uses ? placeholders (parameterized) to prevent SQL
injection, and passwords are hashed with bcrypt — plain text never touches the
database.
"""

from . import security


# ===========================================================================
#  Canonical CRUD — exactly as taught in CW2 Video 03
# ===========================================================================
def create_user_table(conn):
    cur = conn.cursor()
    # Core columns (id, username, password_hash, role) are exactly as in the
    # CW2 brief; full_name and created_at are small additions used by the UI.
    sql = '''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        full_name TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );'''
    cur.execute(sql)
    conn.commit()


def add_user(conn, name, hash):
    cur = conn.cursor()
    sql = 'INSERT INTO users (username, password_hash) VALUES (?, ?)'
    cur.execute(sql, (name, hash))
    conn.commit()


def get_all_users(conn):
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    return cur.fetchall()


def get_user(conn, name):
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username = ?', (name,))
    return cur.fetchone()


def update_user(conn, old_name, new_name):
    cur = conn.cursor()
    cur.execute('UPDATE users SET username = ? WHERE username = ?',
                (new_name, old_name))
    conn.commit()


def delete_user(conn, user_name):
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE username = ?', (user_name,))
    conn.commit()
    return cur.rowcount > 0


# ===========================================================================
#  Friendly helpers built on top of the canonical functions
# ===========================================================================
def register_user(conn, username, password, full_name="", role="agent"):
    """
    Create a new agent account. Returns (ok: bool, message: str).
    Wraps the canonical add_user() with validation, hashing and extra fields.
    """
    username = (username or "").strip()
    if not username or not password:
        return False, "Username and password are required."
    if get_user(conn, username) is not None:
        return False, f"Username '{username}' is already taken."

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, full_name, role) "
        "VALUES (?, ?, ?, ?)",
        (username, security.generate_hash(password), full_name, role),
    )
    conn.commit()
    return True, f"Account '{username}' created. You can now log in."


def login_user(conn, username, password):
    """
    Authenticate against the stored bcrypt hash.
    Returns (ok: bool, user_row_or_None, message).
    """
    user = get_user(conn, username)
    if user is None:
        return False, None, "No account with that username."
    if security.is_valid_hash(password, user["password_hash"]):
        return True, user, "Login successful."
    return False, None, "Incorrect password."


def update_password(conn, username, new_password):
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (security.generate_hash(new_password), username),
    )
    conn.commit()
    return cur.rowcount > 0


def update_role(conn, username, new_role):
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = ? WHERE username = ?",
                (new_role, username))
    conn.commit()
    return cur.rowcount > 0
