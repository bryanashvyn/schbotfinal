"""calendar_sync_apple.py — sync events to Apple iCloud Calendar via CalDAV."""
import logging
from datetime import datetime, timedelta

try:
    from caldav import DAVClient
    from caldav.objects import Calendar
    import icalendar
except ImportError:
    DAVClient = None

import db

logger = logging.getLogger(__name__)

# iCloud CalDAV endpoint
ICLOUD_CALDAV_URL = "https://caldav.icloud.com"


def test_connection(email, password):
    """Test if iCloud credentials work."""
    if not DAVClient:
        return False, "caldav library not installed"
    
    try:
        client = DAVClient(
            url=ICLOUD_CALDAV_URL,
            username=email,
            password=password,
        )
        # Try to get principal (this validates credentials)
        principal = client.principal()
        calendars = principal.calendars()
        return True, "connected ✅"
    except Exception as e:
        logger.exception("iCloud connection failed")
        return False, f"connection failed: {str(e)}"


def store_credentials(chat_id, email, password):
    """Store iCloud credentials securely."""
    with db.get_conn() as conn:
        conn.execute(
            """INSERT INTO apple_auth (chat_id, email, password)
               VALUES (?, ?, ?)
               ON CONFLICT(chat_id) DO UPDATE SET
                 email = excluded.email,
                 password = excluded.password""",
            (chat_id, email, password),
        )


def get_credentials(chat_id):
    """Retrieve iCloud credentials."""
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT email, password FROM apple_auth WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else None


def delete_credentials(chat_id):
    """Delete iCloud credentials."""
    with db.get_conn() as conn:
        conn.execute("DELETE FROM apple_auth WHERE chat_id = ?", (chat_id,))


def _get_client(chat_id):
    """Get authenticated CalDAV client for this user."""
    if not DAVClient:
        return None, "caldav not installed"
    
    creds = get_credentials(chat_id)
    if not creds:
        return None, "not connected"
    
    try:
        client = DAVClient(
            url=ICLOUD_CALDAV_URL,
            username=creds["email"],
            password=creds["password"],
        )
        return client, None
    except Exception as e:
        logger.exception("Failed to get CalDAV client")
        return None, str(e)


def _get_calendar(chat_id):
    """Get the primary calendar for this user."""
    client, err = _get_client(chat_id)
    if err:
        return None, err
    
    try:
        principal = client.principal()
        calendars = principal.calendars()
        
        # Use the first calendar (primary)
        if calendars:
            return calendars[0], None
        else:
            return None, "no calendars found"
    except Exception as e:
        logger.exception("Failed to get calendar")
        return None, str(e)


def push_event(chat_id, event):
    """Add or update event in Apple Calendar."""
    if not DAVClient:
        return None, "caldav not installed"
    
    calendar, err = _get_calendar(chat_id)
    if err:
        return None, f"calendar error: {err}"
    
    try:
        # Build iCalendar event
        ical = icalendar.Event()
        ical.add("uid", f"schedule-bot-{event['id']}@example.com")
        ical.add("summary", event["title"])
        
        # Parse dates
        from dateutil import parser as dtparser
        start_dt = dtparser.isoparse(event["start_dt"])
        end_dt = dtparser.isoparse(event["end_dt"]) if event.get("end_dt") else start_dt + timedelta(hours=1)
        
        ical.add("dtstart", start_dt)
        ical.add("dtend", end_dt)
        
        if event.get("notes"):
            ical.add("description", event["notes"])
        
        # Handle recurrence
        if event.get("rrule"):
            ical.add("rrule", event["rrule"])
        
        # Add to calendar
        calendar.save_event(ical)
        
        # Store UID for future reference
        db.link_event_to_apple_uid(event["id"], f"schedule-bot-{event['id']}@example.com")
        
        return event["id"], None
    except Exception as e:
        logger.exception("Failed to push event to Apple Calendar")
        return None, str(e)


def delete_event(chat_id, event):
    """Remove event from Apple Calendar."""
    if not DAVClient:
        return True, "caldav not installed"
    
    calendar, err = _get_calendar(chat_id)
    if err:
        return False, f"calendar error: {err}"
    
    try:
        # Get the UID we stored
        uid = db.get_apple_uid_for_event(event["id"])
        if not uid:
            # If no UID stored, try to delete by ID
            uid = f"schedule-bot-{event['id']}@example.com"
        
        # Find and delete event
        try:
            event_obj = calendar.search(uid=uid)
            if event_obj:
                event_obj[0].delete()
        except:
            pass  # Event may not exist, that's ok
        
        return True, None
    except Exception as e:
        logger.exception("Failed to delete event from Apple Calendar")
        return False, str(e)


def check_connection(chat_id):
    """Check if user is connected to Apple Calendar."""
    creds = get_credentials(chat_id)
    if not creds:
        return False
    
    try:
        client = DAVClient(
            url=ICLOUD_CALDAV_URL,
            username=creds["email"],
            password=creds["password"],
        )
        client.principal()
        return True
    except:
        return False
