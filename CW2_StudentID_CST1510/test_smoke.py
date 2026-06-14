"""
test_smoke.py — quick verification of the model layer (no Streamlit needed).
Run:  python test_smoke.py
"""
import os, sys
from app_model import db, seed, security
from app_model import users as U
from app_model import customers as C
from app_model import tickets as T
from app_model import conversations as Conv
from app_model import canned_responses as Can
from app_model import ai_assistant as AI

ok = 0; fail = 0
def check(name, cond):
    global ok, fail
    print(("PASS" if cond else "FAIL"), "-", name)
    ok += cond; fail += (not cond)

# fresh DB
if os.path.exists(db.DB_PATH):
    os.remove(db.DB_PATH)
seed.init_database(force=True)
conn = db.get_connection()

# bcrypt (canonical Video 01 functions)
h = security.generate_hash("Secr3t!")
check("bcrypt valid match", security.is_valid_hash("Secr3t!", h))
check("bcrypt wrong rejected", not security.is_valid_hash("x", h))
check("two hashes differ (salt)", security.generate_hash("a") != security.generate_hash("a"))

# canonical CRUD functions from the brief
check("create_user_table exists", hasattr(U, "create_user_table"))
U.add_user(conn, "canon.user", security.generate_hash("pw"))
check("add_user inserts", U.get_user(conn, "canon.user") is not None)
check("get_all_users returns rows", len(U.get_all_users(conn)) >= 1)
U.update_user(conn, "canon.user", "canon.renamed")
check("update_user renames", U.get_user(conn, "canon.renamed") is not None)
check("delete_user removes", U.delete_user(conn, "canon.renamed"))

# users / auth (friendly helpers)
ok_reg, _ = U.register_user(conn, "test.agent", "pw12345", "Test Agent")
check("register new user", ok_reg)
dup_ok, _ = U.register_user(conn, "test.agent", "pw12345")
check("duplicate username rejected", not dup_ok)
lok, urow, _ = U.login_user(conn, "admin", "admin123")
check("admin login works", lok and urow["role"] == "admin")
check("wrong password fails", not U.login_user(conn, "admin", "nope")[0])

# data migrated
check("customers migrated", len(C.get_all_customers(conn)) == 40)
check("tickets migrated", len(T.get_all_tickets(conn)) == 80)
check("conversations migrated", len(Conv.get_thread(conn, 1)) >= 1)
check("canned migrated", len(Can.get_all(conn)) == 12)

# named pandas migrations exist (brief migrate_* pattern)
check("named migrate_* helpers", all(hasattr(seed, n) for n in
      ("migrate_customers", "migrate_tickets", "migrate_conversations",
       "migrate_canned_responses")))

# ticket CRUD
tid = T.create_ticket(conn, 1, "Test Person", "Email", "Payment",
                      "Test subj", "FA111", "Nike", "High", "admin")
check("create ticket", T.get_ticket(conn, tid) is not None)
check("update status", T.update_status(conn, tid, "Resolved"))
check("status persisted", dict(T.get_ticket(conn, tid))["status"] == "Resolved")
mid = Conv.add_message(conn, tid, 1, "Email", "Outbound", "admin", "hello", 0)
check("add message", mid is not None)
check("filter by status", len(T.filter_tickets(conn, status="Resolved")) >= 1)
check("delete ticket", T.delete_ticket(conn, tid))

# stats + charts
s = T.stats(conn)
check("stats has totals", s["total"] >= 80)
check("count_by status", not T.count_by(conn, "status").empty)

# AI offline
reply, mode = AI.answer(conn, "give me a summary of today")
check("AI offline answers", mode == "offline" and len(reply) > 10)
reply2, _ = AI.answer(conn, "are we breaching sla?")
check("AI SLA intent", "SLA" in reply2 or "sla" in reply2.lower())

print(f"\n{ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
