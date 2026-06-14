"""
ai_assistant.py
---------------
AI co-pilot for agents (CW2 Video 08/09).

Two modes, chosen automatically:

  1. ONLINE  - if an OpenAI-compatible API key is available, the assistant
     calls the Chat Completions API (gpt-4o-mini by default) with live
     statistics from the database injected as context.

  2. OFFLINE - if no key/library is available (or the call fails), a built-in
     rule-based assistant answers using the same database context. This means
     the assistant ALWAYS works on demo day, with no key required.

How to enable online mode (any ONE of these):
  * set the environment variable  OPENAI_API_KEY
  * add OPENAI_API_KEY to Streamlit secrets (Streamlit Community Cloud)
  * create a file  .openai_key  in the project root containing the key
  * pass api_key=... to answer()

You can also point at a free / compatible endpoint by setting OPENAI_BASE_URL
(e.g. an OpenRouter or local proxy URL) — see Video 09.
"""

import os
import re

from . import tickets as tickets_model
from . import customers as customers_model  # noqa: F401 (handy for extensions)

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "You are HelpHub Copilot, an assistant embedded in a customer-service "
    "platform for a streetwear & footwear retailer. You help support agents by "
    "answering questions about tickets, customers and metrics, suggesting "
    "replies, and summarising conversations. Be concise, friendly and "
    "professional. When given DATA CONTEXT, base your answer on it and quote "
    "the relevant numbers."
)


# --------------------------------------------------------------------------
# Key / client discovery
# --------------------------------------------------------------------------
def find_api_key(explicit=None):
    if explicit:
        return explicit
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    # Streamlit Community Cloud secrets (soft import so the model layer does
    # not hard-depend on streamlit)
    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    # optional key file next to the project root
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


# --------------------------------------------------------------------------
# Live context pulled from the database (so answers are grounded in real data)
# --------------------------------------------------------------------------
def build_context(conn) -> str:
    s = tickets_model.stats(conn)
    by_status = tickets_model.count_by(conn, "status")
    by_channel = tickets_model.count_by(conn, "channel")
    by_cat = tickets_model.count_by(conn, "category")

    def kv(df):
        return ", ".join(f"{r.iloc[0]}: {int(r['count'])}"
                         for _, r in df.iterrows())

    lines = [
        "DATA CONTEXT (live from the HelpHub database):",
        f"- Total tickets: {s['total']}",
        f"- Open (Open/Pending/On Hold): {s['open']}",
        f"- Resolved/Closed: {s['resolved']} (resolution rate "
        f"{s['resolution_rate']}%)",
        f"- SLA breaches right now: {s['sla_breaches']}",
        f"- Average CSAT: {s['avg_csat']}",
        f"- Average first response time (mins): "
        f"{s['avg_first_response_mins']}",
        f"- Tickets by status: {kv(by_status)}",
        f"- Tickets by channel: {kv(by_channel)}",
        f"- Tickets by category: {kv(by_cat)}",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Online path: OpenAI Chat Completions
# --------------------------------------------------------------------------
def _answer_online(question, context, history, api_key):
    from openai import OpenAI

    kwargs = {"api_key": api_key}
    base = _base_url()
    if base:
        kwargs["base_url"] = base
    client = OpenAI(**kwargs)

    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": context}]
    for role, content in (history or [])[-6:]:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})

    resp = client.chat.completions.create(
        model=DEFAULT_MODEL, messages=messages, temperature=0.4, max_tokens=400)
    return resp.choices[0].message.content.strip()


# --------------------------------------------------------------------------
# Offline path: rule-based engine over the same data
# --------------------------------------------------------------------------
def _answer_offline(question, conn):
    q = question.lower()
    s = tickets_model.stats(conn)

    def top(column, n=3):
        df = tickets_model.count_by(conn, column).head(n)
        return ", ".join(f"{r.iloc[0]} ({int(r['count'])})"
                         for _, r in df.iterrows())

    if re.search(r"\b(sla|breach|overdue|late)\b", q):
        return (f"There are **{s['sla_breaches']}** tickets currently breaching "
                f"SLA. Prioritise Urgent/High tickets first — they have the "
                f"tightest 2-4 hour targets. Filter the inbox by Priority = "
                f"Urgent to clear them.")
    if re.search(r"\b(open|backlog|queue|waiting|outstanding)\b", q):
        return (f"You have **{s['open']}** open tickets in the queue out of "
                f"{s['total']} total. Top categories right now: "
                f"{top('category')}.")
    if re.search(r"\b(csat|satisfaction|happy|rating)\b", q):
        return (f"Average CSAT is **{s['avg_csat']}/5**. To lift it, focus on "
                f"the Complaint and Faulty Item categories where sentiment "
                f"tends to be most negative.")
    if re.search(r"\b(response|frt|first reply|speed|fast)\b", q):
        return (f"Average first response time is "
                f"**{s['avg_first_response_mins']} minutes**. Using canned "
                f"replies for common questions is the quickest way to bring "
                f"this down.")
    if re.search(r"\b(channel|email|chat|whatsapp|instagram|social)\b", q):
        return (f"Busiest channels: {top('channel')}. Live chat and email "
                f"usually carry the bulk of volume.")
    if re.search(r"\b(category|topic|reason|about|type)\b", q):
        return f"Most common ticket categories: {top('category', 5)}."
    if re.search(r"\b(resolve|resolved|closed|done|rate)\b", q):
        return (f"You've resolved **{s['resolved']}** tickets — a resolution "
                f"rate of **{s['resolution_rate']}%**.")
    if re.search(r"\b(priorit|urgent|high)\b", q):
        return (f"Priority breakdown: {top('priority', 4)}. Always work "
                f"Urgent -> High -> Medium -> Low.")
    if re.search(r"\b(summar|overview|status|how are we|today)\b", q):
        return (f"**Today at a glance:** {s['total']} total tickets, "
                f"{s['open']} open, {s['sla_breaches']} breaching SLA, "
                f"avg CSAT {s['avg_csat']}/5, avg first response "
                f"{s['avg_first_response_mins']} mins. Top category: "
                f"{top('category', 1)}.")
    if re.search(r"\b(reply|respond|draft|suggest|what.*say|template)\b", q):
        return ("For a quick, on-brand reply, open the ticket and use the "
                "**Canned replies** panel — pick the matching category and it "
                "auto-fills the customer's name, order number and product. "
                "Always acknowledge, give a clear next step, and a timeframe.")
    if re.search(r"\b(help|what can you|hello|hi|hey)\b", q):
        return ("Hi! I'm HelpHub Copilot. Ask me things like *'how many open "
                "tickets?'*, *'are we breaching SLA?'*, *'what's our CSAT?'*, "
                "*'busiest channel?'*, or *'give me a summary of today'*.")

    return (f"Here's the current snapshot: {s['total']} tickets, {s['open']} "
            f"open, {s['sla_breaches']} breaching SLA, CSAT {s['avg_csat']}/5. "
            f"Try asking about SLA, channels, categories, CSAT or response "
            f"times. (Tip: add an OpenAI key to unlock full natural-language "
            f"answers.)")


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------
def answer(conn, question, history=None, api_key=None):
    """
    Return (reply_text, mode) where mode is 'online' or 'offline'.
    Tries OpenAI first if configured; falls back to the rule engine on any error.
    """
    key = find_api_key(api_key)
    if key:
        try:
            import openai  # noqa: F401
            context = build_context(conn)
            return _answer_online(question, context, history, key), "online"
        except Exception as e:  # network down, bad key, lib missing, etc.
            fallback = _answer_offline(question, conn)
            return (f"{fallback}\n\n_(Online AI unavailable: {e}. "
                    f"Showing offline answer.)_", "offline")
    return _answer_offline(question, conn), "offline"
