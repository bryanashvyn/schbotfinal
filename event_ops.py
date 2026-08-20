"""Single source of truth for creating/deleting events and shift cycles,
used by both the button-based conversation flows and the natural-language
handler — so there's exactly one place that builds RRULEs and talks to
Apple Calendar, instead of two copies that could drift apart."""
import json
from datetime import timedelta

import db
import calendar_sync_apple as calendar_sync

RECURRENCE_OPTIONS = {
    "none": "One-off",
    "weekly": "Weekly",
    "biweekly": "Every 2 weeks (biweekly)",
    "monthly": "Monthly",
    "every6months": "6-week block, every 6 months",
}

DEFAULT_SHIFT_PATTERN = ["morning", "morning", "afternoon", "afternoon", "off", "off"]


def build_rrule(recurrence, weekdays, start_dt):
    """Returns (rrule_str_or_None, end_dt_iso_or_None)."""
    weekdays = weekdays or []
    if recurrence in ("weekly", "biweekly") and not weekdays:
        # Can't build a valid BYDAY rule without days — safer to fall back
        # to one-off than to silently create a recurrence that never fires.
        return None, None
    if recurrence == "weekly":
        return f"FREQ=WEEKLY;BYDAY={','.join(sorted(weekdays))}", None
    if recurrence == "biweekly":
        return f"FREQ=WEEKLY;INTERVAL=2;BYDAY={','.join(sorted(weekdays))}", None
    if recurrence == "monthly":
        return "FREQ=MONTHLY", None
    if recurrence == "every6months":
        return "FREQ=MONTHLY;INTERVAL=6", (start_dt + timedelta(weeks=6)).isoformat()
    return None, None


def create_event(chat_id, title, category, start_dt, recurrence="none",
                  weekdays=None, reminder_offsets=None, notes=None):
    """start_dt: an aware datetime. Returns (event_id, synced: bool)."""
    rrule, end_dt = build_rrule(recurrence, weekdays, start_dt)
    reminder_offsets = sorted(reminder_offsets) if reminder_offsets else [0]

    # Calculate end_dt if not provided
    if not end_dt:
        end_dt = (start_dt + timedelta(hours=1)).isoformat()
    else:
        # end_dt is already an ISO string from build_rrule
        pass

    event_id = db.add_event(
        chat_id=chat_id, title=title, category=category,
        start_dt=start_dt.isoformat(), end_dt=end_dt, rrule=rrule,
        reminder_offsets=reminder_offsets, notes=notes,
    )

    synced = False
    if calendar_sync.check_connection(chat_id):
        # Get the created event
        event = db.get_event(event_id)
        if event:
            _, err = calendar_sync.push_event(chat_id, event)
            if not err:
                synced = True
    return event_id, synced


def delete_event(chat_id, event_id):
    """Returns the deleted event dict, or None if it wasn't found/owned by this chat."""
    event = db.get_event(event_id)
    if not event or event["chat_id"] != chat_id:
        return None
    
    # Delete from Apple Calendar if connected
    if calendar_sync.check_connection(chat_id):
        calendar_sync.delete_event(chat_id, event)
    
    db.deactivate_event(event_id, chat_id)
    return event


def find_events_by_title(chat_id, title_search):
    return [
        e for e in db.get_active_events(chat_id)
        if title_search.lower() in e["title"].lower()
    ]


def set_shift(chat_id, anchor_date, first_shift):
    """anchor_date: a date object. Returns synced: bool."""
    start_idx = DEFAULT_SHIFT_PATTERN.index(first_shift)
    pattern = DEFAULT_SHIFT_PATTERN[start_idx:] + DEFAULT_SHIFT_PATTERN[:start_idx]

    cycle_id = db.set_shift_cycle(chat_id=chat_id, anchor_date=anchor_date.isoformat(), pattern=pattern)

    # Note: shift syncing to Apple Calendar is complex (would need to create 6 recurring events)
    # For now, shifts are local-only. Events u add (exams, dates, etc.) sync normally.
    return False
