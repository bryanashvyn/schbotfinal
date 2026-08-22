"""Export events 2 ICS calendar file."""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from datetime import datetime
import io

import db
import utils

# ICS calendar template
ICS_HEADER = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Schedule Bot//Bryan's Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:My Schedule
X-WR-TIMEZONE:Asia/Singapore
BEGIN:VTIMEZONE
TZID:Asia/Singapore
BEGIN:STANDARD
DTSTART:19700101T000000
TZOFFSETFROM:+0800
TZOFFSETTO:+0800
TZNAME:SGT
END:STANDARD
END:VTIMEZONE
"""

ICS_FOOTER = "END:VCALENDAR"


def create_ics_event(event):
    """Convert a db event 2 ICS format."""
    event_id = event["id"]
    title = event["title"]
    start_dt = utils.parse_datetime_flexible(event["start_dt"])
    
    if not start_dt:
        return None
    
    # ICS format needs UTC times in specific format
    start_utc = start_dt.astimezone().strftime("%Y%m%dT%H%M%S")
    created_at = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    
    # Unique identifier 4 ICS
    uid = f"event-{event_id}@schedule-bot"
    
    ics_event = f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{created_at}
DTSTART;TZID=Asia/Singapore:{start_utc}
SUMMARY:{title}
DESCRIPTION:{event.get('notes', '')}
CATEGORIES:{event.get('category', 'other')}
END:VEVENT
"""
    return ics_event


async def export_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all events 2 ICS file."""
    chat_id = update.effective_chat.id
    events = db.get_active_events(chat_id)
    
    if not events:
        await update.message.reply_text(
            "no events 2 export yet 📭\n"
            "add some events first w/ /add"
        )
        return
    
    # Build ICS content
    ics_content = ICS_HEADER
    
    event_count = 0
    for event in events:
        ics_event = create_ics_event(event)
        if ics_event:
            ics_content += ics_event
            event_count += 1
    
    ics_content += ICS_FOOTER
    
    # Send as file
    ics_file = io.BytesIO(ics_content.encode())
    ics_file.name = "schedule.ics"
    
    await update.message.reply_document(
        document=ics_file,
        caption=f"ur calendar 📅\n{event_count} events ready 2 import\n\n"
                f"open this file w/ ur calendar app 2 sync automatically ✨"
    )


def build_export_handler():
    """Build /exportcalendar command."""
    return CommandHandler("exportcalendar", export_calendar)
