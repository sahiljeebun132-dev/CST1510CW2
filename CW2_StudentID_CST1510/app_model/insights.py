"""
insights.py
-----------
Agent "superpower" helpers that work fully offline (no API needed):

  * analyze_sentiment()  — mood + urgency of a customer message
  * recommend_tone()     — coaching tip on how to reply
  * search_kb()          — searchable internal knowledge base
  * suggest_actions()    — one-click quick-action macros per ticket category

These power the sentiment meter, the Knowledge panel and the Quick-action
buttons in the conversation view.
"""

import re

# ---------------------------------------------------------------------------
# Sentiment / urgency (lightweight lexicon model)
# ---------------------------------------------------------------------------
_NEG = {"angry", "annoyed", "annoying", "terrible", "awful", "worst", "useless",
        "disappointed", "disappointing", "unacceptable", "ridiculous", "frustrated",
        "frustrating", "rubbish", "horrible", "poor", "scam", "never", "still not",
        "no reply", "ignored", "fed up", "complaint", "refund", "broken", "faulty",
        "damaged", "late", "missing", "wrong", "cancel", "disgusting", "hate"}
_POS = {"thanks", "thank you", "appreciate", "great", "perfect", "brilliant",
        "amazing", "lovely", "happy", "pleased", "awesome", "excellent", "good",
        "cheers", "helpful", "love", "fantastic", "sorted"}
_URGENT = {"urgent", "asap", "immediately", "now", "right now", "emergency",
           "today", "deadline", "still waiting", "third time", "again"}


def analyze_sentiment(text):
    """Return dict: label, emoji, score, urgent (bool)."""
    t = f" {str(text).lower()} "
    neg = sum(1 for w in _NEG if w in t)
    pos = sum(1 for w in _POS if w in t)
    urgent = any(w in t for w in _URGENT)
    score = pos - neg
    if score <= -1:
        label, emoji = "Negative", "😠"
    elif score >= 1:
        label, emoji = "Positive", "😊"
    else:
        label, emoji = "Neutral", "😐"
    return {"label": label, "emoji": emoji, "score": score, "urgent": urgent}


def recommend_tone(sentiment):
    """Coaching tip based on the detected mood."""
    if sentiment["label"] == "Negative":
        tip = ("Lead with empathy and a genuine apology, acknowledge the "
               "frustration, then give one clear next step and a timeframe.")
    elif sentiment["label"] == "Positive":
        tip = ("Match their friendly energy, keep it warm and concise, and "
               "confirm anything outstanding.")
    else:
        tip = ("Be clear, friendly and specific — confirm what you'll do and "
               "when they'll hear back.")
    if sentiment["urgent"]:
        tip += " ⚡ They're in a hurry — prioritise speed and reassure first."
    return tip


# ---------------------------------------------------------------------------
# Knowledge base (internal FAQ the agent can search + insert)
# ---------------------------------------------------------------------------
KB_ARTICLES = [
    {"id": 1, "title": "Returns policy & window",
     "category": "Returns & Refunds",
     "answer": "Customers have 28 days from delivery to return unworn items "
               "with tags. Free returns via any collection point using the "
               "prepaid label in their account under Orders > Return."},
    {"id": 2, "title": "Refund timelines",
     "category": "Returns & Refunds",
     "answer": "Refunds are issued within 3-5 working days of the warehouse "
               "receiving the return. Card refunds can take a further 1-3 days "
               "to appear depending on the bank."},
    {"id": 3, "title": "Delivery times by service",
     "category": "Delivery Issue",
     "answer": "Standard 3-5 working days, Express 1-2 days, Next-day if "
               "ordered before 9pm. Tracking link is in the dispatch email."},
    {"id": 4, "title": "Lost / not-received parcel",
     "category": "Delivery Issue",
     "answer": "If tracking shows delivered but the parcel is missing, open a "
               "courier investigation (up to 24h). If confirmed lost we offer a "
               "free replacement or full refund."},
    {"id": 5, "title": "Sizing & fit guidance",
     "category": "Sizing & Fit",
     "answer": "Most trainers run true to size; some customers size up half a "
               "size for a roomier fit. The size guide is on each product page."},
    {"id": 6, "title": "Faulty item process",
     "category": "Faulty Item",
     "answer": "For faulty goods we arrange a free replacement plus a prepaid "
               "return label for the faulty item — the customer pays nothing."},
    {"id": 7, "title": "Duplicate charge / payment",
     "category": "Payment",
     "answer": "A duplicate authorisation usually drops off within 3-5 working "
               "days. If an actual double charge settled, we refund the "
               "duplicate immediately."},
    {"id": 8, "title": "Password reset / login",
     "category": "Account",
     "answer": "Trigger a fresh reset email; the link is valid for 30 minutes. "
               "Ask the customer to check spam if it doesn't arrive."},
    {"id": 9, "title": "Student discount",
     "category": "Promo / Discount",
     "answer": "Student discount needs a verified Student Beans account; once "
               "verified the code applies automatically at checkout."},
    {"id": 10, "title": "Restock notifications",
     "category": "Product Question",
     "answer": "We can't guarantee restock dates, but customers can tap 'Notify "
               "me' on the product page to be emailed when stock returns."},
]


def search_kb(query, k=5):
    """Keyword search over the knowledge base. Returns ranked articles."""
    q = [w for w in re.findall(r"[a-z]+", str(query).lower()) if len(w) > 2]
    if not q:
        return KB_ARTICLES[:k]
    scored = []
    for a in KB_ARTICLES:
        title = a["title"].lower()
        body = a["answer"].lower()
        score = sum(2 for w in q if w in title) + sum(1 for w in q if w in body)
        if a["category"].lower() in str(query).lower():
            score += 2
        if score:
            scored.append((score, a))
    scored.sort(key=lambda x: -x[0])
    return [a for _, a in scored[:k]] or KB_ARTICLES[:k]


# ---------------------------------------------------------------------------
# Quick-action macros (one click = templated reply + status/wrap update)
# ---------------------------------------------------------------------------
# Each macro: label, body (with {name}/{oid}/{product}), optional status + wrap.
_GENERIC = [
    {"label": "🙏 Acknowledge & reassure",
     "body": "Hi {name}, thanks so much for getting in touch — I completely "
             "understand and I'm on it right now. I'll have an update for you "
             "shortly.",
     "status": None, "wrap": None},
    {"label": "✅ Resolve & request CSAT",
     "body": "Glad I could help, {name}! I'll mark this as resolved. If you have "
             "a moment, a quick rating of your experience would mean a lot. "
             "Thanks for choosing us! 👟",
     "status": "Resolved", "wrap": "Resolved"},
]

_BY_CATEGORY = {
    "Order Status": [{"label": "📦 Share tracking update",
                      "body": "Hi {name}, good news — order {oid} is on its way! "
                              "You can follow it with the tracking link in your "
                              "dispatch email. Anything else I can help with?",
                      "status": "Pending", "wrap": "Order Status"}],
    "Delivery Issue": [{"label": "🚚 Open courier investigation",
                        "body": "So sorry {name}. I've opened an investigation "
                                "with the courier for order {oid} and we'll "
                                "update you within 24 hours — we'll sort a "
                                "replacement or refund if it's confirmed lost.",
                        "status": "On Hold", "wrap": "Delivery"}],
    "Returns & Refunds": [{"label": "↩️ Send return instructions",
                           "body": "No problem {name}! Head to Account > Orders > "
                                   "Return, print the prepaid label and drop it "
                                   "at any collection point. The {product} is "
                                   "fully eligible.",
                           "status": "Pending", "wrap": "Returns"},
                          {"label": "💷 Confirm refund timeline",
                           "body": "Thanks {name} — refunds land within 3-5 "
                                   "working days once your return reaches us. "
                                   "I can see yours is being processed now.",
                           "status": "Pending", "wrap": "Refund"}],
    "Faulty Item": [{"label": "🔧 Offer free replacement",
                     "body": "I'm really sorry the {product} arrived faulty, "
                             "{name}. I've arranged a free replacement and a "
                             "prepaid return label — no cost to you.",
                     "status": "Pending", "wrap": "Faulty"}],
    "Payment": [{"label": "💳 Release duplicate charge",
                 "body": "Thanks for flagging {name}. I can see a duplicate "
                         "authorisation on order {oid} — I've released it and it "
                         "should drop off within 3-5 working days.",
                 "status": "Resolved", "wrap": "Payment"}],
    "Account": [{"label": "🔑 Trigger password reset",
                 "body": "Let's get you back in {name}. I've sent a fresh "
                         "password reset — please check your inbox and spam. The "
                         "link is valid for 30 minutes.",
                 "status": "Pending", "wrap": "Account"}],
    "Promo / Discount": [{"label": "🏷️ Fix discount",
                          "body": "Thanks {name}! Student discounts need a "
                                  "verified Student Beans account. I've also "
                                  "added a one-time 10% code to your account.",
                          "status": "Resolved", "wrap": "Promo"}],
    "Sizing & Fit": [{"label": "📏 Share size guide",
                      "body": "Great choice {name}! The {product} runs true to "
                              "size — some customers size up half a size for a "
                              "roomier fit. Full size guide is on the product "
                              "page.",
                      "status": "Pending", "wrap": "Sizing"}],
    "Complaint": [{"label": "🚩 Apologise & escalate",
                   "body": "I'm genuinely sorry for the experience {name}. I've "
                           "escalated order {oid} to a senior agent as priority "
                           "and added a goodwill voucher to your account.",
                   "status": "On Hold", "wrap": "Escalated"}],
}


def suggest_actions(category):
    """Return the quick-action macros relevant to a ticket's category."""
    return _BY_CATEGORY.get(category, []) + _GENERIC
