"""
security.py
-----------
Password security helpers built on bcrypt (CW2 Video 01).

The two core functions below are EXACTLY as taught in the video series; the
extra password_strength() helper is an additional UX feature.

Key ideas demonstrated:
  * Passwords are NEVER stored in plain text.
  * bcrypt is intentionally slow (cost factor 12, the gensalt default) to
    resist brute-force attacks.
  * A random salt is generated per password, so two identical passwords
    produce different hashes (defeats rainbow-table attacks).
  * bcrypt works on bytes, so we encode/decode around it.
"""

import bcrypt


# --- core functions, exactly as in CW2 Video 01 ----------------------------
def generate_hash(psw):
    byte_psw = psw.encode('utf-8')
    salt = bcrypt.gensalt()                 # default cost factor = 12
    hash = bcrypt.hashpw(byte_psw, salt)
    return hash.decode('utf-8')


def is_valid_hash(psw, hash):
    hash_ = hash.encode('utf-8')
    byte_psw = psw.encode('utf-8')
    is_valid = bcrypt.checkpw(byte_psw, hash_)
    return is_valid


# --- extra UX helper (beyond the brief) ------------------------------------
def password_strength(psw):
    """Rate a password and return (label, suggestions) for the register form."""
    suggestions = []
    score = 0
    if len(psw) >= 8:
        score += 1
    else:
        suggestions.append("Use at least 8 characters")
    if any(c.islower() for c in psw) and any(c.isupper() for c in psw):
        score += 1
    else:
        suggestions.append("Mix upper and lower case letters")
    if any(c.isdigit() for c in psw):
        score += 1
    else:
        suggestions.append("Add at least one number")
    if any(not c.isalnum() for c in psw):
        score += 1
    else:
        suggestions.append("Add a symbol (e.g. ! ? #)")

    label = {0: "Very weak", 1: "Weak", 2: "Fair", 3: "Strong",
             4: "Very strong"}[score]
    return label, suggestions


if __name__ == "__main__":
    h = generate_hash("S3cret!")
    print("hash:", h)
    print("correct ->", is_valid_hash("S3cret!", h))
    print("wrong   ->", is_valid_hash("nope", h))
    print("strength:", password_strength("S3cret!"))
