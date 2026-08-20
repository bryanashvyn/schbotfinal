"""/list, /today, /delete, /categories."""
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

import db
import event_ops
from recurrence import occurrences_between, shift_for_date, SHIFT_LABELS
from handlers.add_event import CATEGORIES

LIST_LOOKAHEAD_DAYS = 30


async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    now = datetime.now().astimezone()
    window_end = now + timedelta(days=LIST_LOOKAHEAD_DAYS)

    upcoming = []
    for event in db.get_active_events(chat_id):
        for occ in occurrences_between(event, now, window_end):
            upcoming.append((occ, event))

    if not upcoming:
        await update.message.reply_text(f"Nothing in the next {LIST_LOOKAHEAD_DAYS} days.")
        return

    upcoming.sort(key=lambda pair: pair[0])
    lines = [f"📋 Next {LIST_LOOKAHEAD_DAYS} days:\n"]
    for occ, event in upcoming[:40]:
        cat_label = CATEGORIES.get(event["category"], event["category"])
        lines.append(
            f"#{event['id']} · {occ.strftime('%a %d %b, %I:%M%p')} · "
            f"{cat_label} · {event['title']}"
        )
    await update.message.reply_text("\n".join(lines))


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    now = datetime.now().astimezone()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    lines = []
    cycle = db.get_shift_cycle(chat_id)
    if cycle:
        shift = shift_for_date(cycle, now.date())
        lines.append(SHIFT_LABELS.get(shift, shift))

    todays = []
    for event in db.get_active_events(chat_id):
        for occ in occurrences_between(event, day_start, day_end):
            todays.append((occ, event))
    todays.sort(key=lambda pair: pair[0])

    if todays:
        lines.append("\n📋 Today:")
        for occ, event in todays:
            cat_label = CATEGORIES.get(event["category"], event["category"])
            lines.append(f"  {occ.strftime('%I:%M%p')} · {cat_label} · {event['title']}")
    elif not cycle:
        lines.append("Nothing on today.")

    await update.message.reply_text("\n".join(lines))


async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /delete <id>  (see /list for ids)")
        return
    try:
        event_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("That doesn't look like a valid id.")
        return

    chat_id = update.effective_chat.id
    deleted = event_ops.delete_event(chat_id, event_id)
    await update.message.reply_text(
        f"Deleted ✅ — {deleted['title']}" if deleted else "Couldn't find that event id."
    )


async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    counts = {}
    for event in db.get_active_events(chat_id):
        counts[event["category"]] = counts.get(event["category"], 0) + 1
    if not counts:
        await update.message.reply_text("No events yet — use /add to create one.")
        return
    lines = [f"{CATEGORIES.get(cat, cat)}: {n}" for cat, n in counts.items()]
    await update.message.reply_text("\n".join(lines))
