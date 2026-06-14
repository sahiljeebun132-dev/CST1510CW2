"""
ai_assistant.py
---------------
AI co-pilot for agents (CW2 Video 08/09).

Provides two capabilities, each with an automatic ONLINE (OpenAI) path and an
OFFLINE fallback so everything still works with no API key:

  * answer()       — answer questions about tickets/metrics (the Copilot page)
  * draft_reply()  — write a ready-to-send customer reply for the open ticket

How to enable online mode (any ONE of these):
  * env var OPENAI_API_KEY
  * OPENAI_API_KEY in Streamlit secrets (Streamlit Community Cloud)
  * a .openai_key file in the project root
Set OPENAI_BASE_URL for a free/compatible endpoint (Video 09).
"""

import os
import re

from . import tickets as tickets_model
from . import customers as customers_model  # noqa: F401 (handy for extensions)
from . import insights

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "You are Relay Copilot, an assistant embedded in a customer-service "
    "platform for a streetwear & footwear retailer. You help support agents by "
    "answering questions about tickets, customers and metrics, suggesting "
    "replies, and summarising conversations. Be concise, friendly and "
    "professional. When given DATA CONTEXT, base your answer on it and quote "
    "the relevant numbers."
)

REPLY_PROMPT = (
    "You are an expert customer-service agent for a streetwear & footwear "
    "retailer. Write a warm, concise, professional reply to the customer's "
    "latest message. Acknowledge their issue, give a clear next step and a "
    "timeframe, and sign off politely. Do not invent order details you weren't "
    "given. 2-5 sentences."
)


# --------------------------------------------------------------------------
# Key / client discovery
# --------------------------------------------------------------------------
def find_api_key(explicit=None):
    if explicit:
        return explicit
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    key_file = os.path.join(root, ".openai_key")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            k = f.read().strip()
            if k:
                return k
    return None


def _base_url():
    base = os.environ.get("OPENAI_BASE_URL")
    if base:
        return base
    try:
        import streamlit as st
        if "OPENAI_BASE_URL" in st.secrets:
            return st.secrets["OPENAI_BASE_URL"]
    except Exception:
        pass
    return None


def is_online_available(explicit_key=None) -> bool:
    if find_api_key(explicit_key) is None:
        return False
    try:
        import openai  # noqa: F401
        return True
    except ImportError:
        return False


def _client(api_key):
    from openai import OpenAI
    kwargs = {"api_key": api_key}
    base = _base_url()
    if base:
        kwargs["base_url"] = base
    return OpenAI(**kwargs)


# --------------------------------------------------------------------------
# Live data context for the Copilot
# --------------------------------------------------------------------------
def build_context(conn) -> str:
    s = tickets_model.stats(conn)
    by_status = tickets_model.count_by(conn, "status")
    by_channel = tickets_model.count_by(conn, "channel")
    by_cat = tickets_model.count_by(conn, "category")

    def kv(df):
        return ", ".join(f"{r.iloc[0]}: {int(r['count'])}" for _, r in df.iterrows())

    return "\n".join([
        "DATA CONTEXT (live from the Relay database):",
        f"- Total tickets: {s['total']}",
        f"- Open (Open/Pending/On Hold): {s['open']}",
        f"- Resolved/Closed: {s['resolved']} (resolution rate {s['resolution_rate']}%)",
        f"- SLA breaches right now: {s['sla_breaches']}",
        f"- Average CSAT: {s['avg_csat']}",
        f"- Average first response time (mins): {s['avg_first_response_mins']}",
        f"- Tickets by status: {kv(by_status)}",
        f"- Tickets by channel: {kv(by_channel)}",
        f"- Tickets by category: {kv(by_cat)}",
    ])


# --------------------------------------------------------------------------
# Q&A Copilot
# --------------------------------------------------------------------------
def _answer_online(question, context, history, api_key):
    client = _client(api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": context}]
    for role, content in (history or [])[-6:]:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})
    resp = client.chat.completions.create(
        model=DEFAULT_MODEL, messages=messages, temperature=0.4, max_tokens=400)
    return resp.choices[0].message.content.strip()


def _answer_offline(question, conn):
    q = question.lower()
    s = tickets_model.stats(conn)

    def top(column, n=3):
        df = tickets_model.count_by(conn, column).head(n)
        return ", ".join(f"{r.iloc[0]} ({int(r['count'])})" for _, r in df.iterrows())

    if re.search(r"\b(sla|breach|overdue|late)\b", q):
        return (f"There are **{s['sla_breaches']}** tickets currently breaching "
                f"SLA. Work Urgent/High first — they have the tightest 2-4h targets.")
    if re.search(r"\b(open|backlog|queue|waiting|outstanding)\b", q):
        return (f"You have **{s['open']}** open tickets out of {s['total']}. "
                f"Top categories: {top('category')}.")
    if re.search(r"\b(csat|satisfaction|happy|rating)\b", q):
        return (f"Average CSAT is **{s['avg_csat']}/5**. Focus on Complaint and "
                f"Faulty Item categories to lift it.")
    if re.search(r"\b(response|frt|first reply|speed|fast)\b", q):
        return (f"Average first response time is "
                f"**{s['avg_first_response_mins']} minutes**. Canned replies and "
                f"quick-actions bring this down fastest.")
    if re.search(r"\b(channel|email|chat|whatsapp|instagram|social)\b", q):
        return f"Busiest channels: {top('channel')}."
    if re.search(r"\b(category|topic|reason|about|type)\b", q):
        return f"Most common categories: {top('category', 5)}."
    if re.search(r"\b(resolve|resolved|closed|done|rate)\b", q):
        return (f"You've resolved **{s['resolved']}** tickets — a resolution "
                f"rate of **{s['resolution_rate']}%**.")
    if re.search(r"\b(summar|overview|status|how are we|today)\b", q):
        return (f"**Today at a glance:** {s['total']} total, {s['open']} open, "
                f"{s['sla_breaches']} breaching SLA, CSAT {s['avg_csat']}/5, avg "
                f"first response {s['avg_first_response_mins']} mins. Top category: "
                f"{top('category', 1)}.")
    return (f"Snapshot: {s['total']} tickets, {s['open']} open, "
            f"{s['sla_breaches']} breaching SLA, CSAT {s['avg_csat']}/5. Ask about "
            f"SLA, channels, categories, CSAT or response times.")


def answer(conn, question, history=None, api_key=None):
    """Return (reply_text, mode) where mode is 'online' or 'offline'."""
    key = find_api_key(api_key)
    if key:
        try:
            import openai  # noqa: F401
            return _answer_online(question, build_context(conn), history, key), "online"
        except Exception as e:
            return (f"{_answer_offline(question, conn)}\n\n_(Online AI unavailable: "
                    f"{e}. Offline answer shown.)_", "offline")
    return _answer_offline(question, conn), "offline"


# --------------------------------------------------------------------------
# Draft a customer-facing reply for the open ticket  (the ✨ Draft button)
# --------------------------------------------------------------------------
def _thread_text(thread_df, limit=8):
    lines = []
    for _, m in thread_df.tail(limit).iterrows():
        if m["is_internal_note"]:
            continue
        who = "Customer" if m["direction"] == "Inbound" else "Agent"
        lines.append(f"{who}: {m['body']}")
    return "\n".join(lines)


def _last_inbound(thread_df):
    inbound = thread_df[thread_df["direction"] == "Inbound"]
    return inbound.iloc[-1]["body"] if len(inbound) else ""


def draft_reply(conn, ticket, thread_df, api_key=None):
    """
    Return (draft_text, mode). Writes a ready-to-edit reply to the customer.
    Online uses OpenAI; offline composes a smart template from the ticket
    context, detected sentiment and the matching canned reply.
    """
    name = str(ticket["customer_name"]).split()[0]
    oid = ticket.get("order_ref") or "your order"
    product = ticket.get("product") or "your item"
    last = _last_inbound(thread_df)
    sentiment = insights.analyze_sentiment(last)

    key = find_api_key(api_key)
    if key:
        try:
            client = _client(key)
            ctx = (f"Ticket category: {ticket['category']}. Channel: "
                   f"{ticket['channel']}. Order: {oid}. Product: {product}. "
                   f"Customer first name: {name}. Detected customer mood: "
                   f"{sentiment['label']}.\n\nConversation so far:\n"
                   f"{_thread_text(thread_df)}")
            resp = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "system", "content": REPLY_PROMPT},
                          {"role": "user", "content": ctx}],
                temperature=0.6, max_tokens=220)
            return resp.choices[0].message.content.strip(), "online"
        except Exception:
            pass  # fall through to offline

    # --- offline smart template -------------------------------------------
    actions = insights.suggest_actions(ticket["category"])
    base = actions[0]["body"] if actions else (
        "Hi {name}, thanks for getting in touch — I'm looking into this now and "
        "will update you shortly.")
    body = base.replace("{name}", name).replace("{oid}", oid).replace(
        "{product}", product)
    if sentiment["label"] == "Negative":
        body = (f"Hi {name}, I'm really sorry for the trouble — I completely "
                f"understand the frustration. ") + body.split(", ", 1)[-1]
    return body, "offline"
