"""SQLite persistence layer for the schedule bot."""
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "schedule_bot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    start_dt TEXT NOT NULL,
    end_dt TEXT,
    rrule TEXT,
    reminder_offsets TEXT NOT NULL DEFAULT '[0]',
    notes TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shift_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    anchor_date TEXT NOT NULL,
    pattern TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sent_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    occurrence_dt TEXT NOT NULL,
    offset_minutes INTEGER NOT NULL,
    sent_at TEXT NOT NULL,
    UNIQUE(event_id, occurrence_dt, offset_minutes)
);

CREATE TABLE IF NOT EXISTS google_auth (
    chat_id INTEGER PRIMARY KEY,
    refresh_token TEXT NOT NULL,
    access_token TEXT NOT NULL,
    expiry TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_settings (
    chat_id INTEGER PRIMARY KEY,
    digest_hour INTEGER DEFAULT 7,
    digest_minute INTEGER DEFAULT 0,
    timezone TEXT DEFAULT 'Asia/Singapore'
);

CREATE TABLE IF NOT EXISTS user_state (
    chat_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (chat_id, key)
);

CREATE TABLE IF NOT EXISTS apple_auth (
    chat_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS apple_event_uids (
    event_id INTEGER PRIMARY KEY,
    apple_uid TEXT NOT NULL
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate(conn):
    """Add columns to pre-existing DBs from before Google sync existed."""
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(events)")]
    if "google_event_id" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN google_event_id TEXT")
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(shift_cycles)")]
    if "google_event_ids" not in cols:
        conn.execute("ALTER TABLE shift_cycles ADD COLUMN google_event_ids TEXT")


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


# ---------- Events ----------

def add_event(chat_id, title, category, start_dt, end_dt=None, rrule=None,
              reminder_offsets=None, notes=None):
    reminder_offsets = reminder_offsets or [0]
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO events
               (chat_id, title, category, start_dt, end_dt, rrule,
                reminder_offsets, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (chat_id, title, category, start_dt, end_dt, rrule,
             json.dumps(reminder_offsets), notes,
             datetime.now(timezone.utc).isoformat()),
        )
        return cur.lastrowid


def get_active_events(chat_id=None):
    with get_conn() as conn:
        if chat_id is not None:
            rows = conn.execute(
                "SELECT * FROM events WHERE active = 1 AND chat_id = ? ORDER BY start_dt",
                (chat_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM events WHERE active = 1 ORDER BY start_dt"
            ).fetchall()
        return [dict(r) for r in rows]


def get_event(event_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return dict(row) if row else None


def deactivate_event(event_id, chat_id):
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE events SET active = 0 WHERE id = ? AND chat_id = ?",
            (event_id, chat_id),
        )
        return cur.rowcount > 0


def get_distinct_chat_ids():
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT chat_id FROM events").fetchall()
        return [r["chat_id"] for r in rows]


# ---------- Shift cycles ----------

def set_shift_cycle(chat_id, anchor_date, pattern):
    with get_conn() as conn:
        conn.execute(
            "UPDATE shift_cycles SET active = 0 WHERE chat_id = ?", (chat_id,)
        )
        cur = conn.execute(
            """INSERT INTO shift_cycles (chat_id, anchor_date, pattern, active)
               VALUES (?, ?, ?, 1)""",
            (chat_id, anchor_date, json.dumps(pattern)),
        )
        return cur.lastrowid


def get_shift_cycle(chat_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM shift_cycles WHERE chat_id = ? AND active = 1",
            (chat_id,),
        ).fetchone()
        return dict(row) if row else None


def set_shift_google_ids(cycle_id, google_event_ids):
    with get_conn() as conn:
        conn.execute(
            "UPDATE shift_cycles SET google_event_ids = ? WHERE id = ?",
            (json.dumps(google_event_ids), cycle_id),
        )


# ---------- Google Calendar linkage ----------

def set_event_google_id(event_id, google_event_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE events SET google_event_id = ? WHERE id = ?",
            (google_event_id, event_id),
        )


def save_google_auth(chat_id, refresh_token, access_token, expiry):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO google_auth (chat_id, refresh_token, access_token, expiry)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(chat_id) DO UPDATE SET
                 refresh_token = excluded.refresh_token,
                 access_token = excluded.access_token,
                 expiry = excluded.expiry""",
            (chat_id, refresh_token, access_token, expiry),
        )


def get_google_auth(chat_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM google_auth WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else None


def update_google_access_token(chat_id, access_token, expiry):
    with get_conn() as conn:
        conn.execute(
            "UPDATE google_auth SET access_token = ?, expiry = ? WHERE chat_id = ?",
            (access_token, expiry, chat_id),
        )


def delete_google_auth(chat_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM google_auth WHERE chat_id = ?", (chat_id,))


# ---------- User settings (digest time, timezone, etc.) ----------

def get_user_settings(chat_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM user_settings WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else None


def set_digest_time(chat_id, hour, minute=0, timezone="Asia/Singapore"):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO user_settings (chat_id, digest_hour, digest_minute, timezone)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(chat_id) DO UPDATE SET
                 digest_hour = excluded.digest_hour,
                 digest_minute = excluded.digest_minute,
                 timezone = excluded.timezone""",
            (chat_id, hour, minute, timezone),
        )


def get_digest_time(chat_id):
    """Return (hour, minute) for this user's digest, or (7, 0) default."""
    settings = get_user_settings(chat_id)
    if settings:
        return (settings["digest_hour"], settings["digest_minute"])
    return (7, 0)


def get_user_timezone(chat_id):
    """Return user's timezone, or Singapore default."""
    settings = get_user_settings(chat_id)
    return settings["timezone"] if settings else "Asia/Singapore"


# ---------- User state (transient stuff like joke rotation) ----------

def get_user_state(chat_id, key):
    """Get a stateful value for this user."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM user_state WHERE chat_id = ? AND key = ?",
            (chat_id, key),
        ).fetchone()
        return row["value"] if row else None


def set_user_state(chat_id, key, value):
    """Set a stateful value for this user."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO user_state (chat_id, key, value)
               VALUES (?, ?, ?)
               ON CONFLICT(chat_id, key) DO UPDATE SET value = excluded.value""",
            (chat_id, key, value),
        )


# ---------- Apple Calendar UID tracking ----------

def link_event_to_apple_uid(event_id, apple_uid):
    """Store the Apple Calendar UID for an event."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO apple_event_uids (event_id, apple_uid)
               VALUES (?, ?)
               ON CONFLICT(event_id) DO UPDATE SET apple_uid = excluded.apple_uid""",
            (event_id, apple_uid),
        )


def get_apple_uid_for_event(event_id):
    """Get the Apple Calendar UID for an event."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT apple_uid FROM apple_event_uids WHERE event_id = ?", (event_id,)
        ).fetchone()
        return row["apple_uid"] if row else None


# ---------- Sent reminders (dedupe) ----------

def was_reminder_sent(event_id, occurrence_dt, offset_minutes):
    with get_conn() as conn:
        row = conn.execute(
            """SELECT 1 FROM sent_reminders
               WHERE event_id = ? AND occurrence_dt = ? AND offset_minutes = ?""",
            (event_id, occurrence_dt, offset_minutes),
        ).fetchone()
        return row is not None


def mark_reminder_sent(event_id, occurrence_dt, offset_minutes):
    with get_conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO sent_reminders
               (event_id, occurrence_dt, offset_minutes, sent_at)
               VALUES (?, ?, ?, ?)""",
            (event_id, occurrence_dt, offset_minutes,
             datetime.now(timezone.utc).isoformat()),
        )
