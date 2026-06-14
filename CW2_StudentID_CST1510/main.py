"""
HelpHub — Omnichannel Customer Service Platform
===============================================
CST1510 Coursework 2 — Streamlit entry point (controller / view layer).

A Gnatta-style contact-centre workspace: one shared inbox across email, chat,
social, phone and SMS; ticket queue with SLA timers; customer profiles; canned
replies; an agent dashboard with charts; and an AI co-pilot.

Run:
    pip install -r requirements.txt
    streamlit run main.py

Demo logins (created automatically on first run):
    admin / admin123                (admin)
    sarah.lee / password1           (supervisor)
    james.okafor / password1        (agent)
"""

from datetime import datetime

import streamlit as st
import pandas as pd

from app_model import db, seed, security
from app_model import users as users_model
from app_model import customers as customers_model
from app_model import tickets as tickets_model
from app_model import conversations as conv_model
from app_model import canned_responses as canned_model
from app_model import ai_assistant

APP_NAME = "HelpHub"
DT_FMT = "%Y-%m-%d %H:%M:%S"

st.set_page_config(page_title=f"{APP_NAME} — Customer Service",
                   page_icon="🎧", layout="wide",
                   initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------
# Global styling — clean, modern, smooth
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1300px;}

/* sidebar */
section[data-testid="stSidebar"] {background: #0f172a;}
section[data-testid="stSidebar"] * {color: #e2e8f0;}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  display:flex;align-items:center;padding:9px 12px;margin:2px 0;border-radius:10px;
  cursor:pointer;transition:.15s;font-weight:500;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:#1e293b;}
section[data-testid="stSidebar"] div[role="radiogroup"] input{display:none;}

/* KPI cards */
.kpi{background:#fff;border:1px solid #eceef2;border-radius:16px;padding:18px 20px;
     box-shadow:0 1px 2px rgba(16,24,40,.04);}
.kpi h3{margin:0;font-size:.72rem;color:#667085;font-weight:600;text-transform:uppercase;
        letter-spacing:.05em;}
.kpi .v{font-size:1.85rem;font-weight:700;margin-top:4px;color:#101828;line-height:1.1;}
.kpi .s{font-size:.74rem;color:#98a2b3;margin-top:2px;}

/* pills */
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.72rem;
      font-weight:600;line-height:1.5;}

/* ticket list card */
.tcard{border:1px solid #eceef2;border-radius:12px;padding:10px 12px;margin-bottom:4px;
       background:#fff;}
.tcard.sel{border-color:#6366f1;box-shadow:0 0 0 2px #e0e7ff;}
.tcard .subj{font-weight:600;color:#101828;font-size:.92rem;}
.tcard .meta{color:#667085;font-size:.78rem;margin-top:2px;}

/* chat bubbles */
.bubble-in{background:#f2f4f7;border-radius:14px 14px 14px 4px;padding:10px 14px;
           margin:6px 0;max-width:80%;}
.bubble-out{background:#dcfce7;border-radius:14px 14px 4px 14px;padding:10px 14px;
            margin:6px 0 6px auto;max-width:80%;}
.bubble-note{background:#fef9c3;border-left:3px solid #eab308;border-radius:10px;
             padding:9px 13px;margin:6px 0;font-style:italic;}
.stamp{color:#98a2b3;font-size:.72rem;margin-top:3px;}
.small{color:#667085;font-size:.8rem;}
h2{font-weight:700 !important;color:#101828;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PRIORITY_COLORS = {"Urgent": "#fee2e2;color:#b42318", "High": "#fff1e6;color:#c4320a",
                   "Medium": "#fef7c3;color:#a15c07", "Low": "#dcfae6;color:#067647"}
STATUS_COLORS = {"Open": "#eff4ff;color:#2563eb", "Pending": "#fef7c3;color:#a15c07",
                 "On Hold": "#f4f3ff;color:#6938ef", "Resolved": "#dcfae6;color:#067647",
                 "Closed": "#f2f4f7;color:#475467"}
CHANNEL_ICONS = {"Email": "✉️", "Live Chat": "💬", "WhatsApp": "🟢",
                 "Instagram DM": "📷", "X / Twitter": "𝕏", "Facebook": "📘",
                 "Phone": "📞", "SMS": "📱", "Internal": "🗒️"}


def pill(text, palette):
    color = palette.get(text, "#f2f4f7;color:#475467")
    return f"<span class='pill' style='background:{color}'>{text}</span>"


def fmt_duration(mins):
    mins = int(abs(mins))
    if mins < 60:
        return f"{mins}m"
    if mins < 1440:
        return f"{mins // 60}h {mins % 60}m"
    return f"{mins // 1440}d {(mins % 1440) // 60}h"


def sla_badge(due_str, status):
    """Return (text, css) for an SLA countdown / breach badge."""
    if status in ("Resolved", "Closed"):
        return "✓ Closed", "#f2f4f7;color:#475467"
    try:
        due = datetime.strptime(str(due_str), DT_FMT)
    except (ValueError, TypeError):
        return "—", "#f2f4f7;color:#475467"
    mins = (due - datetime.now()).total_seconds() / 60
    if mins < 0:
        return f"⚠ Overdue {fmt_duration(mins)}", "#fee2e2;color:#b42318"
    if mins < 60:
        return f"⏱ {fmt_duration(mins)} left", "#fff1e6;color:#c4320a"
    return f"⏱ {fmt_duration(mins)} left", "#dcfae6;color:#067647"


def avatar(name):
    initials = "".join([p[0] for p in str(name).split()[:2]]).upper() or "?"
    return (f"<div style='width:34px;height:34px;border-radius:50%;background:#6366f1;"
            f"color:#fff;display:flex;align-items:center;justify-content:center;"
            f"font-weight:700;font-size:.8rem'>{initials}</div>")


# ---------------------------------------------------------------------------
# DB connection + one-time init
# ---------------------------------------------------------------------------
@st.cache_resource
def get_db():
    seed.init_database()
    return db.get_connection()


conn = get_db()

for key, val in {"logged_in": False, "username": None, "role": None,
                 "full_name": None, "page": "Dashboard",
                 "active_ticket": None, "ai_history": []}.items():
    st.session_state.setdefault(key, val)


# ===========================================================================
#  AUTH  (Videos 02/07 login+register, Video 06 session state)
# ===========================================================================
def auth_screen():
    st.write("")
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown(
            "<div style='font-size:2.6rem;font-weight:700;color:#101828'>"
            "🎧 HelpHub</div>"
            "<div style='font-size:1.25rem;color:#475467;font-weight:500;"
            "margin-top:4px'>The friendly omnichannel help desk</div>",
            unsafe_allow_html=True)
        st.write("")
        st.markdown(
            "<div class='small' style='font-size:.95rem;line-height:1.9'>"
            "One shared inbox for <b>email, live chat, WhatsApp, Instagram, X, "
            "Facebook, phone and SMS</b> — with SLA timers, customer profiles, "
            "canned replies, an analytics dashboard and an AI co-pilot.</div>",
            unsafe_allow_html=True)
        st.write("")
        st.info("**Demo logins**\n\n"
                "• `admin` / `admin123` — admin\n\n"
                "• `sarah.lee` / `password1` — supervisor\n\n"
                "• `james.okafor` / `password1` — agent")

    with right:
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["🔐  Log in", "✍️  Register"])
            with tab_login:
                with st.form("login_form"):
                    u = st.text_input("Username", placeholder="admin")
                    p = st.text_input("Password", type="password",
                                      placeholder="••••••••")
                    if st.form_submit_button("Log in", use_container_width=True,
                                             type="primary"):
                        ok, user, msg = users_model.login_user(conn, u, p)
                        if ok:
                            st.session_state.update(
                                logged_in=True, username=user["username"],
                                role=user["role"],
                                full_name=user["full_name"] or user["username"],
                                page="Dashboard")
                            st.rerun()
                        else:
                            st.error(msg)
            with tab_register:
                with st.form("register_form"):
                    nu = st.text_input("Choose a username")
                    fn = st.text_input("Full name")
                    np_ = st.text_input("Choose a password", type="password")
                    np2 = st.text_input("Confirm password", type="password")
                    if np_:
                        label, tips = security.password_strength(np_)
                        st.caption(f"Strength: **{label}**"
                                   + (f" — {', '.join(tips)}" if tips else " ✅"))
                    if st.form_submit_button("Create account",
                                             use_container_width=True):
                        if np_ != np2:
                            st.error("Passwords do not match.")
                        else:
                            ok, msg = users_model.register_user(
                                conn, nu, np_, full_name=fn, role="agent")
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)


# ===========================================================================
#  SIDEBAR
# ===========================================================================
NAV = {"Dashboard": "📊  Dashboard", "Inbox": "📥  Inbox",
       "Customers": "👥  Customers", "Canned Replies": "💬  Canned Replies",
       "AI Copilot": "🤖  AI Copilot", "Team Admin": "🛠️  Team Admin"}


def sidebar():
    with st.sidebar:
        st.markdown(f"<div style='font-size:1.5rem;font-weight:700;padding:4px 0'>"
                    f"🎧 {APP_NAME}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='display:flex;gap:10px;align-items:center;margin:6px 0 2px'>"
            f"{avatar(st.session_state.full_name)}"
            f"<div><div style='font-weight:600'>{st.session_state.full_name}</div>"
            f"<div style='font-size:.74rem;color:#94a3b8'>"
            f"@{st.session_state.username} · {st.session_state.role}</div></div></div>",
            unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e293b'>", unsafe_allow_html=True)

        keys = [k for k in NAV if k != "Team Admin"
                or st.session_state.role in ("admin", "supervisor")]
        current = st.session_state.page if st.session_state.page in keys else keys[0]
        choice = st.radio("nav", keys, index=keys.index(current),
                          format_func=lambda k: NAV[k],
                          label_visibility="collapsed")
        st.session_state.page = choice

        st.markdown("<hr style='border-color:#1e293b'>", unsafe_allow_html=True)
        online = ai_assistant.is_online_available()
        st.markdown(
            f"<div style='font-size:.78rem;color:#94a3b8'>"
            f"{'🟢 AI: OpenAI connected' if online else '🟡 AI: offline mode'}</div>",
            unsafe_allow_html=True)
        st.write("")
        if st.button("Log out", use_container_width=True):
            for k in ("logged_in", "username", "role", "full_name", "active_ticket"):
                st.session_state[k] = False if k == "logged_in" else None
            st.rerun()


# ===========================================================================
#  DASHBOARD
# ===========================================================================
def kpi(col, label, value, sub=""):
    col.markdown(f"<div class='kpi'><h3>{label}</h3><div class='v'>{value}</div>"
                 f"<div class='s'>{sub}</div></div>", unsafe_allow_html=True)


def page_dashboard():
    st.markdown("## 📊 Dashboard")
    st.caption(f"Live overview · {datetime.now():%A %d %B %Y, %H:%M}")
    s = tickets_model.stats(conn)

    c = st.columns(5)
    kpi(c[0], "Total tickets", s["total"], "all time")
    kpi(c[1], "Open", s["open"], "awaiting action")
    kpi(c[2], "SLA breaches", s["sla_breaches"],
        "needs attention" if s["sla_breaches"] else "all on track")
    kpi(c[3], "Avg CSAT", f"{s['avg_csat']}/5" if s["avg_csat"] else "—",
        "customer satisfaction")
    kpi(c[4], "Resolution rate", f"{s['resolution_rate']}%",
        f"{s['resolved']} resolved")

    st.write("")
    df = tickets_model.get_all_tickets(conn)
    open_df = df[df["status"].isin(["Open", "Pending", "On Hold"])]
    urgent = open_df[open_df["priority"].isin(["Urgent", "High"])]
    if not urgent.empty:
        with st.container(border=True):
            st.markdown("#### 🔥 Needs attention — high-priority open tickets")
            for _, t in urgent.head(5).iterrows():
                txt, css = sla_badge(t["sla_due_at"], t["status"])
                cc = st.columns([5, 2, 2])
                cc[0].markdown(f"**#{t['ticket_id']}** {t['subject'][:46]}  \n"
                               f"<span class='small'>{t['customer_name']} · "
                               f"{t['channel']}</span>", unsafe_allow_html=True)
                cc[1].markdown(pill(t["priority"], PRIORITY_COLORS),
                               unsafe_allow_html=True)
                cc[2].markdown(f"<span class='pill' style='background:{css}'>{txt}"
                               f"</span>", unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("#### Tickets by status")
            st.bar_chart(tickets_model.count_by(conn, "status").set_index("status"),
                         color="#6366f1", height=240)
    with c2:
        with st.container(border=True):
            st.markdown("#### Tickets by channel")
            st.bar_chart(tickets_model.count_by(conn, "channel").set_index("channel"),
                         color="#10b981", height=240)
    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            st.markdown("#### Tickets by category")
            st.bar_chart(tickets_model.count_by(conn, "category").set_index("category"),
                         color="#f59e0b", height=240)
    with c4:
        with st.container(border=True):
            st.markdown("#### Agent workload")
            st.bar_chart(
                tickets_model.count_by(conn, "assigned_agent").set_index("assigned_agent"),
                color="#8b5cf6", height=240)


# ===========================================================================
#  INBOX
# ===========================================================================
def page_inbox():
    st.markdown("## 📥 Omnichannel Inbox")
    f = st.columns([1, 1, 1, 1, 2])
    status = f[0].selectbox("Status", ["All"] + tickets_model.STATUSES)
    priority = f[1].selectbox("Priority", ["All"] + tickets_model.PRIORITIES)
    channel = f[2].selectbox("Channel", ["All"] + tickets_model.CHANNELS)
    agents = ["All"] + [u["username"] for u in users_model.get_all_users(conn)]
    agent = f[3].selectbox("Agent", agents)
    search = f[4].text_input("🔍 Search subject / customer / order")

    df = tickets_model.filter_tickets(conn, status=status, priority=priority,
                                      channel=channel, agent=agent, search=search)

    left, right = st.columns([1, 1.5], gap="medium")
    with left:
        top = st.columns([3, 2])
        top[0].caption(f"{len(df)} tickets")
        if top[1].button("➕ New", use_container_width=True):
            st.session_state.active_ticket = "NEW"
            st.rerun()
        with st.container(height=620, border=False):
            for _, t in df.head(80).iterrows():
                icon = CHANNEL_ICONS.get(t["channel"], "•")
                sel = (str(st.session_state.active_ticket) == str(t["ticket_id"]))
                sla_txt, sla_css = sla_badge(t["sla_due_at"], t["status"])
                st.markdown(
                    f"<div class='tcard {'sel' if sel else ''}'>"
                    f"<div class='subj'>{icon} #{t['ticket_id']} · "
                    f"{t['subject'][:40]}</div>"
                    f"<div class='meta'>{t['customer_name']}</div>"
                    f"<div style='margin-top:6px'>{pill(t['priority'], PRIORITY_COLORS)} "
                    f"{pill(t['status'], STATUS_COLORS)} "
                    f"<span class='pill' style='background:{sla_css}'>{sla_txt}</span>"
                    f"</div></div>", unsafe_allow_html=True)
                if st.button("Open", key=f"open{t['ticket_id']}",
                             use_container_width=True):
                    st.session_state.active_ticket = int(t["ticket_id"])
                    st.rerun()
    with right:
        if st.session_state.active_ticket == "NEW":
            new_ticket_form()
        elif st.session_state.active_ticket:
            ticket_detail(int(st.session_state.active_ticket))
        else:
            st.info("Select a ticket to open the conversation, or create one.")


def new_ticket_form():
    st.markdown("### ➕ New ticket")
    custs = customers_model.get_all_customers(conn)
    with st.form("new_ticket"):
        cust = st.selectbox("Customer", custs["name"].tolist())
        a, b = st.columns(2)
        cat = a.selectbox("Category", tickets_model.CATEGORIES)
        chan = b.selectbox("Channel", tickets_model.CHANNELS)
        c, d = st.columns(2)
        pri = c.selectbox("Priority", tickets_model.PRIORITIES, index=1)
        order_ref = d.text_input("Order ref (optional)")
        subject = st.text_input("Subject")
        product = st.text_input("Product (optional)")
        body = st.text_area("First message from customer")
        if st.form_submit_button("Create ticket", type="primary",
                                 use_container_width=True):
            row = custs[custs["name"] == cust].iloc[0]
            tid = tickets_model.create_ticket(
                conn, int(row["customer_id"]), cust, chan, cat, subject,
                order_ref, product, pri, st.session_state.username)
            if body.strip():
                conv_model.add_message(conn, tid, int(row["customer_id"]),
                                       chan, "Inbound", cust, body, 0)
            st.session_state.active_ticket = tid
            st.toast(f"Ticket #{tid} created", icon="✅")
            st.rerun()


def ticket_detail(tid):
    t = tickets_model.get_ticket(conn, tid)
    if t is None:
        st.warning("Ticket not found.")
        return
    t = dict(t)

    # callbacks (run before rerun; may modify widget state safely)
    def _send():
        txt = st.session_state.get("reply_area", "").strip()
        if txt:
            conv_model.reply(conn, t, st.session_state.username, txt)
            st.session_state["reply_area"] = ""
            st.toast("Reply sent", icon="📤")

    def _note():
        txt = st.session_state.get("reply_area", "").strip()
        if txt:
            conv_model.add_note(conn, t, st.session_state.username, txt)
            st.session_state["reply_area"] = ""
            st.toast("Internal note added", icon="🗒️")

    head = st.columns([4, 1])
    head[0].markdown(f"### {CHANNEL_ICONS.get(t['channel'],'•')} "
                     f"#{t['ticket_id']} — {t['subject']}")
    sla_txt, sla_css = sla_badge(t["sla_due_at"], t["status"])
    head[0].markdown(
        f"{pill(t['priority'], PRIORITY_COLORS)} {pill(t['status'], STATUS_COLORS)} "
        f"<span class='pill' style='background:{sla_css}'>{sla_txt}</span> "
        f"<span class='small'>· {t['category']} · {t['channel']} · order "
        f"{t['order_ref'] or '—'}</span>", unsafe_allow_html=True)
    if head[1].button("🗑️ Delete", use_container_width=True):
        tickets_model.delete_ticket(conn, tid)
        st.session_state.active_ticket = None
        st.toast("Ticket deleted", icon="🗑️")
        st.rerun()

    st.markdown(f"<span class='small'>👤 <b>{t['customer_name']}</b> · assigned to "
                f"<b>{t['assigned_agent']}</b> · SLA due {t['sla_due_at']}</span>",
                unsafe_allow_html=True)

    with st.container(height=320, border=True):
        thread = conv_model.get_thread(conn, tid, include_notes=True)
        for _, m in thread.iterrows():
            if m["is_internal_note"]:
                st.markdown(f"<div class='bubble-note'>🗒️ <b>{m['sender']}</b> "
                            f"(note): {m['body']}<div class='stamp'>{m['sent_at']}"
                            f"</div></div>", unsafe_allow_html=True)
            elif m["direction"] == "Outbound":
                st.markdown(f"<div class='bubble-out'>{m['body']}"
                            f"<div class='stamp'>{m['sender']} · {m['sent_at']}</div>"
                            f"</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='bubble-in'><b>{m['sender']}</b><br>{m['body']}"
                            f"<div class='stamp'>{m['sent_at']}</div></div>",
                            unsafe_allow_html=True)

    canned = canned_model.get_all(conn)
    options = {f"{r['category']} · {r['title']}": r for _, r in canned.iterrows()}
    with st.expander("💬 Insert a canned reply"):
        pick = st.selectbox("Saved reply", ["—"] + list(options.keys()))
        if pick != "—" and st.button("Use this reply"):
            row = options[pick]
            st.session_state["reply_area"] = canned_model.fill_placeholders(
                row["body"], name=str(t["customer_name"]).split()[0],
                oid=t["order_ref"] or "your order",
                product=t["product"] or "your item")
            st.rerun()

    st.text_area("Reply to customer", key="reply_area", height=110,
                 placeholder="Type your reply…")
    bb = st.columns([1, 1, 3])
    bb[0].button("📤 Send", type="primary", use_container_width=True, on_click=_send)
    bb[1].button("🗒️ Note", use_container_width=True, on_click=_note)

    st.divider()
    with st.expander("⚙️ Ticket controls"):
        c = st.columns(4)
        ns = c[0].selectbox("Status", tickets_model.STATUSES,
                            index=tickets_model.STATUSES.index(t["status"])
                            if t["status"] in tickets_model.STATUSES else 0)
        npri = c[1].selectbox("Priority", tickets_model.PRIORITIES,
                              index=tickets_model.PRIORITIES.index(t["priority"])
                              if t["priority"] in tickets_model.PRIORITIES else 0)
        agent_list = [u["username"] for u in users_model.get_all_users(conn)]
        na = c[2].selectbox("Assign to", agent_list,
                            index=agent_list.index(t["assigned_agent"])
                            if t["assigned_agent"] in agent_list else 0)
        csat = c[3].selectbox("CSAT", ["—", "1", "2", "3", "4", "5"])
        if st.button("💾 Save changes", type="primary"):
            tickets_model.update_status(conn, tid, ns)
            tickets_model.set_priority(conn, tid, npri)
            tickets_model.assign_ticket(conn, tid, na)
            if csat != "—":
                tickets_model.set_csat(conn, tid, csat)
            st.toast("Ticket updated", icon="✅")
            st.rerun()


# ===========================================================================
#  CUSTOMERS
# ===========================================================================
def page_customers():
    st.markdown("## 👥 Customers")
    term = st.text_input("🔍 Search by name, email or city")
    df = (customers_model.search_customers(conn, term) if term
          else customers_model.get_all_customers(conn))

    cols = st.columns([2, 1], gap="medium")
    with cols[0]:
        st.dataframe(df, use_container_width=True, height=420, hide_index=True)
    with cols[1]:
        with st.container(border=True):
            st.markdown("**➕ Add customer**")
            with st.form("add_cust"):
                n = st.text_input("Name")
                e = st.text_input("Email")
                ph = st.text_input("Phone")
                city = st.text_input("City")
                tier = st.selectbox("Loyalty tier",
                                    ["Bronze", "Silver", "Gold", "VIP"])
                if st.form_submit_button("Add", use_container_width=True):
                    cid = customers_model.add_customer(conn, n, e, ph, city, tier)
                    st.toast(f"Added customer #{cid}", icon="✅")
                    st.rerun()

    st.divider()
    names = df["name"].tolist()
    if names:
        who = st.selectbox("View customer profile", names)
        row = df[df["name"] == who].iloc[0]
        with st.container(border=True):
            m = st.columns(4)
            m[0].metric("Loyalty", row["loyalty_tier"])
            m[1].metric("Lifetime orders", int(row["lifetime_orders"]))
            m[2].metric("Lifetime spend", f"£{row['lifetime_spend_gbp']:,.0f}")
            m[3].metric("City", row["city"])
            st.markdown(f"<span class='small'>✉️ {row['email']} · 📞 {row['phone']}"
                        f"</span>", unsafe_allow_html=True)
            st.markdown("**Ticket history**")
            hist = tickets_model.tickets_for_customer(conn, int(row["customer_id"]))
            if hist.empty:
                st.caption("No tickets yet.")
            else:
                st.dataframe(hist[["ticket_id", "channel", "category", "subject",
                                   "priority", "status", "created_at"]],
                             use_container_width=True, hide_index=True)


# ===========================================================================
#  CANNED REPLIES
# ===========================================================================
def page_canned():
    st.markdown("## 💬 Canned Replies")
    st.caption("Use {name}, {oid}, {product} placeholders — they auto-fill from "
               "the ticket when inserted.")
    df = canned_model.get_all(conn)
    st.dataframe(df, use_container_width=True, hide_index=True, height=300)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with st.container(border=True):
            st.markdown("**➕ Add a canned reply**")
            with st.form("add_canned"):
                cat = st.text_input("Category")
                title = st.text_input("Title")
                body = st.text_area("Body")
                if st.form_submit_button("Save", use_container_width=True):
                    canned_model.add(conn, cat, title, body)
                    st.toast("Saved", icon="✅")
                    st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown("**🗑️ Delete a canned reply**")
            if not df.empty:
                pick = st.selectbox("Choose",
                                    [f"{r['canned_id']} · {r['title']}"
                                     for _, r in df.iterrows()])
                if st.button("Delete", use_container_width=True):
                    canned_model.delete(conn, int(pick.split(" · ")[0]))
                    st.toast("Deleted", icon="🗑️")
                    st.rerun()


# ===========================================================================
#  AI COPILOT
# ===========================================================================
def page_ai():
    st.markdown("## 🤖 AI Copilot")
    online = ai_assistant.is_online_available()
    st.caption("Ask about your tickets, customers and metrics. "
               + ("Connected to OpenAI." if online
                  else "Offline mode — add an OpenAI key for full answers (README)."))

    quick = st.columns(4)
    prompts = ["Summary of today", "Are we breaching SLA?",
               "What's our CSAT?", "Busiest channel?"]
    for col, p in zip(quick, prompts):
        if col.button(p, use_container_width=True):
            st.session_state.ai_history.append(("user", p))
            reply, _ = ai_assistant.answer(conn, p, st.session_state.ai_history)
            st.session_state.ai_history.append(("assistant", reply))
            st.rerun()

    for role, content in st.session_state.ai_history:
        with st.chat_message("user" if role == "user" else "assistant",
                             avatar="🧑" if role == "user" else "🤖"):
            st.markdown(content)

    q = st.chat_input("Ask HelpHub Copilot…")
    if q:
        st.session_state.ai_history.append(("user", q))
        reply, _ = ai_assistant.answer(conn, q, st.session_state.ai_history)
        st.session_state.ai_history.append(("assistant", reply))
        st.rerun()


# ===========================================================================
#  TEAM ADMIN
# ===========================================================================
def page_team_admin():
    st.markdown("## 🛠️ Team Admin")
    st.caption("Manage agent accounts. Visible to supervisors and admins only.")
    rows = users_model.get_all_users(conn)
    df = pd.DataFrame([{"id": r["id"], "username": r["username"],
                        "full_name": r["full_name"], "role": r["role"],
                        "created_at": r["created_at"]} for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        with st.container(border=True):
            st.markdown("**➕ Add agent**")
            with st.form("add_agent"):
                u = st.text_input("Username")
                fn = st.text_input("Full name")
                p = st.text_input("Temp password", type="password")
                role = st.selectbox("Role", ["agent", "supervisor", "admin"])
                if st.form_submit_button("Create", use_container_width=True):
                    ok, msg = users_model.register_user(conn, u, p,
                                                        full_name=fn, role=role)
                    if ok:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.error(msg)
    with c2:
        with st.container(border=True):
            st.markdown("**🔑 Reset password**")
            who = st.selectbox("Agent", [r["username"] for r in rows], key="rp_who")
            newp = st.text_input("New password", type="password", key="rp_pw")
            if st.button("Reset", use_container_width=True):
                if users_model.update_password(conn, who, newp):
                    st.toast("Password reset", icon="✅")
    with c3:
        with st.container(border=True):
            st.markdown("**🗑️ Remove agent**")
            removable = [r["username"] for r in rows
                         if r["username"] != st.session_state.username]
            who = st.selectbox("Agent", removable, key="del_who")
            if st.button("Remove", use_container_width=True):
                users_model.delete_user(conn, who)
                st.toast(f"Removed {who}", icon="🗑️")
                st.rerun()


# ===========================================================================
#  ROUTER
# ===========================================================================
def main():
    if not st.session_state.logged_in:
        auth_screen()
        return
    sidebar()
    page = st.session_state.page
    {"Dashboard": page_dashboard, "Inbox": page_inbox, "Customers": page_customers,
     "Canned Replies": page_canned, "AI Copilot": page_ai,
     "Team Admin": page_team_admin}.get(page, page_dashboard)()


if __name__ == "__main__":
    main()
