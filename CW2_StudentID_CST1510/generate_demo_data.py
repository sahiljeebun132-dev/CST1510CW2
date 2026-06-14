"""
generate_demo_data.py
----------------------
Generates realistic customer-service demo data for the HelpHub platform and
writes it to the DATA/ folder as CSV files. These CSVs are later migrated into
the SQLite database by app_model/seed.py using pandas (CW2 rubric: pandas
CSV -> SQLite migration).

Run once:  python generate_demo_data.py
"""

import csv
import os
import random
from datetime import datetime, timedelta

random.seed(1510)  # deterministic output so the demo always looks the same

DATA_DIR = os.path.join(os.path.dirname(__file__), "DATA")
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------------------------------------------------------
# Reference data (themed around a streetwear / footwear retailer, like Gnatta's
# real client Footasylum)
# ----------------------------------------------------------------------------
FIRST_NAMES = ["Aisha", "Liam", "Sofia", "Noah", "Mia", "Ethan", "Zara", "Leo",
               "Maya", "Kai", "Ivy", "Omar", "Ella", "Finn", "Nia", "Jack",
               "Priya", "Tom", "Lola", "Reece", "Amara", "Dylan", "Hana", "Cole"]
LAST_NAMES = ["Khan", "Smith", "Rossi", "Brown", "Patel", "Jones", "Ahmed",
              "Taylor", "Walsh", "Nguyen", "Clarke", "Owusu", "Murphy", "Diaz",
              "Wright", "Begum", "Foster", "Reid", "Singh", "Mensah"]

CHANNELS = ["Email", "Live Chat", "WhatsApp", "Instagram DM", "X / Twitter",
            "Facebook", "Phone", "SMS"]
CHANNEL_WEIGHTS = [25, 22, 14, 12, 9, 7, 6, 5]

CATEGORIES = ["Order Status", "Returns & Refunds", "Delivery Issue",
              "Sizing & Fit", "Faulty Item", "Payment", "Account",
              "Promo / Discount", "Product Question", "Complaint"]

PRIORITIES = ["Low", "Medium", "High", "Urgent"]
PRIORITY_WEIGHTS = [30, 40, 22, 8]

STATUSES = ["Open", "Pending", "On Hold", "Resolved", "Closed"]
STATUS_WEIGHTS = [28, 18, 10, 26, 18]

SENTIMENTS = ["Positive", "Neutral", "Negative"]
SENTIMENT_WEIGHTS = [22, 48, 30]

AGENTS = ["admin", "sarah.lee", "james.okafor", "priya.nair", "tom.becker"]

CITIES = ["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Bristol",
          "Liverpool", "Sheffield", "Cardiff", "Newcastle", "Nottingham"]

PRODUCTS = ["Nike Air Max 90", "Adidas Samba OG", "New Balance 550",
            "Jordan 1 Low", "The North Face Puffer", "Carhartt Beanie",
            "Nike Tech Fleece Hoodie", "Adidas Gazelle", "Asics Gel-1130",
            "Stussy Tee", "On Cloud 5", "Puma Suede Classic"]

SUBJECT_TEMPLATES = {
    "Order Status": ["Where is my order {oid}?", "Order {oid} not updated",
                     "Tracking for {oid} not working"],
    "Returns & Refunds": ["Refund not received for {oid}",
                          "How do I return the {product}?",
                          "Return label missing for {oid}"],
    "Delivery Issue": ["{product} delivered to wrong address",
                       "Parcel {oid} says delivered but nothing arrived",
                       "Courier missed delivery for {oid}"],
    "Sizing & Fit": ["Is the {product} true to size?",
                     "{product} too small, need exchange",
                     "Size guide for {product}?"],
    "Faulty Item": ["{product} arrived damaged",
                    "Sole peeling on my {product}",
                    "Faulty stitching on {product}"],
    "Payment": ["Charged twice for order {oid}",
                "Payment failed but money taken",
                "Klarna issue on order {oid}"],
    "Account": ["Can't log into my account", "Reset password not working",
                "Update email on my account"],
    "Promo / Discount": ["Student discount not applying",
                         "Promo code REJECTED at checkout",
                         "Price dropped after I bought {product}"],
    "Product Question": ["Will the {product} be restocked?",
                         "Does the {product} come in black?",
                         "Material of the {product}?"],
    "Complaint": ["Terrible service on order {oid}",
                  "Still no reply after 3 days",
                  "Very disappointed with {product}"],
}

MESSAGE_TEMPLATES = {
    "Order Status": "Hi, I placed order {oid} on {ago} days ago and it still "
                    "hasn't shipped. Can you tell me what's happening?",
    "Returns & Refunds": "I sent back the {product} from order {oid} but I "
                         "still haven't seen my refund. Please help.",
    "Delivery Issue": "The tracking for {oid} says delivered but I never got "
                      "my {product}. I've checked with neighbours.",
    "Sizing & Fit": "Thinking of buying the {product} — do they run true to "
                    "size or should I size up?",
    "Faulty Item": "My {product} from order {oid} arrived with a fault. "
                   "Pretty annoyed, I'd like a replacement.",
    "Payment": "I think I've been charged twice for order {oid}. Can you "
               "check and refund the duplicate?",
    "Account": "I can't log into my account and the password reset email "
               "never arrives. Can you sort this out?",
    "Promo / Discount": "My student discount code won't apply at checkout "
                        "for the {product}. What am I doing wrong?",
    "Product Question": "Quick one — will the {product} be restocked any "
                        "time soon? Been waiting ages.",
    "Complaint": "This is the third time I'm messaging about order {oid} and "
                 "nobody has replied. Really not good enough.",
}

CANNED = [
    ("Greeting", "Welcome", "Hi {name}, thanks for getting in touch with HelpHub! "
     "I'm happy to help — could you share your order number so I can take a look?"),
    ("Order Status", "Order on the way", "Good news {name}! Order {oid} has been "
     "dispatched and is on its way. You can track it with the link in your "
     "confirmation email. Anything else I can help with?"),
    ("Returns & Refunds", "Refund timeline", "Thanks {name}. Refunds are processed "
     "within 3-5 working days once your return reaches our warehouse. I can see "
     "yours is being processed now — you'll get an email when it's complete."),
    ("Returns & Refunds", "How to return", "No problem {name}! Just head to your "
     "account > Orders > Return, print the prepaid label, and drop it at any "
     "collection point. The {product} is fully eligible for return."),
    ("Delivery Issue", "Lost parcel", "So sorry to hear that {name}. I've opened "
     "an investigation with the courier for order {oid}. We'll update you within "
     "24 hours and sort a replacement or refund if it's confirmed lost."),
    ("Sizing & Fit", "Fit advice", "Great choice {name}! The {product} tends to "
     "run true to size, though some customers size up half a size for a roomier "
     "fit. Our size guide is on the product page if that helps."),
    ("Faulty Item", "Faulty replacement", "I'm really sorry the {product} arrived "
     "faulty, {name}. I've arranged a free replacement and a prepaid return label "
     "for the faulty one — no need to pay anything."),
    ("Payment", "Duplicate charge", "Thanks for flagging {name}. I can see a "
     "duplicate authorisation on order {oid} — I've released it, and it should "
     "drop off your statement within 3-5 working days."),
    ("Account", "Password reset", "Let's get you back in {name}. I've triggered a "
     "fresh password reset — please check your inbox (and spam). The link is "
     "valid for 30 minutes."),
    ("Promo / Discount", "Discount fix", "Thanks {name}! Student discounts need a "
     "verified Student Beans account. Once verified, the code applies "
     "automatically at checkout. I've also added a one-time 10% code for you."),
    ("Closing", "Wrap up", "Glad I could help, {name}! Is there anything else I "
     "can do for you today? Thanks for choosing HelpHub. 👟"),
    ("Complaint", "Apology + escalate", "I'm genuinely sorry for the experience "
     "{name}. I've escalated order {oid} to a senior agent as priority and added "
     "a goodwill voucher to your account. We'll make this right."),
]


def rnd_dt(days_back_max=30):
    delta = timedelta(days=random.randint(0, days_back_max),
                      hours=random.randint(0, 23),
                      minutes=random.randint(0, 59))
    return datetime.now() - delta


def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------------------------------------------------------
# 1. customers.csv
# ----------------------------------------------------------------------------
customers = []
for cid in range(1, 41):
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    created = rnd_dt(720)
    customers.append({
        "customer_id": cid,
        "name": f"{fn} {ln}",
        "email": f"{fn.lower()}.{ln.lower()}{random.randint(1,99)}@example.com",
        "phone": f"+447{random.randint(100000000, 999999999)}",
        "city": random.choice(CITIES),
        "loyalty_tier": random.choices(["Bronze", "Silver", "Gold", "VIP"],
                                       weights=[40, 30, 20, 10])[0],
        "lifetime_orders": random.randint(1, 60),
        "lifetime_spend_gbp": round(random.uniform(40, 4200), 2),
        "created_at": fmt(created),
    })

with open(os.path.join(DATA_DIR, "customers.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(customers[0].keys()))
    w.writeheader()
    w.writerows(customers)

# ----------------------------------------------------------------------------
# 2. tickets.csv  (one ticket = one customer-service case)
# ----------------------------------------------------------------------------
tickets = []
for tid in range(1, 81):
    cust = random.choice(customers)
    cat = random.choice(CATEGORIES)
    product = random.choice(PRODUCTS)
    oid = f"FA{random.randint(100000, 999999)}"
    created = rnd_dt(30)
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
    priority = random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS)[0]
    # SLA target hours by priority
    sla_hours = {"Urgent": 2, "High": 4, "Medium": 12, "Low": 24}[priority]
    sla_due = created + timedelta(hours=sla_hours)
    first_response_mins = random.randint(2, 240)
    resolved_at = ""
    if status in ("Resolved", "Closed"):
        resolved_at = fmt(created + timedelta(hours=random.randint(1, 72)))
    subject = random.choice(SUBJECT_TEMPLATES[cat]).format(oid=oid, product=product)
    tickets.append({
        "ticket_id": tid,
        "customer_id": cust["customer_id"],
        "customer_name": cust["name"],
        "channel": random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0],
        "category": cat,
        "subject": subject,
        "order_ref": oid,
        "product": product,
        "priority": priority,
        "status": status,
        "sentiment": random.choices(SENTIMENTS, weights=SENTIMENT_WEIGHTS)[0],
        "assigned_agent": random.choice(AGENTS),
        "sla_target_hours": sla_hours,
        "sla_due_at": fmt(sla_due),
        "first_response_mins": first_response_mins,
        "csat_score": random.choice(["", "", "3", "4", "4", "5", "5", "2", "1"]),
        "created_at": fmt(created),
        "updated_at": fmt(created + timedelta(hours=random.randint(0, 48))),
        "resolved_at": resolved_at,
    })

with open(os.path.join(DATA_DIR, "tickets.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(tickets[0].keys()))
    w.writeheader()
    w.writerows(tickets)

# ----------------------------------------------------------------------------
# 3. conversations.csv  (individual messages within tickets - the inbox feed)
# ----------------------------------------------------------------------------
conversations = []
msg_id = 1
for t in tickets:
    cat = t["category"]
    base = datetime.strptime(t["created_at"], "%Y-%m-%d %H:%M:%S")
    # opening customer message
    opening = MESSAGE_TEMPLATES[cat].format(
        oid=t["order_ref"], product=t["product"], ago=random.randint(2, 9))
    conversations.append({
        "message_id": msg_id,
        "ticket_id": t["ticket_id"],
        "customer_id": t["customer_id"],
        "channel": t["channel"],
        "direction": "Inbound",
        "sender": t["customer_name"],
        "body": opening,
        "sent_at": fmt(base),
        "is_internal_note": 0,
    })
    msg_id += 1
    # a few back-and-forth replies
    n_replies = random.randint(1, 4)
    cursor = base
    for r in range(n_replies):
        cursor += timedelta(minutes=random.randint(3, 600))
        inbound = (r % 2 == 1)
        if inbound:
            conversations.append({
                "message_id": msg_id, "ticket_id": t["ticket_id"],
                "customer_id": t["customer_id"], "channel": t["channel"],
                "direction": "Inbound", "sender": t["customer_name"],
                "body": random.choice([
                    "Okay, thanks for looking into it.",
                    "That's still not resolved though.",
                    "Order number is " + t["order_ref"] + ".",
                    "Appreciate the quick reply!",
                    "How long will that take?",
                ]),
                "sent_at": fmt(cursor), "is_internal_note": 0,
            })
        else:
            conversations.append({
                "message_id": msg_id, "ticket_id": t["ticket_id"],
                "customer_id": t["customer_id"], "channel": t["channel"],
                "direction": "Outbound", "sender": t["assigned_agent"],
                "body": random.choice([
                    "Thanks for getting in touch — I'm checking this now.",
                    "I've escalated this and you'll hear back within 24h.",
                    "I've processed that for you, anything else?",
                    "Could you confirm your order number please?",
                    "Sorry for the wait — sorting it right away.",
                ]),
                "sent_at": fmt(cursor), "is_internal_note": 0,
            })
        msg_id += 1
    # occasional internal note (agent-only)
    if random.random() < 0.3:
        cursor += timedelta(minutes=random.randint(1, 30))
        conversations.append({
            "message_id": msg_id, "ticket_id": t["ticket_id"],
            "customer_id": t["customer_id"], "channel": "Internal",
            "direction": "Note", "sender": t["assigned_agent"],
            "body": random.choice([
                "Customer is a VIP - handle with priority.",
                "Refund approved by supervisor.",
                "Possible repeat issue, see previous ticket.",
                "Courier confirmed parcel lost in transit.",
            ]),
            "sent_at": fmt(cursor), "is_internal_note": 1,
        })
        msg_id += 1

with open(os.path.join(DATA_DIR, "conversations.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(conversations[0].keys()))
    w.writeheader()
    w.writerows(conversations)

# ----------------------------------------------------------------------------
# 4. canned_responses.csv  (saved replies / macros)
# ----------------------------------------------------------------------------
with open(os.path.join(DATA_DIR, "canned_responses.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["canned_id", "category", "title", "body"])
    for i, (cat, title, body) in enumerate(CANNED, start=1):
        w.writerow([i, cat, title, body])

print("Demo data generated in DATA/:")
for fn in sorted(os.listdir(DATA_DIR)):
    path = os.path.join(DATA_DIR, fn)
    print(f"  {fn:24s} {os.path.getsize(path):>7,} bytes")
print(f"\ncustomers={len(customers)}  tickets={len(tickets)}  "
      f"messages={len(conversations)}  canned={len(CANNED)}")
