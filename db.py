"""Postgres persistence layer 4 the schedule bot."""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime, timezone

# Get Postgres URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment")


def get_conn():
    """Get a Postgres connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Create all tables if they don't exist."""
    with get_conn() as conn:
        cur = conn.cursor()
        
        # Events table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                start_dt TEXT NOT NULL,
                end_dt TEXT,
                rrule TEXT,
                reminder_offsets TEXT NOT NULL DEFAULT '[0]',
                notes TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        
        # Shift cycles table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS shift_cycles (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                anchor_date TEXT NOT NULL,
                pattern TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        # Sent reminders table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sent_reminders (
                id SERIAL PRIMARY KEY,
                event_id INTEGER NOT NULL,
                occurrence_dt TEXT NOT NULL,
                offset_minutes INTEGER NOT NULL,
                sent_at TEXT NOT NULL,
                UNIQUE(event_id, occurrence_dt, offset_minutes)
            )
        """)
        
        # User settings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                chat_id BIGINT PRIMARY KEY,
                digest_hour INTEGER DEFAULT 7,
                digest_minute INTEGER DEFAULT 0,
                timezone TEXT DEFAULT 'Asia/Singapore'
            )
        """)
        
        # User state table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_state (
                chat_id BIGINT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (chat_id, key)
            )
        """)
        
        # Apple auth table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS apple_auth (
                chat_id BIGINT PRIMARY KEY,
                email TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)
        
        # Apple event UIDs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS apple_event_uids (
                event_id INTEGER PRIMARY KEY,
                apple_uid TEXT NOT NULL
            )
        """)
        
        conn.commit()


# ---------- Events ----------

def add_event(chat_id, title, category, start_dt, end_dt=None, rrule=None,
              reminder_offsets=None, notes=None):
    """Add a new event."""
    if reminder_offsets is None:
        reminder_offsets = [0]
    
    reminder_json = json.dumps(reminder_offsets)
    created_at = datetime.now(timezone.utc).isoformat()
    
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO events 
               (chat_id, title, category, start_dt, end_dt, rrule, reminder_offsets, notes, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (chat_id, title, category, start_dt, end_dt, rrule, reminder_json, notes, created_at)
        )
        event_id = cur.fetchone()["id"]
        conn.commit()
        return event_id


def get_active_events(chat_id=None):
    """Get all active events."""
    with get_conn() as conn:
        cur = conn.cursor()
        if chat_id:
            cur.execute(
                "SELECT * FROM events WHERE chat_id = %s AND active = 1 ORDER BY start_dt",
                (chat_id,)
            )
        else:
            cur.execute("SELECT * FROM events WHERE active = 1 ORDER BY start_dt")
        
        rows = cur.fetchall()
        events = []
        for row in rows:
            event = dict(row)
            if isinstance(event.get("reminder_offsets"), str):
                event["reminder_offsets"] = json.loads(event["reminder_offsets"])
            events.append(event)
        return events


def get_event(event_id):
    """Get single event by ID."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM events WHERE id = %s", (event_id,))
        row = cur.fetchone()
        
        if not row:
            return None
        
        event = dict(row)
        if isinstance(event.get("reminder_offsets"), str):
            event["reminder_offsets"] = json.loads(event["reminder_offsets"])
        return event


def deactivate_event(event_id, chat_id):
    """Deactivate (soft delete) an event."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE events SET active = 0 WHERE id = %s AND chat_id = %s",
            (event_id, chat_id)
        )
        conn.commit()
        return cur.rowcount > 0


def update_event_field(event_id, field, value):
    """Update a single field of an event."""
    allowed_fields = ["title", "category", "start_dt", "end_dt", "rrule", "reminder_offsets", "notes"]
    if field not in allowed_fields:
        return False
    
    # Serialize lists as JSON
    if isinstance(value, list):
        value = json.dumps(value)
    
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE events SET {field} = %s WHERE id = %s",
            (value, event_id)
        )
        conn.commit()
        return True


def get_distinct_chat_ids():
    """Get all unique chat IDs."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT chat_id FROM events")
        rows = cur.fetchall()
        return [r["chat_id"] for r in rows]


# ---------- Shift cycles ----------

def set_shift_cycle(chat_id, anchor_date, pattern):
    """Create or update shift cycle."""
    with get_conn() as conn:
        cur = conn.cursor()
        
        # Delete old cycle if exists
        cur.execute("DELETE FROM shift_cycles WHERE chat_id = %s", (chat_id,))
        
        # Insert new
        cur.execute(
            """INSERT INTO shift_cycles (chat_id, anchor_date, pattern, active)
               VALUES (%s, %s, %s, 1)""",
            (chat_id, anchor_date, json.dumps(pattern))
        )
        conn.commit()


def get_shift_cycle(chat_id):
    """Get active shift cycle."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM shift_cycles WHERE chat_id = %s AND active = 1",
            (chat_id,)
        )
        row = cur.fetchone()
        
        if not row:
            return None
        
        result = dict(row)
        result["pattern"] = json.loads(result["pattern"])
        return result


# ---------- Reminders ----------

def was_reminder_sent(event_id, occurrence_dt, offset_minutes):
    """Check if reminder was already sent."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT 1 FROM sent_reminders 
               WHERE event_id = %s AND occurrence_dt = %s AND offset_minutes = %s""",
            (event_id, occurrence_dt, offset_minutes)
        )
        return cur.fetchone() is not None


def mark_reminder_sent(event_id, occurrence_dt, offset_minutes):
    """Mark reminder as sent."""
    sent_at = datetime.now(timezone.utc).isoformat()
    
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO sent_reminders (event_id, occurrence_dt, offset_minutes, sent_at)
                   VALUES (%s, %s, %s, %s)""",
                (event_id, occurrence_dt, offset_minutes, sent_at)
            )
            conn.commit()
        except:
            # Duplicate, ignore
            pass


# ---------- User settings ----------

def get_user_settings(chat_id):
    """Get user's settings."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_settings WHERE chat_id = %s", (chat_id,))
        row = cur.fetchone()
        
        if not row:
            return {"digest_hour": 7, "digest_minute": 0, "timezone": "Asia/Singapore"}
        
        return dict(row)


def set_digest_time(chat_id, hour, minute=0):
    """Set user's digest time."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO user_settings (chat_id, digest_hour, digest_minute)
               VALUES (%s, %s, %s)
               ON CONFLICT (chat_id) DO UPDATE SET digest_hour = %s, digest_minute = %s""",
            (chat_id, hour, minute, hour, minute)
        )
        conn.commit()


def set_timezone(chat_id, tz):
    """Set user's timezone."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO user_settings (chat_id, timezone)
               VALUES (%s, %s)
               ON CONFLICT (chat_id) DO UPDATE SET timezone = %s""",
            (chat_id, tz, tz)
        )
        conn.commit()


# ---------- User state ----------

def set_user_state(chat_id, key, value):
    """Store user state (for conversations)."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO user_state (chat_id, key, value)
               VALUES (%s, %s, %s)
               ON CONFLICT (chat_id, key) DO UPDATE SET value = %s""",
            (chat_id, key, value, value)
        )
        conn.commit()


def get_user_state(chat_id, key):
    """Get user state."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT value FROM user_state WHERE chat_id = %s AND key = %s",
            (chat_id, key)
        )
        row = cur.fetchone()
        return row["value"] if row else None


# ---------- Apple Calendar ----------

def store_apple_credentials(chat_id, email, password):
    """Store iCloud credentials."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO apple_auth (chat_id, email, password)
               VALUES (%s, %s, %s)
               ON CONFLICT (chat_id) DO UPDATE SET email = %s, password = %s""",
            (chat_id, email, password, email, password)
        )
        conn.commit()


def get_apple_credentials(chat_id):
    """Get iCloud credentials."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT email, password FROM apple_auth WHERE chat_id = %s", (chat_id,))
        row = cur.fetchone()
        
        if not row:
            return None
        
        return {"email": row["email"], "password": row["password"]}


def delete_apple_credentials(chat_id):
    """Delete iCloud credentials."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM apple_auth WHERE chat_id = %s", (chat_id,))
        conn.commit()


def link_event_to_apple_uid(event_id, apple_uid):
    """Link event 2 apple UID."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO apple_event_uids (event_id, apple_uid)
               VALUES (%s, %s)
               ON CONFLICT (event_id) DO UPDATE SET apple_uid = %s""",
            (event_id, apple_uid, apple_uid)
        )
        conn.commit()


def get_apple_uid_for_event(event_id):
    """Get apple UID 4 event."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT apple_uid FROM apple_event_uids WHERE event_id = %s", (event_id,))
        row = cur.fetchone()
        return row["apple_uid"] if row else None
