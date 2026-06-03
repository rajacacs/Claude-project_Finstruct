"""Fernet encryption for PII fields — reuses CA Reminder pattern."""

from __future__ import annotations
import os
import stat
import logging
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

log = logging.getLogger(__name__)
_KEY_FILE = Path(os.environ.get("APPDATA", Path.home())) / "FinStruct" / ".enc_key"

_fernet: Fernet | None = None


def _load_or_create_key() -> Fernet:
    global _fernet
    if _fernet:
        return _fernet
    try:
        import keyring
        raw = keyring.get_password("finstruct_v1", "enc_key")
        if raw:
            _fernet = Fernet(raw.encode())
            return _fernet
        key = Fernet.generate_key()
        keyring.set_password("finstruct_v1", "enc_key", key.decode())
        _fernet = Fernet(key)
        return _fernet
    except Exception:
        pass
    # File fallback
    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if _KEY_FILE.exists():
        _fernet = Fernet(_KEY_FILE.read_bytes().strip())
    else:
        key = Fernet.generate_key()
        _KEY_FILE.write_bytes(key)
        try:
            os.chmod(_KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
        _fernet = Fernet(key)
    return _fernet


def encrypt(value: str) -> str:
    if not value:
        return value
    try:
        return _load_or_create_key().encrypt(value.encode()).decode()
    except Exception as e:
        log.error("Encryption failed: %s", e)
        return value


def decrypt(value: str) -> str:
    if not value:
        return value
    try:
        return _load_or_create_key().decrypt(value.encode()).decode()
    except (InvalidToken, Exception):
        return "[DECRYPTION ERROR]"
