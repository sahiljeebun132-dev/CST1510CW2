# CST1510 Coursework 2 — Technical Report
## HelpHub: An Omnichannel Customer Service Platform

**Student ID:** _[your ID]_  **Name:** _[your name]_  **Module:** CST1510

> Adapt this into the provided report template. It documents the design,
> implementation and testing of the submitted application.

---

## 1. Introduction

HelpHub is a secure, multi-channel customer-service platform built in Python.
It is modelled on commercial contact-centre tools such as **Gnatta** (used by
the retailer Footasylum), where support agents handle customer conversations
from many channels — email, live chat, social media, phone and SMS — inside a
single workspace.

The application is built incrementally on the foundations taught in the CW2
video series: secure password hashing with **bcrypt**, an **SQLite** relational
database accessed through full CRUD operations, **pandas** for migrating CSV
datasets into the database, a modular **MVC-style package**, an interactive
**Streamlit** web UI with **session management**, and an **OpenAI**-powered AI
assistant. The cyber-intelligence theme of the original brief is reskinned as a
customer-service domain, but every underlying technique is preserved.

## 2. System architecture

The codebase follows a clear **Model–View–Controller** separation:

- **Model** — the `app_model/` package. Each module owns one domain
  (security, database, users, customers, tickets, conversations, canned
  responses, AI). The model layer contains all database access and business
  logic and never imports Streamlit, so it can be tested in isolation.
- **View / Controller** — `main.py`. Streamlit renders the UI and routes the
  user between pages based on session state. Views call model functions only;
  they contain no SQL.

```
main.py  ──calls──▶  app_model/*  ──uses──▶  SQLite (DATA/project_data.db)
   ▲                                              ▲
 Streamlit UI                              pandas migrates CSV ▶ tables
```

The data model has five tables linked by foreign keys:

| Table | Purpose | Key relationships |
|---|---|---|
| `users` | Agent accounts (hashed passwords, roles) | — |
| `customers` | Customer records & lifetime value | — |
| `tickets` | One support case each | `customer_id → customers` |
| `conversations` | Messages within a ticket | `ticket_id → tickets` |
| `canned_responses` | Saved reply macros | — |

## 3. Security: password hashing (Video 01)

Passwords are never stored in plain text. `security.py` wraps bcrypt:

- `generate_hash(psw)` encodes the password to bytes, generates a random salt
  with `bcrypt.gensalt(rounds=12)`, hashes it, and returns a UTF-8 string.
- `is_valid_hash(psw, hash_)` uses `bcrypt.checkpw` for a constant-time compare.

The **cost factor of 12** makes hashing deliberately slow (~2¹² rounds),
frustrating brute-force attacks, while **per-password salting** ensures that
two identical passwords produce different hashes, defeating rainbow-table
attacks. A bonus `password_strength()` helper powers the live strength meter on
the registration form — a small UX improvement over the base brief.

## 4. Authentication & session management (Videos 02, 06, 07)

`users.py` provides `register_user`, `login_user`, and supporting CRUD.
Registration rejects duplicate usernames and empty fields and returns a
`(success, message)` tuple so the UI can give clear feedback. Login fetches the
stored hash and verifies it with bcrypt.

Session state (`st.session_state`) stores `logged_in`, `username`, `role` and
`full_name`. The router in `main.py` shows the login/register screen when the
user is not authenticated and the full workspace once they are. The **Team
Admin** page is conditionally added to the navigation only for `supervisor` and
`admin` roles, demonstrating role-based access control.

## 5. Database & CRUD (Video 03)

`db.py` centralises the SQLite connection, enabling `sqlite3.Row` (column
access by name) and `PRAGMA foreign_keys = ON`. `schema.py` creates all tables
with `CREATE TABLE IF NOT EXISTS`, so startup is idempotent.

Every domain module implements full **Create, Read, Update, Delete**:

- **Create** — e.g. `tickets.create_ticket`, `customers.add_customer`.
- **Read** — single-row `fetchone` lookups and `pandas.read_sql` queries that
  return DataFrames for the dashboard.
- **Update** — e.g. `tickets.update_status`, `users.update_password`.
- **Delete** — e.g. `tickets.delete_ticket`, which cascades to remove the
  ticket's conversation messages first to respect the foreign-key constraint.

**Two security practices are applied throughout:** all values are bound with
`?` **parameterized placeholders** (never string-formatted into SQL, preventing
SQL injection), and every UPDATE/DELETE includes a WHERE clause so a single row
is affected rather than the whole table.

## 6. CSV → SQLite migration with pandas (Video 03)

`seed.py` migrates three CSV datasets into the database with pandas:
`pd.read_csv(path)` loads each file and `DataFrame.to_sql(table, conn)` writes
it. `init_database()` orchestrates the whole bootstrap — create tables, seed
default agent accounts (with hashed passwords), and migrate the CSVs only if a
table is empty — so the app is ready on first run with no manual steps.

The demo dataset (generated by `generate_demo_data.py`) contains 40 customers,
80 tickets and ~305 messages, themed around a streetwear/footwear retailer to
make the dashboard look realistic during the demo.

## 7. Modular package design (Video 04)

The growing logic is split into the `app_model/` package with one module per
concern and an `__init__.py` that documents the layout. This separation of
concerns keeps each file short, makes the code testable without the UI, and
mirrors the layered architecture taught in the brief.

## 8. Streamlit dashboard & UI (Videos 05, 07)

The UI is organised into six pages reached from the sidebar:

- **Dashboard** — KPI cards (total, open, SLA breaches, CSAT, resolution rate)
  and five `st.bar_chart` visualisations grouped from the ticket data.
- **Inbox** — the core omnichannel queue: filter controls, a scrollable ticket
  list, and a conversation panel that renders inbound/outbound/internal
  messages as styled chat bubbles, with reply, note, canned-reply and ticket
  controls.
- **Customers** — searchable directory, add-customer form, and per-customer
  profile with ticket history.
- **Canned Replies** — manage saved macros with placeholder substitution.
- **AI Copilot** — chat interface using `st.chat_input`/`st.chat_message`.
- **Team Admin** — agent management for privileged roles.

Custom CSS provides KPI cards, coloured status/priority pills and chat bubbles
for a polished, friendly interface that goes beyond the base requirement.

## 9. AI integration (Videos 08, 09)

`ai_assistant.py` adds an agent co-pilot. It first builds a **live data
context** from the database (totals, SLA breaches, CSAT, breakdowns by status,
channel and category) so answers are grounded in real numbers. It then operates
in one of two modes, chosen automatically:

1. **Online** — if an OpenAI key is found (env var `OPENAI_API_KEY`, a
   `.openai_key` file, or a passed argument), it calls
   `client.chat.completions.create(model="gpt-4o-mini", ...)` with the system
   prompt, the data context and recent history. An optional `OPENAI_BASE_URL`
   supports free/compatible endpoints (Video 09).
2. **Offline** — if no key is available or the API call fails, a rule-based
   intent engine answers from the same context (SLA, backlog, CSAT, response
   time, channels, categories, summaries, reply suggestions).

This dual design means the assistant **always works during the demo**, with or
without internet or a paid key — a deliberate robustness improvement.

## 10. Testing & verification

`test_smoke.py` runs 21 automated checks against the model layer with a fresh
database: bcrypt match/mismatch and salt uniqueness; registration and duplicate
rejection; correct and incorrect login; that all four CSVs migrated with the
expected row counts; ticket create/update/delete; parameterized filtering;
analytics totals and group-by; and the AI offline responses. All 21 pass. The
Streamlit app was additionally booted headless and served HTTP 200 with no
import or runtime errors.

## 11. Reflection & possible extensions

The project meets every CW2 requirement and adds genuine product features:
omnichannel routing, SLA tracking, internal notes, canned replies, a CRM view,
role-based admin and a resilient AI co-pilot. Future work could include
automatic ticket routing by sentiment, CSAT survey emails, real channel
integrations (e.g. an email/IMAP poller), and a Plotly time-series of ticket
volume. Security could be hardened further with rate-limiting on login and
password-reset tokens.

## 12. References

- bcrypt documentation — password hashing and salting
- SQLite / Python `sqlite3` — parameterized queries
- pandas — `read_csv`, `to_sql`, `read_sql`
- Streamlit — `session_state`, `chat_input`, charting
- OpenAI Python SDK — Chat Completions API
