"""
app_model
=========
Model layer for the HelpHub customer-service platform (CST1510 CW2).

Modular, MVC-style package. Each module owns one domain:

    security.py          -> bcrypt password hashing / verification
    db.py                -> SQLite connection utility
    schema.py            -> table creation (DDL)
    seed.py              -> pandas CSV -> SQLite migration
    users.py             -> agent accounts + register / login logic
    customers.py         -> customer records (CRUD)
    tickets.py           -> support tickets (CRUD + queries)
    conversations.py     -> omnichannel messages (CRUD)
    canned_responses.py  -> saved replies / macros (CRUD)
    ai_assistant.py      -> AI co-pilot (OpenAI API + offline fallback)
"""

__version__ = "1.0.0"
__appname__ = "HelpHub"
