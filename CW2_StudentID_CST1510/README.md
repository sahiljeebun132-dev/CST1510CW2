# 🎧 HelpHub — Omnichannel Customer Service Platform

**CST1510 Coursework 2** · A Gnatta-style contact-centre built in Python with
bcrypt, SQLite, pandas, Streamlit and an OpenAI-powered AI co-pilot.

HelpHub gives support agents **one shared inbox** across email, live chat,
WhatsApp, Instagram, X, Facebook, phone and SMS — with a ticket queue, SLA
timers, customer profiles, canned replies, an analytics dashboard and an AI
assistant that answers questions about your live data.

---

## Quick start

```bash
# 1. (optional) create a virtual environment
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
streamlit run main.py
```

The database (`DATA/project_data.db`) is **created and seeded automatically**
the first time you run the app — tables are built, default agent accounts are
added, and the three CSV datasets are migrated in with pandas. No setup script
needed.

> If you ever want a clean re-seed, delete `DATA/project_data.db` and restart,
> or run `python -m app_model.seed`.

### Demo logins

| Username        | Password    | Role        |
|-----------------|-------------|-------------|
| `admin`         | `admin123`  | admin       |
| `sarah.lee`     | `password1` | supervisor  |
| `james.okafor`  | `password1` | agent       |
| `priya.nair`    | `password1` | agent       |
| `tom.becker`    | `password1` | agent       |

You can also register a brand-new agent account from the **Register** tab.

---

## Features

**Authentication & security**
- bcrypt password hashing (cost factor 12) with per-password salting
- Register / login forms with a live password-strength meter
- Session management — protected pages, role-based navigation, logout

**Omnichannel inbox**
- One unified queue across 8 channels, each with its own icon
- Filter by status, priority, channel, agent, or free-text search
- Full conversation thread per ticket: inbound, outbound and internal notes
- Reply to customers, add internal notes, insert canned replies
- Change status, priority, assignee and CSAT; create or delete tickets
- SLA target + due time shown on every ticket

**Customers (CRM)**
- Searchable customer directory with loyalty tier and lifetime value
- Per-customer profile with full ticket history
- Add / edit customer records

**Canned replies (macros)**
- Saved replies with `{name}`, `{oid}`, `{product}` placeholders that
  auto-fill from the active ticket
- Add and delete macros

**Analytics dashboard**
- KPI cards: total tickets, open, SLA breaches, average CSAT, resolution rate
- Bar charts: tickets by status, channel, category, priority and agent workload

**AI Copilot**
- Ask natural-language questions about your live data
- Uses the **OpenAI API** when a key is configured, with a built-in
  **offline rule-based engine** as a fallback so it always works

**Team Admin** (supervisors/admins)
- Create agents, reset passwords, change roles, remove agents

---

## Enabling the OpenAI AI assistant (optional)

The Copilot works **offline out of the box**. To unlock full natural-language
answers, give it an API key in any one of these ways:

1. Environment variable:
   ```bash
   # Windows
   setx OPENAI_API_KEY "sk-..."
   # macOS/Linux
   export OPENAI_API_KEY="sk-..."
   ```
2. Or create a file named `.openai_key` in the project root containing the key.

Free / compatible endpoints (CW2 Video 09): set `OPENAI_BASE_URL` to point at a
compatible provider, and optionally `OPENAI_MODEL` (default `gpt-4o-mini`).

The sidebar shows **🟢 OpenAI connected** or **🟡 offline mode** so you always
know which mode you're in.

---

## Project structure

```
CW2_StudentID_CST1510/
├── main.py                 ← Streamlit entry point (controller + views)
├── cli.py                  ← terminal register/login menu (Videos 02-03)
├── requirements.txt
├── generate_demo_data.py   ← regenerates the demo CSVs
├── test_smoke.py           ← model-layer verification tests (27 checks)
├── DATA/
│   ├── project_data.db     ← SQLite DB (auto-created)
│   ├── customers.csv
│   ├── tickets.csv
│   ├── conversations.csv
│   └── canned_responses.csv
└── app_model/              ← model layer (MVC)
    ├── __init__.py
    ├── security.py         ← bcrypt hashing / verification
    ├── db.py               ← SQLite connection utility
    ├── schema.py           ← table creation (DDL)
    ├── seed.py             ← pandas CSV → SQLite migration
    ├── users.py            ← agent accounts + register/login
    ├── customers.py        ← customer CRUD
    ├── tickets.py          ← ticket CRUD + analytics
    ├── conversations.py    ← message thread CRUD
    ├── canned_responses.py ← saved-reply CRUD
    └── ai_assistant.py     ← AI co-pilot (OpenAI + offline)
```

---

## Verifying it works

```bash
python test_smoke.py
```

Runs 21 checks across bcrypt hashing, registration/login, CSV→SQLite migration,
ticket CRUD, filtering, analytics and the AI fallback. All should pass.

---

## How it maps to the CW2 rubric

| Requirement | Where |
|---|---|
| 1. bcrypt password hashing | `app_model/security.py` |
| 2. Register + login | `app_model/users.py`, `main.py` auth screen |
| 3. SQLite + full CRUD | `app_model/db.py`, `schema.py`, all domain modules |
| 4. CSV → SQLite via pandas | `app_model/seed.py` (`migrate_csv`) |
| 5. Modular package | `app_model/` (one module per domain) |
| 6. Streamlit dashboard | `main.py` `page_dashboard` (charts) |
| 7. Session management | `st.session_state`, protected pages in `main.py` |
| 8. Login/register UI | `main.py` `auth_screen` (forms + validation) |
| 9. ChatGPT integration | `app_model/ai_assistant.py`, `main.py` `page_ai` |

> **Security note:** every SQL statement uses `?` placeholders (parameterized
> queries) to prevent SQL injection, and all UPDATE/DELETE statements include a
> WHERE clause.

### Canonical functions from the video series

The exact functions taught in the videos are preserved verbatim so the code
matches the brief, with friendlier wrappers layered on top:

- `security.generate_hash` / `security.is_valid_hash` (Video 01)
- `users.create_user_table`, `add_user`, `get_all_users`, `get_user`,
  `update_user`, `delete_user` (Video 03)
- `seed.migrate_customers` / `migrate_tickets` / … follow the same
  `pd.read_csv(...) → df.to_sql(...)` pattern as the brief's
  `migrate_cyber_incidents` (Video 03)
- `cli.py` reproduces the Video 02/03 terminal menu (`1. Register / 2. Log in /
  3. Exit`) on top of SQLite, showing the journey from CLI to web app.
