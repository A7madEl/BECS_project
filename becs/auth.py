import os, base64, hashlib
try:
    import bcrypt
    _HAS_BCRYPT = True
except Exception:
    _HAS_BCRYPT = False

PBKDF2_ITERATIONS = 130_000

def _to_bytes(s):
    return s if isinstance(s, (bytes, bytearray)) else s.encode("utf-8")

def hash_password(password: str) -> str:
    pwd = _to_bytes(password)
    if _HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        digest = bcrypt.hashpw(pwd, salt)
        return "bcrypt$" + base64.b64encode(digest).decode("ascii")
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pwd, salt, PBKDF2_ITERATIONS)
    return f"pbkdf2${salt.hex()}${dk.hex()}${PBKDF2_ITERATIONS}"

def verify_password(password: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    scheme, rest = stored.split("$", 1)
    pwd = _to_bytes(password)
    if scheme == "bcrypt":
        if not _HAS_BCRYPT: return False
        try:
            import base64
            digest = base64.b64decode(rest.encode("ascii"))
            return bcrypt.checkpw(pwd, digest)
        except Exception:
            return False
    if scheme == "pbkdf2":
        try:
            salt_hex, hash_hex, it_s = rest.split("$")
            iters = int(it_s)
            dk = hashlib.pbkdf2_hmac("sha256", pwd, bytes.fromhex(salt_hex), iters)
            return dk.hex() == hash_hex
        except Exception:
            return False
    return False
