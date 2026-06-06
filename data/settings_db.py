"""Global settings DB — recent projects, learned mappings, app config."""

from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from config import SETTINGS_DB
from data.encryption import encrypt, decrypt


class SettingsDB:
    _instance: "SettingsDB | None" = None

    def __init__(self):
        self._conn = sqlite3.connect(SETTINGS_DB, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    @classmethod
    def instance(cls) -> "SettingsDB":
        if cls._instance is None:
            cls._instance = SettingsDB()
        return cls._instance

    @contextmanager
    def _tx(self):
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _init_schema(self):
        self._conn.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        );
        CREATE TABLE IF NOT EXISTS recent_projects (
            path TEXT PRIMARY KEY,
            entity_name TEXT,
            entity_type TEXT,
            fy TEXT,
            last_opened TEXT
        );
        CREATE TABLE IF NOT EXISTS learned_mappings (
            ledger_name TEXT,
            entity_type TEXT,
            mapping_code TEXT,
            confirmed_count INTEGER DEFAULT 1,
            PRIMARY KEY (ledger_name, entity_type)
        );
        """)
        self._conn.commit()

    # ── Settings ─────────────────────────────────────────────────────────
    def get(self, key: str, default: str = "") -> str:
        row = self._conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set(self, key: str, value: str):
        with self._tx():
            self._conn.execute(
                "INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value)
            )

    def get_api_key(self, provider: str = "Claude") -> str:
        key_name = f"{provider.lower()}_api_key"
        v = self.get(key_name)
        return decrypt(v) if v else ""

    def set_api_key(self, key: str, provider: str = "Claude"):
        key_name = f"{provider.lower()}_api_key"
        self.set(key_name, encrypt(key) if key else "")

    def get_ai_provider(self) -> str:
        return self.get("ai_provider", "Claude")

    def set_ai_provider(self, provider: str):
        self.set("ai_provider", provider)

    def get_annexure_tolerance(self) -> float:
        v = self.get("annexure_tolerance", "10")
        try:
            return float(v)
        except ValueError:
            return 10.0

    def set_annexure_tolerance(self, value: float):
        self.set("annexure_tolerance", str(value))

    # ── Recent Projects ───────────────────────────────────────────────────
    def add_recent(self, path: str, name: str, etype: str, fy: str):
        with self._tx():
            self._conn.execute(
                "INSERT OR REPLACE INTO recent_projects(path,entity_name,entity_type,fy,last_opened) "
                "VALUES(?,?,?,?,?)",
                (path, name, etype, fy, datetime.now().isoformat())
            )

    def get_recent(self, limit: int = 10) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM recent_projects ORDER BY last_opened DESC LIMIT ?", (limit,)
        ).fetchall()

    def remove_recent(self, path: str):
        with self._tx():
            self._conn.execute("DELETE FROM recent_projects WHERE path=?", (path,))

    # ── Learned Mappings ─────────────────────────────────────────────────
    def learn(self, ledger: str, entity_type: str, code: str):
        with self._tx():
            self._conn.execute("""
                INSERT INTO learned_mappings(ledger_name,entity_type,mapping_code,confirmed_count)
                VALUES(?,?,?,1)
                ON CONFLICT(ledger_name,entity_type) DO UPDATE SET
                  mapping_code=excluded.mapping_code,
                  confirmed_count=confirmed_count+1
            """, (ledger.strip().lower(), entity_type, code))

    def lookup(self, ledger: str, entity_type: str) -> str | None:
        row = self._conn.execute(
            "SELECT mapping_code FROM learned_mappings WHERE ledger_name=? AND entity_type=?",
            (ledger.strip().lower(), entity_type)
        ).fetchone()
        return row[0] if row else None

    def get_all_learned(self, entity_type: str) -> dict[str, str]:
        rows = self._conn.execute(
            "SELECT ledger_name,mapping_code FROM learned_mappings WHERE entity_type=?",
            (entity_type,)
        ).fetchall()
        return {r[0]: r[1] for r in rows}
