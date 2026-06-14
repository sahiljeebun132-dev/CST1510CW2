"""
Relay — Omnichannel Customer Service Platform
=============================================
CST1510 Coursework 2 — Streamlit entry point (controller / view layer).

A Gnatta-style contact-centre with a 4-pane "Interactions" workspace
(Radar | Conversation | History | Update) plus agent superpowers:
  ✨ AI draft replies · 😊 live sentiment + tone coaching · ⚡ one-click quick
  actions · 📚 knowledge base · 🏅 personal performance scorecard.

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
from app_model import events as events_model
from app_model import insights
from app_model import ai_assistant

APP_NAME = "Relay"
DT_FMT = "%Y-%m-%d %H:%M:%S"
BRAND = "Footasylum"

st.set_page_config(page_title=f"{APP_NAME} — Customer Service",
                   page_icon="💬", layout="wide",
                   initial_sidebar_state="expanded")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--brand:#6d28d9;--brand2:#7c3aed;--accent:#ec4899;}
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top:.6rem; padding-bottom:.6rem; max-width:1750px;}
section[data-testid="stSidebar"] {background:#1a1530;}
section[data-testid="stSidebar"] * {color:#e9e5f7;}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  display:flex;align-items:center;padding:9px 12px;margin:2px 0;border-radius:10px;
  cursor:pointer;transition:.15s;font-weight:500;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:#2a2150;}
section[data-testid="stSidebar"] div[role="radiogroup"] input{display:none;}
.topbar{display:flex;align-items:center;gap:26px;background:#fff;border:1px solid #ece9f5;
        border-radius:14px;padding:10px 18px;margin-bottom:10px;box-shadow:0 1px 2px rgba(20,10,40,.05);}
.topbar .brand{font-size:1.4rem;font-weight:800;color:var(--brand);display:flex;align-items:center;gap:8px;}
.topbar .nav{display:flex;gap:18px;color:#6b7280;font-weight:600;font-size:.9rem;}
.topbar .nav .on{color:var(--brand);}
.topbar .sp{flex:1;}
.topbar .ico{color:#9aa0ac;font-size:1.05rem;}
.av{border-radius:50%;background:var(--brand);color:#fff;display:flex;align-items:center;
    justify-content:center;font-weight:700;flex:none;}
.kpi{background:#fff;border:1px solid #eceef2;border-radius:16px;padding:16px 18px;box-shadow:0 1px 2px rgba(16,24,40,.04);}
.kpi h3{margin:0;font-size:.70rem;color:#667085;font-weight:600;text-transform:uppercase;letter-spacing:.05em;}
.kpi .v{font-size:1.8rem;font-weight:800;margin-top:4px;color:#101828;line-height:1.1;}
.kpi .s{font-size:.73rem;color:#98a2b3;margin-top:2px;}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:.70rem;font-weight:600;line-height:1.5;}
.radar{border:1px solid #eceef2;border-radius:12px;padding:10px 12px;margin-bottom:6px;background:#fff;}
.radar.sel{background:#f6f1ff;border-color:#d8c8ff;box-shadow:inset 3px 0 0 var(--brand);}
.radar .nm{font-weight:700;color:#1e1b2e;font-size:.92rem;}
.radar .pv{color:#6b7280;font-size:.78rem;font-style:italic;margin:3px 0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.radar .tid{color:var(--brand);font-weight:700;font-size:.78rem;}
.icocircle{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.85rem;flex:none;}
.bin{background:#f3f4f6;border-radius:4px 12px 12px 12px;padding:9px 13px;margin:4px 0;max-width:78%;}
.bout{background:#fff;border:1px solid #e7e3f2;border-radius:12px 4px 12px 12px;padding:9px 13px;margin:4px 0 4px auto;max-width:78%;}
.bnote{background:#fff7da;border-left:3px solid #eab308;border-radius:8px;padding:8px 12px;margin:4px 0;font-style:italic;font-size:.85rem;}
.who{color:#9aa0ac;font-size:.7rem;margin-top:3px;}
.small{color:#6b7280;font-size:.8rem;}
.ph{font-weight:800;color:#1e1b2e;font-size:1.02rem;border-bottom:2px solid #ece9f5;padding-bottom:6px;margin-bottom:8px;}
.mood{border-radius:10px;padding:8px 12px;margin:6px 0;font-size:.82rem;}
.hrow{display:flex;gap:10px;margin-bottom:14px;}
.hrow .hi{width:26px;height:26px;border-radius:50%;background:#efeafe;color:var(--brand);display:flex;align-items:center;justify-content:center;font-size:.8rem;flex:none;}
.hrow .hb b{font-size:.86rem;color:#1e1b2e;}
.hrow .ht{color:var(--brand);font-size:.74rem;font-weight:600;}
.hrow .hp{display:inline-block;background:#f3eeff;color:var(--brand);border-radius:6px;padding:1px 7px;font-size:.68rem;font-weight:600;margin:3px 0;}
.hrow .hd{color:#475467;font-size:.78rem;}
.kbcard{border:1px solid #eceef2;border-radius:12px;padding:12px 14px;margin-bottom:10px;background:#fff;}
h2{font-weight:800 !important;color:#101828;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PRIORITY_COLORS = {"Urgent": "#fee2e2;color:#b42318", "High": "#fff1e6;color:#c4320a",
                   "Medium": "#fef7c3;color:#a15c07", "Low": "#dcfae6;color:#067647"}
STATUS_COLORS = {"Open": "#eff4ff;color:#2563eb", "Pending": "#fef7c3;color:#a15c07",
                 "On Hold": "#f4f3ff;color:#6938ef", "Resolved": "#dcfae6;color:#067647",
                 "Closed": "#f2f4f7;color:#475467"}
CHANNEL_ICONS = {"Email": "✉️", "Live Chat": "💬", "WhatsApp": "🟢", "Instagram DM": "📷",
                 "X / Twitter": "𝕏", "Facebook": "📘", "Phone": "📞", "SMS": "📱", "Internal": "🗒️"}
CHANNEL_BG = {"Email": "#d1fae5", "Live Chat": "#ede9fe", "WhatsApp": "#d1fae5",
              "Instagram DM": "#fce7f3", "X / Twitter": "#e5e7eb", "Facebook": "#dbeafe",
              "Phone": "#fef3c7", "SMS": "#ede9fe", "Internal": "#fef9c3"}
EVENT_ICONS = {"created": "🟢", "status": "🔁", "priority": "⚑", "assign": "👤",
               "reply": "📤", "note": "🗒️", "csat": "⭐", "resolved": "✅",
               "fields": "✏️", "macro": "⚡"}
MOOD_BG = {"Negative": "#fee2e2;color:#9a2620", "Neutral": "#f1f5f9;color:#475467",
           "Positive": "#dcfae6;color:#0a6b46"}
PRANK = {"Urgent": 0, "High": 1, "Medium": 2, "Low": 3}


def pill(text, palette):
    return f"<span class='pill' style='background:{palette.get(text,'#f2f4f7;color:#475467')}'>{text}</span>"


def fmt_duration(mins):
    mins = int(abs(mins))
    if mins < 60:
        return f"{mins} min"
    if mins < 1440:
        return f"{mins // 60}h {mins % 60}m"
    return f"{mins // 1440}d {(mins % 1440) // 60}h"


def ago(ts):
    try:
        secs = (datetime.now() - datetime.strptime(str(ts), DT_FMT)).total_seconds()
    except (ValueError, TypeError):
        return ""
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{int(secs//60)} min ago"
    if secs < 86400:
        return f"{int(secs//3600)}h ago"
    return f"{int(secs//86400)}d ago"


def sla_badge(due_str, status):
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


def avatar(name, size=34, bg="var(--brand)"):
    initials = "".join([p[0] for p in str(name).split()[:2]]).upper() or "?"
    return (f"<div class='av' style='width:{size}px;height:{size}px;background:{bg};"
            f"font-size:{size*0.4:.0f}px'>{initials}</div>")


def log_event(tid, etype, detail):
    events_model.log_event(conn, tid, etype, detail, st.session_state.username)


@st.cache_resource
def get_db():
    seed.init_database()
    return db.get_connection()


conn = get_db()

for key, val in {"logged_in": False, "username": None, "role": None,
                 "full_name": None, "page": "Interactions",
                 "active_ticket": None, "ai_history": []}.items():
    st.session_state.setdefault(key, val)


# ===========================================================================
#  AUTH
# ===========================================================================
def auth_screen():
    st.write("")
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown(
            "<div style='font-size:2.7rem;font-weight:800;color:#6d28d9'>💬 Relay</div>"
            "<div style='font-size:1.25rem;color:#475467;font-weight:500;margin-top:4px'>"
            "Every conversation, one workspace</div>", unsafe_allow_html=True)
        st.write("")
        st.markdown(
            "<div class='small' style='font-size:.95rem;line-height:1.9'>"
            "A contact-centre desk that unifies <b>email, live chat, WhatsApp, "
            "Instagram, X, Facebook, phone and SMS</b> — with AI draft replies, "
            "live sentiment coaching, one-click quick actions, a knowledge base "
            "and agent scorecards.</div>", unsafe_allow_html=True)
        st.write("")
        st.info("**Demo logins**\n\n"
                "• `admin` / `admin123` — admin\n\n"
                "• `sarah.lee` / `password1` — supervisor\n\n"
                "• `james.okafor` / `password1` — agent")
    with right:
        with st.container(border=True):
            tlog, treg = st.tabs(["🔐  Log in", "✍️  Register"])
            with tlog:
                with st.form("login_form"):
                    u = st.text_input("Username", placeholder="admin")
                    p = st.text_input("Password", type="password", placeholder="••••••••")
                    if st.form_submit_button("Log in", use_container_width=True, type="primary"):
                        ok, user, msg = users_model.login_user(conn, u, p)
                        if ok:
                            st.session_state.update(
                                logged_in=True, username=user["username"], role=user["role"],
                                full_name=user["full_name"] or user["username"],
                                page="Interactions")
                            st.rerun()
                        else:
                            st.error(msg)
            with treg:
                with st.form("register_form"):
                    nu = st.text_input("Choose a username")
                    fn = st.text_input("Full name")
                    np_ = st.text_input("Choose a password", type="password")
                    np2 = st.text_input("Confirm password", type="password")
                    if np_:
                        label, tips = security.password_strength(np_)
                        st.caption(f"Strength: **{label}**" + (f" — {', '.join(tips)}" if tips else " ✅"))
                    if st.form_submit_button("Create account", use_container_width=True):
                        if np_ != np2:
                            st.error("Passwords do not match.")
                        else:
                            ok, msg = users_model.register_user(conn, nu, np_, full_name=fn, role="agent")
                            st.success(msg) if ok else st.error(msg)


# ===========================================================================
#  TOP BAR + SIDEBAR
# ===========================================================================
def top_bar():
    page = st.session_state.page
    nav = " ".join(f"<span class='{'on' if p == page else ''}'>{p}</span>"
                   for p in ["Interactions", "Dashboard", "My Performance", "Knowledge"])
    online = ai_assistant.is_online_available()
    st.markdown(
        f"<div class='topbar'><div class='brand'>💬 {APP_NAME}</div>"
        f"<div class='nav'>{nav}</div><div class='sp'></div>"
        f"<span class='ico'>🔍</span><span class='ico'>💬</span><span class='ico'>🔔</span>"
        f"<span class='small'>{'🟢 AI' if online else '🟡 AI'}</span>"
        f"{avatar(st.session_state.full_name, 32)}</div>", unsafe_allow_html=True)


NAV = {"Interactions": "💬  Interactions", "Dashboard": "📊  Dashboard",
       "My Performance": "🏅  My Performance", "Customers": "👥  Customers",
       "Canned Replies": "📋  Canned Replies", "Knowledge": "📚  Knowledge",
       "AI Copilot": "🤖  AI Copilot", "Team Admin": "🛠️  Team Admin"}


def sidebar():
    with st.sidebar:
        st.markdown(f"<div style='font-size:1.5rem;font-weight:800;padding:4px 0'>💬 {APP_NAME}</div>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<div style='display:flex;gap:10px;align-items:center;margin:6px 0 2px'>"
            f"{avatar(st.session_state.full_name)}"
            f"<div><div style='font-weight:600'>{st.session_state.full_name}</div>"
            f"<div style='font-size:.74rem;color:#a99fd0'>@{st.session_state.username} · "
            f"{st.session_state.role}</div></div></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#2a2150'>", unsafe_allow_html=True)
        keys = [k for k in NAV if k != "Team Admin" or st.session_state.role in ("admin", "supervisor")]
        current = st.session_state.page if st.session_state.page in keys else keys[0]
        choice = st.radio("nav", keys, index=keys.index(current),
                          format_func=lambda k: NAV[k], label_visibility="collapsed")
        st.session_state.page = choice
        st.markdown("<hr style='border-color:#2a2150'>", unsafe_allow_html=True)
        if st.button("Log out", use_container_width=True):
            for k in ("logged_in", "username", "role", "full_name", "active_ticket"):
                st.session_state[k] = False if k == "logged_in" else None
            st.rerun()


# ===========================================================================
#  INTERACTIONS  — 4-pane workspace + agent superpowers
# ===========================================================================
def last_messages():
    df = pd.read_sql("SELECT ticket_id, body, MAX(sent_at) AS last_at FROM conversations "
                     "GROUP BY ticket_id", conn)
    return {int(r["ticket_id"]): (r["body"], r["last_at"]) for _, r in df.iterrows()}


def pick_next(df):
    openq = df[df["status"].isin(["Open", "Pending", "On Hold"])].copy()
    if openq.empty:
        st.toast("No open tickets in the queue 🎉")
        return
    openq["r"] = openq["priority"].map(PRANK).fillna(9)
    openq = openq.sort_values(["r", "sla_due_at"])
    st.session_state.active_ticket = int(openq.iloc[0]["ticket_id"])


def page_interactions():
    with st.expander("🔍 Filter the queue", expanded=False):
        f = st.columns([1, 1, 1, 1, 2])
        status = f[0].selectbox("Status", ["All"] + tickets_model.STATUSES)
        priority = f[1].selectbox("Priority", ["All"] + tickets_model.PRIORITIES)
        channel = f[2].selectbox("Channel", ["All"] + tickets_model.CHANNELS)
        agents = ["All"] + [u["username"] for u in users_model.get_all_users(conn)]
        agent = f[3].selectbox("Agent", agents)
        search = f[4].text_input("Search subject / customer / order")
    df = tickets_model.filter_tickets(conn, status=status, priority=priority,
                                      channel=channel, agent=agent, search=search)
    lastmsg = last_messages()

    c_radar, c_conv, c_hist, c_upd = st.columns([1.05, 2.25, 1.2, 1.3], gap="small")
    with c_radar:
        h = st.columns([2, 1.3, 1.3])
        h[0].markdown("<div class='ph'>Radar</div>", unsafe_allow_html=True)
        if h[1].button("➕ New", use_container_width=True):
            st.session_state.active_ticket = "NEW"; st.rerun()
        if h[2].button("⚡ Next", use_container_width=True, help="Jump to the most urgent open ticket"):
            pick_next(df); st.rerun()
        with st.container(height=640, border=False):
            render_radar(df, lastmsg)
    with c_conv:
        if st.session_state.active_ticket == "NEW":
            new_ticket_form()
        elif st.session_state.active_ticket:
            render_conversation(int(st.session_state.active_ticket), lastmsg)
        else:
            st.markdown("<div class='ph'>Conversation</div>", unsafe_allow_html=True)
            st.info("Select an interaction from the Radar, or hit ⚡ Next for the most urgent.")
    with c_hist:
        st.markdown("<div class='ph'>History</div>", unsafe_allow_html=True)
        if st.session_state.active_ticket and st.session_state.active_ticket != "NEW":
            with st.container(height=620, border=False):
                render_history(int(st.session_state.active_ticket))
    with c_upd:
        st.markdown("<div class='ph'>Update</div>", unsafe_allow_html=True)
        if st.session_state.active_ticket and st.session_state.active_ticket != "NEW":
            render_update(int(st.session_state.active_ticket))


def render_radar(df, lastmsg):
    for _, t in df.head(60).iterrows():
        tid = int(t["ticket_id"])
        sel = (str(st.session_state.active_ticket) == str(tid))
        body, _ = lastmsg.get(tid, (t["subject"], t["created_at"]))
        mood = insights.analyze_sentiment(body)["emoji"]
        try:
            mins = (datetime.now() - datetime.strptime(
                t["updated_at"] or t["created_at"], DT_FMT)).total_seconds() / 60
        except (ValueError, TypeError):
            mins = 0
        ico = CHANNEL_ICONS.get(t["channel"], "•")
        bg = CHANNEL_BG.get(t["channel"], "#eee")
        st.markdown(
            f"<div class='radar {'sel' if sel else ''}'>"
            f"<div style='display:flex;gap:9px;align-items:center'>"
            f"<div class='icocircle' style='background:{bg}'>{ico}</div>"
            f"<div class='nm'>{t['customer_name']} {mood}</div></div>"
            f"<div class='pv'>{str(body)[:46]}</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<span class='tid'>#{tid}</span>"
            f"<span class='pill' style='background:#f6f1ff;color:#6d28d9'>Assigned {fmt_duration(mins)}</span>"
            f"</div></div>", unsafe_allow_html=True)
        if st.button("Open", key=f"open{tid}", use_container_width=True):
            st.session_state.active_ticket = tid; st.rerun()


def render_conversation(tid, lastmsg):
    t = tickets_model.get_ticket(conn, tid)
    if t is None:
        st.warning("Ticket not found."); return
    t = dict(t)
    cust = customers_model.get_customer(conn, t["customer_id"])
    email = dict(cust)["email"] if cust is not None else ""
    _, last_at = lastmsg.get(tid, ("", t["created_at"]))
    thread_df = conv_model.get_thread(conn, tid, include_notes=True)
    user = st.session_state.username

    def fill(body):
        return canned_model.fill_placeholders(
            body, name=str(t["customer_name"]).split()[0],
            oid=t["order_ref"] or "your order", product=t["product"] or "your item")

    # --- callbacks (run before widget re-instantiation, so editing reply is safe)
    def _send():
        txt = st.session_state.get("reply_area", "").strip()
        if txt:
            conv_model.reply(conn, t, user, txt); log_event(tid, "reply", "Agent replied")
            st.session_state["reply_area"] = ""; st.toast("Message sent", icon="📤")

    def _note():
        txt = st.session_state.get("reply_area", "").strip()
        if txt:
            conv_model.add_note(conn, t, user, txt); log_event(tid, "note", "Internal note added")
            st.session_state["reply_area"] = ""; st.toast("Note added", icon="🗒️")

    def _end():
        tickets_model.update_status(conn, tid, "Resolved")
        log_event(tid, "status", "Interaction ended — marked Resolved")
        st.toast("Interaction ended (Resolved)", icon="✅")

    def _set_reply(text):
        st.session_state["reply_area"] = text
        st.toast("Inserted into composer", icon="✍️")

    def _draft():
        txt, mode = ai_assistant.draft_reply(conn, t, thread_df)
        st.session_state["reply_area"] = txt
        st.toast(f"AI draft ready ({mode})", icon="✨")

    def _macro(m):
        conv_model.reply(conn, t, user, fill(m["body"]))
        log_event(tid, "macro", f"Quick action: {m['label']}")
        if m.get("status"):
            tickets_model.update_status(conn, tid, m["status"])
            log_event(tid, "status", f"Status → {m['status']} (quick action)")
        if m.get("wrap"):
            tickets_model.update_fields(conn, tid, wrap_one=m["wrap"])
        st.toast("Quick action applied", icon="⚡")

    # --- header ---
    head = st.columns([0.5, 5, 1])
    head[0].markdown(avatar(t["customer_name"], 40, "#7c3aed"), unsafe_allow_html=True)
    try:
        lhm = datetime.strptime(str(last_at), DT_FMT).strftime("%H:%M")
    except (ValueError, TypeError):
        lhm = "—"
    head[1].markdown(
        f"<div style='font-weight:700;font-size:1.02rem'>{t['customer_name']}</div>"
        f"<div class='small'>{email}</div>"
        f"<div class='small'>Last message received at {lhm}</div>", unsafe_allow_html=True)
    if head[2].button("✕ Close", use_container_width=True):
        st.session_state.active_ticket = None; st.rerun()

    sla_txt, sla_css = sla_badge(t["sla_due_at"], t["status"])
    st.markdown(
        f"<span class='pill' style='background:{CHANNEL_BG.get(t['channel'],'#eee')};color:#3b2a66'>"
        f"{CHANNEL_ICONS.get(t['channel'],'•')} {t['channel']}</span> "
        f"{pill(t['priority'], PRIORITY_COLORS)} {pill(t['status'], STATUS_COLORS)} "
        f"<span class='pill' style='background:{sla_css}'>{sla_txt}</span> "
        f"<span class='small'>· #{tid} · {t['subject']}</span>", unsafe_allow_html=True)

    # --- thread ---
    with st.container(height=250, border=False):
        for _, m in thread_df.iterrows():
            if m["is_internal_note"]:
                st.markdown(f"<div class='bnote'>🗒️ <b>{m['sender']}</b> (note): {m['body']}"
                            f"<div class='who'>{ago(m['sent_at'])}</div></div>", unsafe_allow_html=True)
            elif m["direction"] == "Outbound":
                st.markdown(f"<div class='bout'>{m['body']}<div class='who'>{m['sender']} · "
                            f"{ago(m['sent_at'])} · Delivered</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='bin'>{m['body']}<div class='who'>{m['sender']} · "
                            f"{ago(m['sent_at'])}</div></div>", unsafe_allow_html=True)

    # --- sentiment meter + tone coaching ---
    inbound = thread_df[thread_df["direction"] == "Inbound"]
    last_in = inbound.iloc[-1]["body"] if len(inbound) else ""
    senti = insights.analyze_sentiment(last_in)
    st.markdown(
        f"<div class='mood' style='background:{MOOD_BG.get(senti['label'])}'>"
        f"{senti['emoji']} <b>Customer mood: {senti['label']}</b>"
        f"{'  ⚡ urgent' if senti['urgent'] else ''} — "
        f"<span style='font-weight:500'>{insights.recommend_tone(senti)}</span></div>",
        unsafe_allow_html=True)

    # --- quick-action macros (one click = reply + status/wrap) ---
    st.markdown("<span class='small'><b>⚡ Quick actions</b> — one click sends a reply "
                "and updates the ticket</span>", unsafe_allow_html=True)
    macros = insights.suggest_actions(t["category"])
    for i in range(0, len(macros), 2):
        cc = st.columns(2)
        for j, m in enumerate(macros[i:i + 2]):
            cc[j].button(m["label"], key=f"macro{i+j}", use_container_width=True,
                         on_click=_macro, args=(m,))

    # --- composer ---
    st.markdown(f"<span class='small'>**To:** {t['customer_name']} &nbsp; "
                f"**From:** {BRAND} — {t['channel']}</span>", unsafe_allow_html=True)
    st.text_area("msg", key="reply_area", height=88, label_visibility="collapsed",
                 placeholder="Enter your message here")
    chars = len(st.session_state.get("reply_area", ""))
    tb = st.columns([1, 1, 1.1, 1.6, 0.9, 0.9])
    with tb[0].popover("📋", use_container_width=True):
        st.caption(f"Canned replies · {t['category']}")
        canned = canned_model.get_all(conn)
        match = canned[canned["category"].isin([t["category"], "Greeting", "Closing"])]
        for _, r in (match if not match.empty else canned).iterrows():
            st.button(f"➕ {r['title']}", key=f"can{r['canned_id']}", use_container_width=True,
                      on_click=_set_reply, args=(fill(r["body"]),))
    with tb[1].popover("📚", use_container_width=True):
        st.caption("Knowledge base")
        kq = st.text_input("Search", key="kbq", label_visibility="collapsed",
                           placeholder="Search articles…")
        for a in insights.search_kb(kq or t["category"]):
            st.markdown(f"**{a['title']}**  \n<span class='small'>{a['answer'][:90]}…</span>",
                        unsafe_allow_html=True)
            st.button("Insert", key=f"kb{a['id']}", use_container_width=True,
                      on_click=_set_reply, args=(a["answer"],))
    tb[2].button("✨ Draft", use_container_width=True, on_click=_draft,
                 help="Let AI write a reply from the conversation")
    tb[3].markdown(f"<div style='text-align:right;color:#9aa0ac;font-size:.8rem;"
                   f"padding-top:6px'>Characters: {chars}</div>", unsafe_allow_html=True)
    tb[4].button("End", use_container_width=True, on_click=_end)
    tb[5].button("Send", type="primary", use_container_width=True, on_click=_send)
    if st.button("🗒️ Add internal note", use_container_width=True):
        _note(); st.rerun()


def render_history(tid):
    t = dict(tickets_model.get_ticket(conn, tid))
    rows = [("created", "Interaction opened", f"via {t['channel']}", t["customer_name"], t["created_at"])]
    for _, e in events_model.get_events(conn, tid).iterrows():
        rows.append((e["event_type"], e["event_type"].title(), e["detail"], e["actor"], e["created_at"]))
    if t.get("resolved_at"):
        rows.append(("resolved", "Resolved", f"Marked {t['status']}", "", t["resolved_at"]))
    rows.sort(key=lambda r: str(r[4]))
    for etype, label, detail, actor, when in rows:
        who = f" · {actor}" if actor else ""
        st.markdown(
            f"<div class='hrow'><div class='hi'>{EVENT_ICONS.get(etype,'•')}</div>"
            f"<div class='hb'><b>{APP_NAME}{who}</b><br><span class='ht'>{when}</span><br>"
            f"<span class='hp'>{label}</span><br><span class='hd'>{detail}</span></div></div>",
            unsafe_allow_html=True)


def render_update(tid):
    t = dict(tickets_model.get_ticket(conn, tid))
    cust = customers_model.get_customer(conn, t["customer_id"])
    cust = dict(cust) if cust is not None else {}
    with st.form("update_panel"):
        st.text_input("Queue", value=f"{t['channel']} — {BRAND}", disabled=True)
        order = st.text_input("Order Number", value=t.get("order_ref") or "")
        track = st.text_input("Tracking Number", value=t.get("tracking_number") or "")
        email = st.text_input("Email Address", value=cust.get("email", ""))
        phone = st.text_input("Phone Number", value=cust.get("phone", ""))
        postcode = st.text_input("Postcode", value=t.get("postcode") or "")
        reason = st.selectbox("Reason For Contact", tickets_model.CATEGORIES,
                              index=tickets_model.CATEGORIES.index(t["category"])
                              if t["category"] in tickets_model.CATEGORIES else 0)
        status = st.selectbox("Status", tickets_model.STATUSES,
                              index=tickets_model.STATUSES.index(t["status"])
                              if t["status"] in tickets_model.STATUSES else 0)
        priority = st.selectbox("Priority", tickets_model.PRIORITIES,
                                index=tickets_model.PRIORITIES.index(t["priority"])
                                if t["priority"] in tickets_model.PRIORITIES else 0)
        agent_list = [u["username"] for u in users_model.get_all_users(conn)]
        agent = st.selectbox("Assigned Agent", agent_list,
                             index=agent_list.index(t["assigned_agent"])
                             if t["assigned_agent"] in agent_list else 0)
        w1 = st.text_input("Wrap One", value=t.get("wrap_one") or "", placeholder="Start typing here…")
        w2 = st.text_input("Wrap Two", value=t.get("wrap_two") or "", placeholder="Start typing here…")
        if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
            tickets_model.update_fields(conn, tid, order_ref=order, tracking_number=track,
                                        postcode=postcode, category=reason, priority=priority,
                                        assigned_agent=agent, wrap_one=w1, wrap_two=w2)
            if status != t["status"]:
                tickets_model.update_status(conn, tid, status)
                log_event(tid, "status", f"Status changed to {status}")
            if priority != t["priority"]:
                log_event(tid, "priority", f"Priority set to {priority}")
            if agent != t["assigned_agent"]:
                log_event(tid, "assign", f"Assigned to {agent}")
            if cust and (email != cust.get("email") or phone != cust.get("phone")):
                customers_model.update_customer(conn, t["customer_id"], email=email, phone=phone)
            log_event(tid, "fields", "Ticket details updated")
            st.toast("Ticket updated", icon="✅"); st.rerun()
    if st.button("🗑️ Delete ticket", use_container_width=True):
        tickets_model.delete_ticket(conn, tid)
        st.session_state.active_ticket = None
        st.toast("Ticket deleted", icon="🗑️"); st.rerun()


def new_ticket_form():
    st.markdown("<div class='ph'>New interaction</div>", unsafe_allow_html=True)
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
        if st.form_submit_button("Create interaction", type="primary", use_container_width=True):
            row = custs[custs["name"] == cust].iloc[0]
            tid = tickets_model.create_ticket(conn, int(row["customer_id"]), cust, chan, cat,
                                              subject, order_ref, product, pri, st.session_state.username)
            if body.strip():
                conv_model.add_message(conn, tid, int(row["customer_id"]), chan, "Inbound", cust, body, 0)
            log_event(tid, "created", f"Interaction created on {chan}")
            st.session_state.active_ticket = tid
            st.toast(f"Ticket #{tid} created", icon="✅"); st.rerun()


# ===========================================================================
#  MY PERFORMANCE  (agent scorecard + leaderboard)
# ===========================================================================
def page_performance():
    st.markdown("## 🏅 My Performance")
    me = st.session_state.username
    df = tickets_model.get_all_tickets(conn)
    open_states = ["Open", "Pending", "On Hold"]
    mine = df[df["assigned_agent"] == me]
    open_mine = mine[mine["status"].isin(open_states)]
    resolved_mine = mine[mine["status"].isin(["Resolved", "Closed"])]
    csat = pd.to_numeric(mine["csat_score"], errors="coerce").dropna()
    now = datetime.now()
    at_risk = 0
    for _, r in open_mine.iterrows():
        try:
            if datetime.strptime(r["sla_due_at"], DT_FMT) < now:
                at_risk += 1
        except (ValueError, TypeError):
            pass

    c = st.columns(4)
    c[0].markdown(f"<div class='kpi'><h3>Assigned to me</h3><div class='v'>{len(mine)}</div>"
                  f"<div class='s'>{len(open_mine)} still open</div></div>", unsafe_allow_html=True)
    c[1].markdown(f"<div class='kpi'><h3>Resolved by me</h3><div class='v'>{len(resolved_mine)}</div>"
                  f"<div class='s'>all time</div></div>", unsafe_allow_html=True)
    c[2].markdown(f"<div class='kpi'><h3>My CSAT</h3><div class='v'>"
                  f"{round(csat.mean(),2) if len(csat) else '—'}/5</div>"
                  f"<div class='s'>{len(csat)} ratings</div></div>", unsafe_allow_html=True)
    c[3].markdown(f"<div class='kpi'><h3>SLA at risk</h3><div class='v'>{at_risk}</div>"
                  f"<div class='s'>open & overdue</div></div>", unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.markdown("#### 🏆 Team leaderboard")
        rows = []
        for ag, g in df.groupby("assigned_agent"):
            rc = int(g["status"].isin(["Resolved", "Closed"]).sum())
            cs = pd.to_numeric(g["csat_score"], errors="coerce").dropna()
            rows.append({"Agent": ag, "Resolved": rc, "Open": int(g["status"].isin(open_states).sum()),
                         "Avg CSAT": round(cs.mean(), 2) if len(cs) else None})
        lb = pd.DataFrame(rows).sort_values("Resolved", ascending=False)
        st.dataframe(lb, use_container_width=True, hide_index=True)
        st.bar_chart(lb.set_index("Agent")[["Resolved"]], color="#6d28d9", height=240)
    with right:
        st.markdown("#### 📋 My open queue")
        if open_mine.empty:
            st.success("You're all caught up — no open tickets! 🎉")
        else:
            for _, t in open_mine.head(12).iterrows():
                txt, css = sla_badge(t["sla_due_at"], t["status"])
                cc = st.columns([4, 2])
                cc[0].markdown(f"**#{t['ticket_id']}** {t['subject'][:30]}  \n"
                               f"<span class='small'>{t['customer_name']}</span>", unsafe_allow_html=True)
                if cc[1].button("Open", key=f"perf{t['ticket_id']}", use_container_width=True):
                    st.session_state.active_ticket = int(t["ticket_id"])
                    st.session_state.page = "Interactions"; st.rerun()


# ===========================================================================
#  KNOWLEDGE BASE
# ===========================================================================
def page_knowledge():
    st.markdown("## 📚 Knowledge Base")
    st.caption("Search internal answers and policies. In a conversation, open 📚 in the "
               "composer to insert any of these straight into your reply.")
    q = st.text_input("🔍 Search the knowledge base", placeholder="e.g. refund, delivery, sizing")
    for a in insights.search_kb(q) if q else insights.KB_ARTICLES:
        st.markdown(f"<div class='kbcard'><b>{a['title']}</b> "
                    f"<span class='pill' style='background:#f3eeff;color:#6d28d9'>{a['category']}</span>"
                    f"<div class='small' style='margin-top:6px'>{a['answer']}</div></div>",
                    unsafe_allow_html=True)


# ===========================================================================
#  DASHBOARD / CUSTOMERS / CANNED / AI / TEAM ADMIN
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
    kpi(c[2], "SLA breaches", s["sla_breaches"], "needs attention" if s["sla_breaches"] else "on track")
    kpi(c[3], "Avg CSAT", f"{s['avg_csat']}/5" if s["avg_csat"] else "—", "satisfaction")
    kpi(c[4], "Resolution rate", f"{s['resolution_rate']}%", f"{s['resolved']} resolved")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("#### Tickets by status")
            st.bar_chart(tickets_model.count_by(conn, "status").set_index("status"), color="#6d28d9", height=240)
    with c2:
        with st.container(border=True):
            st.markdown("#### Tickets by channel")
            st.bar_chart(tickets_model.count_by(conn, "channel").set_index("channel"), color="#ec4899", height=240)
    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            st.markdown("#### Tickets by category")
            st.bar_chart(tickets_model.count_by(conn, "category").set_index("category"), color="#f59e0b", height=240)
    with c4:
        with st.container(border=True):
            st.markdown("#### Agent workload")
            st.bar_chart(tickets_model.count_by(conn, "assigned_agent").set_index("assigned_agent"),
                         color="#10b981", height=240)


def page_customers():
    st.markdown("## 👥 Customers")
    term = st.text_input("🔍 Search by name, email or city")
    df = (customers_model.search_customers(conn, term) if term else customers_model.get_all_customers(conn))
    cols = st.columns([2, 1], gap="medium")
    with cols[0]:
        st.dataframe(df, use_container_width=True, height=420, hide_index=True)
    with cols[1]:
        with st.container(border=True):
            st.markdown("**➕ Add customer**")
            with st.form("add_cust"):
                n = st.text_input("Name"); e = st.text_input("Email")
                ph = st.text_input("Phone"); city = st.text_input("City")
                tier = st.selectbox("Loyalty tier", ["Bronze", "Silver", "Gold", "VIP"])
                if st.form_submit_button("Add", use_container_width=True):
                    cid = customers_model.add_customer(conn, n, e, ph, city, tier)
                    st.toast(f"Added customer #{cid}", icon="✅"); st.rerun()
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
            st.markdown(f"<span class='small'>✉️ {row['email']} · 📞 {row['phone']}</span>", unsafe_allow_html=True)
            hist = tickets_model.tickets_for_customer(conn, int(row["customer_id"]))
            if not hist.empty:
                st.dataframe(hist[["ticket_id", "channel", "category", "subject", "priority",
                                   "status", "created_at"]], use_container_width=True, hide_index=True)


def page_canned():
    st.markdown("## 📋 Canned Replies")
    st.caption("Use {name}, {oid}, {product} placeholders — they auto-fill on insert.")
    df = canned_model.get_all(conn)
    st.dataframe(df, use_container_width=True, hide_index=True, height=300)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with st.container(border=True):
            st.markdown("**➕ Add a canned reply**")
            with st.form("add_canned"):
                cat = st.text_input("Category"); title = st.text_input("Title")
                body = st.text_area("Body")
                if st.form_submit_button("Save", use_container_width=True):
                    canned_model.add(conn, cat, title, body); st.toast("Saved", icon="✅"); st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown("**🗑️ Delete a canned reply**")
            if not df.empty:
                pick = st.selectbox("Choose", [f"{r['canned_id']} · {r['title']}" for _, r in df.iterrows()])
                if st.button("Delete", use_container_width=True):
                    canned_model.delete(conn, int(pick.split(" · ")[0])); st.toast("Deleted", icon="🗑️"); st.rerun()


def page_ai():
    st.markdown("## 🤖 AI Copilot")
    online = ai_assistant.is_online_available()
    st.caption("Ask about your tickets, customers and metrics. "
               + ("Connected to OpenAI." if online else "Offline mode — add an OpenAI key (README)."))
    quick = st.columns(4)
    for col, p in zip(quick, ["Summary of today", "Are we breaching SLA?", "What's our CSAT?", "Busiest channel?"]):
        if col.button(p, use_container_width=True):
            st.session_state.ai_history.append(("user", p))
            r, _ = ai_assistant.answer(conn, p, st.session_state.ai_history)
            st.session_state.ai_history.append(("assistant", r)); st.rerun()
    for role, content in st.session_state.ai_history:
        with st.chat_message("user" if role == "user" else "assistant",
                             avatar="🧑" if role == "user" else "🤖"):
            st.markdown(content)
    q = st.chat_input("Ask Relay Copilot…")
    if q:
        st.session_state.ai_history.append(("user", q))
        r, _ = ai_assistant.answer(conn, q, st.session_state.ai_history)
        st.session_state.ai_history.append(("assistant", r)); st.rerun()


def page_team_admin():
    st.markdown("## 🛠️ Team Admin")
    st.caption("Manage agent accounts. Supervisors and admins only.")
    rows = users_model.get_all_users(conn)
    df = pd.DataFrame([{"id": r["id"], "username": r["username"], "full_name": r["full_name"],
                        "role": r["role"], "created_at": r["created_at"]} for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        with st.container(border=True):
            st.markdown("**➕ Add agent**")
            with st.form("add_agent"):
                u = st.text_input("Username"); fn = st.text_input("Full name")
                p = st.text_input("Temp password", type="password")
                role = st.selectbox("Role", ["agent", "supervisor", "admin"])
                if st.form_submit_button("Create", use_container_width=True):
                    ok, msg = users_model.register_user(conn, u, p, full_name=fn, role=role)
                    if ok:
                        st.toast(msg, icon="✅"); st.rerun()
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
            rem = [r["username"] for r in rows if r["username"] != st.session_state.username]
            who = st.selectbox("Agent", rem, key="del_who")
            if st.button("Remove", use_container_width=True):
                users_model.delete_user(conn, who); st.toast(f"Removed {who}", icon="🗑️"); st.rerun()


# ===========================================================================
#  ROUTER
# ===========================================================================
def main():
    if not st.session_state.logged_in:
        auth_screen(); return
    sidebar()
    top_bar()
    {"Interactions": page_interactions, "Dashboard": page_dashboard,
     "My Performance": page_performance, "Customers": page_customers,
     "Canned Replies": page_canned, "Knowledge": page_knowledge,
     "AI Copilot": page_ai, "Team Admin": page_team_admin}.get(
        st.session_state.page, page_interactions)()


if __name__ == "__main__":
    main()
