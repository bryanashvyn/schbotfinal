"""Background job: checks upcoming events/offsets every minute and sends
reminders, plus a once-a-day shift + agenda digest."""
import json
import logging
from datetime import datetime, timedelta

from pytz import timezone as pytz_timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import db
import utils
import personality
from recurrence import occurrences_between, shift_for_date, SHIFT_LABELS

logger = logging.getLogger(__name__)

LOOKAHEAD_DAYS = 60      # how far ahead we compute occurrences for recurring events
DIGEST_HOUR = 7          # local hour to send the daily digest
CATCHUP_WINDOW = timedelta(hours=2)  # covers reminders missed during a restart/downtime


async def check_reminders(bot):
    now = datetime.now().astimezone()
    window_end = now + timedelta(days=LOOKAHEAD_DAYS)

    for event in db.get_active_events():
        offsets = json.loads(event["reminder_offsets"])
        for occ in occurrences_between(event, now - timedelta(days=1), window_end):
            for offset in offsets:
                trigger_at = occ - timedelta(minutes=offset)
                # Fires in the normal 1-minute tick, and also catches up on
                # anything missed within the last 2 hours (e.g. bot restart).
                if now - CATCHUP_WINDOW <= trigger_at <= now:
                    occ_key = occ.isoformat()
                    if not db.was_reminder_sent(event["id"], occ_key, offset):
                        try:
                            await send_reminder(bot, event, occ, offset)
                        except Exception:
                            logger.exception("Failed to send reminder for event %s", event["id"])
                            continue
                        db.mark_reminder_sent(event["id"], occ_key, offset)


async def send_reminder(bot, event, occurrence, offset_minutes):
    text = personality.format_reminder(event, occurrence, offset_minutes)
    await bot.send_message(chat_id=event["chat_id"], text=text, parse_mode="Markdown")


async def send_daily_digest(bot, chat_ids):
    for chat_id in chat_ids:
        try:
            # Get user's timezone and local time in that timezone
            tz_str = db.get_user_timezone(chat_id)
            try:
                tz = pytz_timezone(tz_str)
            except:
                tz = pytz_timezone("Asia/Singapore")
            
            now = datetime.now(tz)
            today = now.date()
            day_start = tz.localize(datetime(today.year, today.month, today.day, 0, 0, 0))
            day_end = day_start + timedelta(days=1)

            lines = []
            
            # Morning greeting
            lines.append(f"hey, good morning 🌅\n")
            
            # Add a daily joke
            joke = personality.get_daily_joke(chat_id)
            lines.append(f"dad joke of the day: {joke}\n")
            
            # Shift info
            shift_cycle = db.get_shift_cycle(chat_id)
            if shift_cycle:
                shift = shift_for_date(shift_cycle, today)
                shift_label = SHIFT_LABELS.get(shift, shift)
                lines.append(f"ur shift 2day: {shift_label}\n")

            # Today's events
            todays_events = []
            for event in db.get_active_events(chat_id):
                for occ in occurrences_between(event, day_start, day_end):
                    todays_events.append((event, occ))
            
            if todays_events:
                lines.append("📋 ur day:")
                for event, occ in sorted(todays_events, key=lambda x: x[1]):
                    lines.append(personality.format_digest_entry(event, occ))
                lines.append("")
            
            # Stats
            stats = personality.format_stats(chat_id)
            if stats:
                lines.append(stats)
                lines.append("")
            
            # Countdowns
            countdowns = personality.format_countdowns(chat_id)
            if countdowns:
                lines.append(countdowns)
                lines.append("")
            
            # Closing
            lines.append("go get 'em tiger! 💪")

            if lines:
                await bot.send_message(chat_id=chat_id, text="\n".join(lines))
        except Exception:
            logger.exception("Failed to send daily digest to chat %s", chat_id)


async def _daily_digest_job(bot):
    """Check each user if it's time for their digest (supports customizable times)."""
    chat_ids = db.get_distinct_chat_ids()
    
    for chat_id in chat_ids:
        try:
            # Get user's timezone and custom digest time
            tz_str = db.get_user_timezone(chat_id)
            digest_hour, digest_minute = db.get_digest_time(chat_id)
            
            try:
                tz = pytz_timezone(tz_str)
            except:
                tz = pytz_timezone("Asia/Singapore")
            
            now = datetime.now(tz)
            
            # Check if it's time for this user's digest
            if now.hour == digest_hour and now.minute == digest_minute:
                await send_daily_digest(bot, [chat_id])
        except Exception:
            logger.exception("Failed to check digest time for chat %s", chat_id)


def setup_scheduler(application):
    scheduler = AsyncIOScheduler()
    # Check reminders every minute
    scheduler.add_job(check_reminders, "interval", minutes=1, args=[application.bot])
    # Check digests every minute (each user has their own time)
    scheduler.add_job(_daily_digest_job, "interval", minutes=1, args=[application.bot])
    scheduler.start()
    return scheduler
