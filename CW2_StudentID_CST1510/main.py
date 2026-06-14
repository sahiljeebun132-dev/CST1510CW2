"""
Relay — Omnichannel Customer Service Platform
=============================================
CST1510 Coursework 2 — Streamlit entry point (controller / view layer).

Clean two-pane help-desk: a ticket queue on the left and a roomy conversation
on the right with Conversation / History / Update / Customer tabs. Agent tools
(AI draft replies, sentiment coaching, quick actions, canned replies, knowledge
base) live inside the conversation. Plus a dashboard, customers CRM, personal
performance scorecard, knowledge base and an AI co-pilot.

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
                   page_icon="💬", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------
# Light, minimal theme
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#f6f7f9;--card:#fff;--line:#e9ebf0;--ink:#1c2330;--muted:#737a88;
      --accent:#4f46e5;--accent-soft:#eef0ff;}
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:var(--bg);}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.2rem;padding-bottom:1rem;max-width:1500px;}
h1,h2,h3{color:var(--ink);font-weight:800;letter-spacing:-.01em;}

/* sidebar — light */
section[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line);}
section[data-testid="stSidebar"] *{color:var(--ink);}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  display:flex;align-items:center;padding:9px 12px;margin:1px 0;border-radius:10px;
  cursor:pointer;font-weight:500;color:var(--muted);transition:.12s;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:#f4f5f8;color:var(--ink);}
section[data-testid="stSidebar"] div[role="radiogroup"] input{display:none;}

/* page title */
.title{font-size:1.5rem;font-weight:800;color:var(--ink);margin:0 0 2px;}
.sub{color:var(--muted);font-size:.85rem;margin-bottom:14px;}

/* generic card */
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;}

/* KPI */
.kpi{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 18px;}
.kpi h3{margin:0;font-size:.70rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em;}
.kpi .v{font-size:1.8rem;font-weight:800;margin-top:4px;color:var(--ink);}
.kpi .s{font-size:.73rem;color:#9aa0ab;margin-top:2px;}

/* pills */
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.7rem;font-weight:600;}

/* queue rows (non-selected = button, selected = highlighted card) */
[class*="st-key-q_"] button{
  text-align:left!important;justify-content:flex-start!important;border:1px solid var(--line);
  background:var(--card);border-radius:12px;padding:11px 13px;font-weight:500;color:var(--ink);
  box-shadow:none;line-height:1.3;min-height:0;}
[class*="st-key-q_"] button:hover{border-color:#cdd0db;background:#fafbff;}
[class*="st-key-q_"] button p{font-size:.86rem;}
.qsel{background:var(--accent-soft);border:1px solid #c7c9f5;border-radius:12px;padding:11px 13px;
      box-shadow:inset 3px 0 0 var(--accent);margin-bottom:2px;}
.qsel .nm{font-weight:700;color:var(--ink);font-size:.9rem;}
.qsel .mt{color:var(--muted);font-size:.74rem;margin-top:2px;}

/* conversation */
.cvhead{display:flex;align-items:center;gap:12px;margin-bottom:2px;}
.av{border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;
    justify-content:center;font-weight:700;flex:none;}
.bin{background:#f1f3f6;border-radius:4px 14px 14px 14px;padding:10px 14px;margin:6px 0;max-width:74%;
     color:var(--ink);font-size:.9rem;}
.bout{background:var(--accent-soft);border-radius:14px 4px 14px 14px;padding:10px 14px;margin:6px 0 6px auto;
      max-width:74%;color:#262b6b;font-size:.9rem;}
.bnote{background:#fff7da;border-left:3px solid #eab308;border-radius:8px;padding:9px 13px;margin:6px 0;
       font-style:italic;font-size:.85rem;}
.who{color:#9aa0ab;font-size:.7rem;margin-top:4px;}
.small{color:var(--muted);font-size:.8rem;}
.mood{border-radius:10px;padding:9px 13px;margin:8px 0;font-size:.82rem;}

/* history timeline */
.hrow{display:flex;gap:11px;margin-bottom:15px;}
.hrow .hi{width:28px;height:28px;border-radius:50%;background:var(--accent-soft);color:var(--accent);
          display:flex;align-items:center;justify-content:center;font-size:.8rem;flex:none;}
.hrow b{font-size:.86rem;color:var(--ink);}
.hrow .ht{color:var(--accent);font-size:.74rem;font-weight:600;}
.hrow .hp{display:inline-block;background:var(--accent-soft);color:var(--accent);border-radius:6px;
          padding:1px 8px;font-size:.68rem;font-weight:600;margin:3px 0;}
.hrow .hd{color:var(--muted);font-size:.78rem;}
.kbcard{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:13px 16px;margin-bottom:10px;}
.stTabs [data-baseweb="tab-list"]{gap:4px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PRIORITY_COLORS = {"Urgent": "#fee2e2;color:#b42318", "High": "#fff1e6;color:#c4320a",
                   "Medium": "#fef7c3;color:#a15c07", "Low": "#e7f6ee;color:#067647"}
STATUS_COLORS = {"Open": "#eef0ff;color:#4f46e5", "Pending": "#fef7c3;color:#a15c07",
                 "On Hold": "#f4f3ff;color:#6938ef", "Resolved": "#e7f6ee;color:#067647",
                 "Closed": "#f1f3f6;color:#475467"}
CHANNEL_ICONS = {"Email": "✉️", "Live Chat": "💬", "WhatsApp": "🟢", "Instagram DM": "📷",
                 "X / Twitter": "𝕏", "Facebook": "📘", "Phone": "📞", "SMS": "📱", "Internal": "🗒️"}
DOT = {"Urgent": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
EVENT_ICONS = {"created": "🟢", "status": "🔁", "priority": "⚑", "assign": "👤",
               "reply": "📤", "note": "🗒️", "csat": "⭐", "resolved": "✅",
               "fields": "✏️", "macro": "⚡"}
MOOD_BG = {"Negative": "#fdeceb;color:#9a2620", "Neutral": "#f1f3f6;color:#475467",
           "Positive": "#e7f6ee;color:#0a6b46"}
PRANK = {"Urgent": 0, "High": 1, "Medium": 2, "Low": 3}


def pill(text, palette):
    return f"<span class='pill' style='background:{palette.get(text,'#f1f3f6;color:#475467')}'>{text}</span>"


def fmt_duration(mins):
    mins = int(abs(mins))
    if mins < 60:
        return f"{mins}m"
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
        return f"{int(secs//60)}m ago"
    if secs < 86400:
        return f"{int(secs//3600)}h ago"
    return f"{int(secs//86400)}d ago"


def sla_badge(due_str, status):
    if status in ("Resolved", "Closed"):
        return "Closed", "#f1f3f6;color:#475467"
    try:
        due = datetime.strptime(str(due_str), DT_FMT)
    except (ValueError, TypeError):
        return "—", "#f1f3f6;color:#475467"
    mins = (due - datetime.now()).total_seconds() / 60
    if mins < 0:
        return f"Overdue {fmt_duration(mins)}", "#fee2e2;color:#b42318"
    if mins < 60:
        return f"{fmt_duration(mins)} left", "#fff1e6;color:#c4320a"
    return f"{fmt_duration(mins)} left", "#e7f6ee;color:#067647"


def avatar(name, size=38, bg="var(--accent)"):
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
                 "full_name": None, "page": "Inbox",
                 "active_ticket": None, "ai_history": []}.items():
    st.session_state.setdefault(key, val)


# ===========================================================================
#  AUTH
# ===========================================================================
def auth_screen():
    st.write("")
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        st.markdown("<div style='text-align:center;font-size:2.6rem;font-weight:800;"
                    "color:#4f46e5'>💬 Relay</div>"
                    "<div style='text-align:center;color:#737a88;margin-bottom:18px'>"
                    "Every conversation, one workspace</div>", unsafe_allow_html=True)
        with st.container(border=True):
            tlog, treg = st.tabs(["Log in", "Register"])
            with tlog:
                with st.form("login_form"):
                    u = st.text_input("Username", placeholder="admin")
                    p = st.text_input("Password", type="password", placeholder="••••••••")
                    if st.form_submit_button("Log in", use_container_width=True, type="primary"):
                        ok, user, msg = users_model.login_user(conn, u, p)
                        if ok:
                            st.session_state.update(
                                logged_in=True, username=user["username"], role=user["role"],
                                full_name=user["full_name"] or user["username"], page="Inbox")
                            st.rerun()
                        else:
                            st.error(msg)
                st.caption("Demo: **admin / admin123**, sarah.lee / password1, "
                           "james.okafor / password1")
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
#  SIDEBAR
# ===========================================================================
NAV = {"Inbox": "💬  Inbox", "Dashboard": "📊  Dashboard",
       "My Performance": "🏅  My Performance", "Customers": "👥  Customers",
       "Canned Replies": "📋  Canned Replies", "Knowledge": "📚  Knowledge",
       "AI Copilot": "🤖  AI Copilot", "Team Admin": "🛠️  Team Admin"}


def sidebar():
    with st.sidebar:
        st.markdown(f"<div style='font-size:1.45rem;font-weight:800;color:#4f46e5;"
                    f"padding:2px 0 10px'>💬 {APP_NAME}</div>", unsafe_allow_html=True)
        keys = [k for k in NAV if k != "Team Admin" or st.session_state.role in ("admin", "supervisor")]
        current = st.session_state.page if st.session_state.page in keys else keys[0]
        st.session_state.page = st.radio("nav", keys, index=keys.index(current),
                                         format_func=lambda k: NAV[k], label_visibility="collapsed")
        st.markdown("<hr style='border-color:#e9ebf0'>", unsafe_allow_html=True)
        online = ai_assistant.is_online_available()
        st.markdown(
            f"<div style='display:flex;gap:9px;align-items:center'>"
            f"{avatar(st.session_state.full_name, 32)}"
            f"<div><div style='font-weight:600;font-size:.85rem'>{st.session_state.full_name}</div>"
            f"<div class='small'>{st.session_state.role} · {'🟢 AI' if online else '🟡 AI'}</div>"
            f"</div></div>", unsafe_allow_html=True)
        st.write("")
        if st.button("Log out", use_container_width=True):
            for k in ("logged_in", "username", "role", "full_name", "active_ticket"):
                st.session_state[k] = False if k == "logged_in" else None
            st.rerun()


def page_title(title, sub=""):
    st.markdown(f"<div class='title'>{title}</div>"
                + (f"<div class='sub'>{sub}</div>" if sub else ""), unsafe_allow_html=True)


# ===========================================================================
#  INBOX  — clean 2-pane (queue | conversation with tabs)
# ===========================================================================
def last_messages():
    df = pd.read_sql("SELECT ticket_id, body, MAX(sent_at) AS last_at FROM conversations "
                     "GROUP BY ticket_id", conn)
    return {int(r["ticket_id"]): (r["body"], r["last_at"]) for _, r in df.iterrows()}


def pick_next(df):
    openq = df[df["status"].isin(["Open", "Pending", "On Hold"])].copy()
    if openq.empty:
        st.toast("No open tickets 🎉"); return
    openq["r"] = openq["priority"].map(PRANK).fillna(9)
    openq = openq.sort_values(["r", "sla_due_at"])
    st.session_state.active_ticket = int(openq.iloc[0]["ticket_id"])


def page_inbox():
    page_title("Inbox", "Your unified queue across every channel")
    with st.popover("🔍 Filters", use_container_width=False):
        status = st.selectbox("Status", ["All"] + tickets_model.STATUSES)
        priority = st.selectbox("Priority", ["All"] + tickets_model.PRIORITIES)
        channel = st.selectbox("Channel", ["All"] + tickets_model.CHANNELS)
        agents = ["All"] + [u["username"] for u in users_model.get_all_users(conn)]
        agent = st.selectbox("Agent", agents)
        search = st.text_input("Search subject / customer / order")
    df = tickets_model.filter_tickets(conn, status=status, priority=priority,
                                      channel=channel, agent=agent, search=search)
    lastmsg = last_messages()

    q, main = st.columns([1, 2.6], gap="large")
    with q:
        top = st.columns([2, 1, 1])
        top[0].markdown(f"<div class='small' style='padding-top:8px'><b>{len(df)}</b> "
                        f"conversations</div>", unsafe_allow_html=True)
        if top[1].button("＋", use_container_width=True, help="New ticket"):
            st.session_state.active_ticket = "NEW"; st.rerun()
        if top[2].button("⚡", use_container_width=True, help="Pick next urgent"):
            pick_next(df); st.rerun()
        with st.container(height=660, border=False):
            render_queue(df, lastmsg)

    with main:
        if st.session_state.active_ticket == "NEW":
            with st.container(border=True):
                new_ticket_form()
        elif st.session_state.active_ticket:
            render_conversation(int(st.session_state.active_ticket), lastmsg)
        else:
            with st.container(border=True):
                st.write("")
                st.markdown("<div style='text-align:center;color:#9aa0ab;padding:48px 0'>"
                            "💬<br><b style='color:#6b7280'>Select a conversation</b><br>"
                            "<span class='small'>Pick one from the queue, or hit ⚡ for the "
                            "most urgent.</span></div>", unsafe_allow_html=True)
                st.write("")


def render_queue(df, lastmsg):
    for _, t in df.head(60).iterrows():
        tid = int(t["ticket_id"])
        icon = CHANNEL_ICONS.get(t["channel"], "•")
        dot = DOT.get(t["priority"], "⚪")
        sla_txt, _ = sla_badge(t["sla_due_at"], t["status"])
        if str(st.session_state.active_ticket) == str(tid):
            st.markdown(
                f"<div class='qsel'><div class='nm'>{icon} {t['customer_name']} {dot}</div>"
                f"<div class='mt'>#{tid} · {t['status']} · {sla_txt}</div></div>",
                unsafe_allow_html=True)
        else:
            if st.button(f"{icon}  {t['customer_name']}  {dot}\n\n#{tid} · {sla_txt}",
                         key=f"q_{tid}", use_container_width=True):
                st.session_state.active_ticket = tid; st.rerun()


def render_conversation(tid, lastmsg):
    t = tickets_model.get_ticket(conn, tid)
    if t is None:
        st.warning("Ticket not found."); return
    t = dict(t)
    cust = customers_model.get_customer(conn, t["customer_id"])
    email = dict(cust)["email"] if cust is not None else ""

    # header
    with st.container(border=True):
        hc = st.columns([0.6, 5, 1.1])
        hc[0].markdown(avatar(t["customer_name"], 42), unsafe_allow_html=True)
        sla_txt, sla_css = sla_badge(t["sla_due_at"], t["status"])
        hc[1].markdown(
            f"<div style='font-weight:700;font-size:1.05rem'>{t['customer_name']}</div>"
            f"<div class='small'>{CHANNEL_ICONS.get(t['channel'],'')} {t['channel']} · #{tid} "
            f"· {email}</div>", unsafe_allow_html=True)
        if hc[2].button("Close ✕", use_container_width=True):
            st.session_state.active_ticket = None; st.rerun()
        st.markdown(
            f"{pill(t['priority'], PRIORITY_COLORS)} {pill(t['status'], STATUS_COLORS)} "
            f"<span class='pill' style='background:{sla_css}'>{sla_txt}</span> "
            f"<span class='small'>· {t['subject']}</span>", unsafe_allow_html=True)

    tab_conv, tab_hist, tab_upd, tab_cust = st.tabs(
        ["💬 Conversation", "🕘 History", "✏️ Update", "👤 Customer"])
    with tab_conv:
        render_conv_tab(t, tid)
    with tab_hist:
        render_history(tid)
    with tab_upd:
        render_update(tid)
    with tab_cust:
        render_customer_tab(t)


def render_conv_tab(t, tid):
    thread_df = conv_model.get_thread(conn, tid, include_notes=True)
    user = st.session_state.username

    def fill(body):
        return canned_model.fill_placeholders(
            body, name=str(t["customer_name"]).split()[0],
            oid=t["order_ref"] or "your order", product=t["product"] or "your item")

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
        st.toast("Resolved", icon="✅")

    def _set_reply(text):
        st.session_state["reply_area"] = text; st.toast("Inserted", icon="✍️")

    def _draft():
        txt, mode = ai_assistant.draft_reply(conn, t, thread_df)
        st.session_state["reply_area"] = txt; st.toast(f"AI draft ready ({mode})", icon="✨")

    def _macro(m):
        conv_model.reply(conn, t, user, fill(m["body"]))
        log_event(tid, "macro", f"Quick action: {m['label']}")
        if m.get("status"):
            tickets_model.update_status(conn, tid, m["status"])
            log_event(tid, "status", f"Status → {m['status']}")
        if m.get("wrap"):
            tickets_model.update_fields(conn, tid, wrap_one=m["wrap"])
        st.toast("Quick action applied", icon="⚡")

    # thread
    with st.container(height=330, border=False):
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

    # sentiment coaching (subtle)
    inbound = thread_df[thread_df["direction"] == "Inbound"]
    last_in = inbound.iloc[-1]["body"] if len(inbound) else ""
    senti = insights.analyze_sentiment(last_in)
    st.markdown(f"<div class='mood' style='background:{MOOD_BG.get(senti['label'])}'>"
                f"{senti['emoji']} <b>{senti['label']} mood</b>"
                f"{' · ⚡ urgent' if senti['urgent'] else ''} — "
                f"{insights.recommend_tone(senti)}</div>", unsafe_allow_html=True)

    # composer
    st.text_area("Reply", key="reply_area", height=96, label_visibility="collapsed",
                 placeholder=f"Reply to {str(t['customer_name']).split()[0]} on {t['channel']}…")
    row = st.columns([1.1, 1.2, 1.2, 2.2, 1.1])
    row[0].button("Send", type="primary", use_container_width=True, on_click=_send)
    row[1].button("✨ AI draft", use_container_width=True, on_click=_draft)
    with row[2].popover("📋 Insert", use_container_width=True):
        ct, kt = st.tabs(["Canned", "Knowledge"])
        with ct:
            canned = canned_model.get_all(conn)
            match = canned[canned["category"].isin([t["category"], "Greeting", "Closing"])]
            for _, r in (match if not match.empty else canned).iterrows():
                st.button(f"➕ {r['title']}", key=f"can{r['canned_id']}", use_container_width=True,
                          on_click=_set_reply, args=(fill(r["body"]),))
        with kt:
            kq = st.text_input("Search KB", key="kbq", label_visibility="collapsed",
                               placeholder="Search articles…")
            for a in insights.search_kb(kq or t["category"]):
                st.button(f"➕ {a['title']}", key=f"kb{a['id']}", use_container_width=True,
                          on_click=_set_reply, args=(a["answer"],))
    row[3].markdown(f"<div style='text-align:right;color:#9aa0ab;font-size:.78rem;padding-top:8px'>"
                    f"{len(st.session_state.get('reply_area',''))} chars</div>", unsafe_allow_html=True)
    row[4].button("End", use_container_width=True, on_click=_end)

    with st.expander("⚡ Quick actions — one click sends a reply + updates the ticket"):
        macros = insights.suggest_actions(t["category"])
        for i in range(0, len(macros), 2):
            cc = st.columns(2)
            for j, m in enumerate(macros[i:i + 2]):
                cc[j].button(m["label"], key=f"macro{i+j}", use_container_width=True,
                             on_click=_macro, args=(m,))
        if st.button("🗒️ Add as internal note instead", use_container_width=True):
            _note(); st.rerun()


def render_history(tid):
    t = dict(tickets_model.get_ticket(conn, tid))
    rows = [("created", "Interaction opened", f"via {t['channel']}", t["customer_name"], t["created_at"])]
    for _, e in events_model.get_events(conn, tid).iterrows():
        rows.append((e["event_type"], e["event_type"].title(), e["detail"], e["actor"], e["created_at"]))
    if t.get("resolved_at"):
        rows.append(("resolved", "Resolved", f"Marked {t['status']}", "", t["resolved_at"]))
    rows.sort(key=lambda r: str(r[4]))
    st.caption("Full audit trail of this interaction.")
    for etype, label, detail, actor, when in rows:
        who = f" · {actor}" if actor else ""
        st.markdown(
            f"<div class='hrow'><div class='hi'>{EVENT_ICONS.get(etype,'•')}</div>"
            f"<div><b>{APP_NAME}{who}</b><br><span class='ht'>{when}</span><br>"
            f"<span class='hp'>{label}</span><br><span class='hd'>{detail}</span></div></div>",
            unsafe_allow_html=True)


def render_update(tid):
    t = dict(tickets_model.get_ticket(conn, tid))
    cust = customers_model.get_customer(conn, t["customer_id"])
    cust = dict(cust) if cust is not None else {}
    with st.form("update_panel"):
        a, b = st.columns(2)
        order = a.text_input("Order Number", value=t.get("order_ref") or "")
        track = b.text_input("Tracking Number", value=t.get("tracking_number") or "")
        c, d = st.columns(2)
        email = c.text_input("Email Address", value=cust.get("email", ""))
        phone = d.text_input("Phone Number", value=cust.get("phone", ""))
        e, f = st.columns(2)
        postcode = e.text_input("Postcode", value=t.get("postcode") or "")
        reason = f.selectbox("Reason For Contact", tickets_model.CATEGORIES,
                             index=tickets_model.CATEGORIES.index(t["category"])
                             if t["category"] in tickets_model.CATEGORIES else 0)
        g, h, i = st.columns(3)
        status = g.selectbox("Status", tickets_model.STATUSES,
                             index=tickets_model.STATUSES.index(t["status"])
                             if t["status"] in tickets_model.STATUSES else 0)
        priority = h.selectbox("Priority", tickets_model.PRIORITIES,
                               index=tickets_model.PRIORITIES.index(t["priority"])
                               if t["priority"] in tickets_model.PRIORITIES else 0)
        agent_list = [u["username"] for u in users_model.get_all_users(conn)]
        agent = i.selectbox("Assigned Agent", agent_list,
                            index=agent_list.index(t["assigned_agent"])
                            if t["assigned_agent"] in agent_list else 0)
        w1, w2 = st.columns(2)
        wrap1 = w1.text_input("Wrap One", value=t.get("wrap_one") or "", placeholder="Disposition…")
        wrap2 = w2.text_input("Wrap Two", value=t.get("wrap_two") or "", placeholder="Sub-disposition…")
        if st.form_submit_button("💾 Save changes", type="primary", use_container_width=True):
            tickets_model.update_fields(conn, tid, order_ref=order, tracking_number=track,
                                        postcode=postcode, category=reason, priority=priority,
                                        assigned_agent=agent, wrap_one=wrap1, wrap_two=wrap2)
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


def render_customer_tab(t):
    cust = customers_model.get_customer(conn, t["customer_id"])
    if cust is None:
        st.caption(t["customer_name"]); return
    cust = dict(cust)
    m = st.columns(4)
    m[0].metric("Loyalty", cust["loyalty_tier"])
    m[1].metric("Lifetime orders", int(cust["lifetime_orders"]))
    m[2].metric("Lifetime spend", f"£{cust['lifetime_spend_gbp']:,.0f}")
    m[3].metric("City", cust["city"])
    st.markdown(f"<span class='small'>✉️ {cust['email']} · 📞 {cust['phone']}</span>",
                unsafe_allow_html=True)
    st.markdown("**Previous interactions**")
    hist = tickets_model.tickets_for_customer(conn, int(cust["customer_id"]))
    st.dataframe(hist[["ticket_id", "channel", "category", "subject", "status", "created_at"]],
                 use_container_width=True, hide_index=True)


def new_ticket_form():
    page_title("New interaction")
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
        body = st.text_area("First message from customer")
        s, x = st.columns([1, 1])
        if s.form_submit_button("Create", type="primary", use_container_width=True):
            row = custs[custs["name"] == cust].iloc[0]
            tid = tickets_model.create_ticket(conn, int(row["customer_id"]), cust, chan, cat,
                                              subject, order_ref, "", pri, st.session_state.username)
            if body.strip():
                conv_model.add_message(conn, tid, int(row["customer_id"]), chan, "Inbound", cust, body, 0)
            log_event(tid, "created", f"Interaction created on {chan}")
            st.session_state.active_ticket = tid
            st.toast(f"Ticket #{tid} created", icon="✅"); st.rerun()
    if st.button("Cancel", use_container_width=True):
        st.session_state.active_ticket = None; st.rerun()


# ===========================================================================
#  MY PERFORMANCE
# ===========================================================================
def page_performance():
    page_title("My Performance", f"Personal scorecard for @{st.session_state.username}")
    me = st.session_state.username
    df = tickets_model.get_all_tickets(conn)
    open_states = ["Open", "Pending", "On Hold"]
    mine = df[df["assigned_agent"] == me]
    open_mine = mine[mine["status"].isin(open_states)]
    resolved_mine = mine[mine["status"].isin(["Resolved", "Closed"])]
    csat = pd.to_numeric(mine["csat_score"], errors="coerce").dropna()
    now = datetime.now(); at_risk = 0
    for _, r in open_mine.iterrows():
        try:
            if datetime.strptime(r["sla_due_at"], DT_FMT) < now:
                at_risk += 1
        except (ValueError, TypeError):
            pass
    c = st.columns(4)
    for col, lab, v, s in [
        (c[0], "Assigned to me", len(mine), f"{len(open_mine)} open"),
        (c[1], "Resolved by me", len(resolved_mine), "all time"),
        (c[2], "My CSAT", f"{round(csat.mean(),2) if len(csat) else '—'}/5", f"{len(csat)} ratings"),
        (c[3], "SLA at risk", at_risk, "open & overdue")]:
        col.markdown(f"<div class='kpi'><h3>{lab}</h3><div class='v'>{v}</div>"
                     f"<div class='s'>{s}</div></div>", unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.markdown("#### 🏆 Team leaderboard")
        rows = []
        for ag, g in df.groupby("assigned_agent"):
            cs = pd.to_numeric(g["csat_score"], errors="coerce").dropna()
            rows.append({"Agent": ag,
                         "Resolved": int(g["status"].isin(["Resolved", "Closed"]).sum()),
                         "Open": int(g["status"].isin(open_states).sum()),
                         "Avg CSAT": round(cs.mean(), 2) if len(cs) else None})
        lb = pd.DataFrame(rows).sort_values("Resolved", ascending=False)
        st.dataframe(lb, use_container_width=True, hide_index=True)
        st.bar_chart(lb.set_index("Agent")[["Resolved"]], color="#4f46e5", height=240)
    with right:
        st.markdown("#### 📋 My open queue")
        if open_mine.empty:
            st.success("All caught up — no open tickets! 🎉")
        for _, t in open_mine.head(12).iterrows():
            cc = st.columns([4, 1])
            txt, _ = sla_badge(t["sla_due_at"], t["status"])
            cc[0].markdown(f"**#{t['ticket_id']}** {t['subject'][:28]}  \n"
                           f"<span class='small'>{t['customer_name']} · {txt}</span>",
                           unsafe_allow_html=True)
            if cc[1].button("Open", key=f"perf{t['ticket_id']}", use_container_width=True):
                st.session_state.active_ticket = int(t["ticket_id"])
                st.session_state.page = "Inbox"; st.rerun()


# ===========================================================================
#  KNOWLEDGE
# ===========================================================================
def page_knowledge():
    page_title("Knowledge Base", "Search internal answers — also available inside any reply")
    q = st.text_input("🔍 Search", placeholder="e.g. refund, delivery, sizing")
    for a in (insights.search_kb(q) if q else insights.KB_ARTICLES):
        st.markdown(f"<div class='kbcard'><b>{a['title']}</b> "
                    f"<span class='pill' style='background:#eef0ff;color:#4f46e5'>{a['category']}</span>"
                    f"<div class='small' style='margin-top:6px'>{a['answer']}</div></div>",
                    unsafe_allow_html=True)


# ===========================================================================
#  DASHBOARD
# ===========================================================================
def page_dashboard():
    page_title("Dashboard", f"{datetime.now():%A %d %B %Y, %H:%M}")
    s = tickets_model.stats(conn)
    c = st.columns(5)
    for col, lab, v, sub in [
        (c[0], "Total tickets", s["total"], "all time"),
        (c[1], "Open", s["open"], "awaiting action"),
        (c[2], "SLA breaches", s["sla_breaches"], "needs attention" if s["sla_breaches"] else "on track"),
        (c[3], "Avg CSAT", f"{s['avg_csat']}/5" if s["avg_csat"] else "—", "satisfaction"),
        (c[4], "Resolution rate", f"{s['resolution_rate']}%", f"{s['resolved']} resolved")]:
        col.markdown(f"<div class='kpi'><h3>{lab}</h3><div class='v'>{v}</div>"
                     f"<div class='s'>{sub}</div></div>", unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("#### By status")
            st.bar_chart(tickets_model.count_by(conn, "status").set_index("status"), color="#4f46e5", height=230)
    with c2:
        with st.container(border=True):
            st.markdown("#### By channel")
            st.bar_chart(tickets_model.count_by(conn, "channel").set_index("channel"), color="#10b981", height=230)
    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            st.markdown("#### By category")
            st.bar_chart(tickets_model.count_by(conn, "category").set_index("category"), color="#f59e0b", height=230)
    with c4:
        with st.container(border=True):
            st.markdown("#### Agent workload")
            st.bar_chart(tickets_model.count_by(conn, "assigned_agent").set_index("assigned_agent"),
                         color="#ec4899", height=230)


def page_customers():
    page_title("Customers")
    term = st.text_input("🔍 Search by name, email or city")
    df = (customers_model.search_customers(conn, term) if term else customers_model.get_all_customers(conn))
    cols = st.columns([2, 1], gap="large")
    with cols[0]:
        st.dataframe(df, use_container_width=True, height=440, hide_index=True)
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


def page_canned():
    page_title("Canned Replies", "Use {name}, {oid}, {product} — they auto-fill on insert")
    df = canned_model.get_all(conn)
    st.dataframe(df, use_container_width=True, hide_index=True, height=320)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("**➕ Add**")
            with st.form("add_canned"):
                cat = st.text_input("Category"); title = st.text_input("Title")
                body = st.text_area("Body")
                if st.form_submit_button("Save", use_container_width=True):
                    canned_model.add(conn, cat, title, body); st.toast("Saved", icon="✅"); st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown("**🗑️ Delete**")
            if not df.empty:
                pick = st.selectbox("Choose", [f"{r['canned_id']} · {r['title']}" for _, r in df.iterrows()])
                if st.button("Delete", use_container_width=True):
                    canned_model.delete(conn, int(pick.split(" · ")[0])); st.toast("Deleted", icon="🗑️"); st.rerun()


def page_ai():
    page_title("AI Copilot")
    online = ai_assistant.is_online_available()
    st.caption("Connected to OpenAI." if online else "Offline mode — add an OpenAI key (README).")
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
    page_title("Team Admin", "Manage agent accounts — supervisors & admins only")
    rows = users_model.get_all_users(conn)
    df = pd.DataFrame([{"id": r["id"], "username": r["username"], "full_name": r["full_name"],
                        "role": r["role"], "created_at": r["created_at"]} for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)
    c1, c2, c3 = st.columns(3, gap="large")
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
    {"Inbox": page_inbox, "Dashboard": page_dashboard, "My Performance": page_performance,
     "Customers": page_customers, "Canned Replies": page_canned, "Knowledge": page_knowledge,
     "AI Copilot": page_ai, "Team Admin": page_team_admin}.get(
        st.session_state.page, page_inbox)()


if __name__ == "__main__":
    main()
