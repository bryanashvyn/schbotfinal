"""Natural-language front door: free-text messages get interpreted by
Claude and routed to the same event_ops functions the button-based
commands use, so behaviour is identical either way."""
import os
import json
import logging
from datetime import datetime

from dotenv import load_dotenv
from dateutil import parser as dtparser

import db
import calendar_sync
import event_ops
from handlers.add_event import CATEGORIES

load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

_client = None
if API_KEY:
    from anthropic import Anthropic
    _client = Anthropic(api_key=API_KEY)


def is_configured():
    return _client is not None


TOOLS = [
    {
        "name": "add_event",
        "description": (
            "Create a new schedule entry: class, exam, assignment, date, trip, "
            "work appointment, key work date, or other."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "category": {"type": "string", "enum": list(CATEGORIES.keys())},
                "start_datetime": {
                    "type": "string",
                    "description": "ISO 8601 local datetime of the first/only occurrence",
                },
                "recurrence": {
                    "type": "string",
                    "enum": list(event_ops.RECURRENCE_OPTIONS.keys()),
                    "description": "'none' for a one-off event",
                },
                "weekdays": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]},
                    "description": "Required if recurrence is weekly or biweekly",
                },
                "reminder_offsets_minutes": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Minutes before the event to remind, e.g. 1440 for a day before. Default [0] if unspecified.",
                },
                "notes": {"type": "string"},
            },
            "required": ["title", "category", "start_datetime", "recurrence"],
        },
    },
    {
        "name": "delete_event",
        "description": "Delete/cancel an existing upcoming event, matched by title.",
        "input_schema": {
            "type": "object",
            "properties": {"title_search": {"type": "string"}},
            "required": ["title_search"],
        },
    },
    {
        "name": "list_events",
        "description": "Show the user's upcoming events (next 30 days).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "show_today",
        "description": "Show today's shift and today's events.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "set_shift",
        "description": "Configure the rotating 2-morning/2-afternoon/2-off work cycle.",
        "input_schema": {
            "type": "object",
            "properties": {
                "anchor_date": {"type": "string", "description": "ISO date of a day whose shift is known"},
                "first_shift": {"type": "string", "enum": ["morning", "afternoon", "off"]},
            },
            "required": ["anchor_date", "first_shift"],
        },
    },
    {
        "name": "show_shift",
        "description": "Show the shift for the next 7 days.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "reply",
        "description": (
            "Reply conversationally when nothing above applies — greetings, small talk, "
            "or when required info is missing (ask a short follow-up question here "
            "instead of guessing)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
]

SYSTEM_PROMPT = """You are the natural-language front end for a personal scheduling \
Telegram bot. The user juggles classes (often biweekly), exams, assignments, dates \
with their girlfriend, trips, work appointments, key work dates, and a rotating \
2-day-morning / 2-day-afternoon / 2-day-off work shift.

Always call exactly one tool per message. Resolve relative dates ("next Friday", \
"in 2 weeks") against the current local datetime given below. If something required \
is missing or ambiguous (e.g. no time given for an event that needs one), use the \
`reply` tool to ask one short, specific follow-up question rather than guessing.

Current local datetime: {now}
"""


async def handle_message(update, context, text):
    chat_id = update.effective_chat.id
    if not is_configured():
        await update.message.reply_text(
            "Free-text chat isn't set up yet (ANTHROPIC_API_KEY missing from .env) "
            "— try /add or /help for commands."
        )
        return

    now = datetime.now().astimezone()
    try:
        resp = _client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT.format(now=now.isoformat()),
            tools=TOOLS,
            messages=[{"role": "user", "content": text}],
        )
    except Exception:
        logger.exception("Anthropic call failed")
        await update.message.reply_text("Had trouble understanding that — mind rephrasing, or try /add?")
        return

    tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
    if not tool_use:
        text_block = next((b for b in resp.content if b.type == "text"), None)
        await update.message.reply_text(text_block.text if text_block else "Sorry, I didn't catch that.")
        return

    await _dispatch(update, context, chat_id, tool_use.name, tool_use.input)


async def _dispatch(update, context, chat_id, name, args):
    if name == "reply":
        await update.message.reply_text(args["text"])
    elif name == "add_event":
        await _do_add_event(update, chat_id, args)
    elif name == "delete_event":
        await _do_delete_event(update, chat_id, args["title_search"])
    elif name == "list_events":
        from handlers.browse import list_events
        await list_events(update, context)
    elif name == "show_today":
        from handlers.browse import today
        await today(update, context)
    elif name == "set_shift":
        await _do_set_shift(update, chat_id, args)
    elif name == "show_shift":
        from handlers.shift import shift_show
        await shift_show(update, context)
    else:
        await update.message.reply_text("Not sure how to do that yet — try /help.")


async def _do_add_event(update, chat_id, args):
    try:
        start_dt = dtparser.parse(args["start_datetime"])
    except (ValueError, OverflowError):
        await update.message.reply_text("Couldn't quite parse that date/time — could you restate it?")
        return
    if start_dt.tzinfo is None:
        start_dt = start_dt.astimezone()

    _event_id, synced = event_ops.create_event(
        chat_id=chat_id, title=args["title"], category=args["category"], start_dt=start_dt,
        recurrence=args.get("recurrence", "none"), weekdays=args.get("weekdays"),
        reminder_offsets=args.get("reminder_offsets_minutes"), notes=args.get("notes"),
    )

    note = " (synced to Google Calendar)" if synced else (
        " (⚠️ Google Calendar sync failed — saved locally only)"
        if calendar_sync.is_connected(chat_id) else ""
    )
    when = start_dt.strftime("%a %d %b %Y, %I:%M %p")
    await update.message.reply_text(f"Got it — {args['title']} on {when} ✅{note}")


async def _do_delete_event(update, chat_id, title_search):
    matches = event_ops.find_events_by_title(chat_id, title_search)
    if not matches:
        await update.message.reply_text(f"Couldn't find anything matching \"{title_search}\".")
        return
    if len(matches) > 1:
        lines = [f"#{e['id']} · {e['title']}" for e in matches]
        await update.message.reply_text(
            "A few things match — use /delete <id> for the one you mean:\n" + "\n".join(lines)
        )
        return

    deleted = event_ops.delete_event(chat_id, matches[0]["id"])
    await update.message.reply_text(f"Deleted \"{deleted['title']}\" ✅")


async def _do_set_shift(update, chat_id, args):
    try:
        anchor_date = dtparser.isoparse(args["anchor_date"]).date()
    except (ValueError, OverflowError):
        await update.message.reply_text("Couldn't parse that date — could you restate it?")
        return

    synced = event_ops.set_shift(chat_id, anchor_date, args["first_shift"])
    note = " Synced to Google Calendar too." if synced else ""
    await update.message.reply_text(f"Shift pattern saved ✅{note}")
