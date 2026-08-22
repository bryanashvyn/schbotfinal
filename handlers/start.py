from telegram import Update
from telegram.ext import ContextTypes

HELP_TEXT = (
    "🗓 *schedule bot (ur personal assistant)*\n\n"
    "i'm here to keep ur life as organized as it can be. just talk 2 me naturally thx!\n"
    "e.g. \"exam on 5 sep 2pm, remind me a day & 1 hour before\" or \"when's my shift 2morrow?\"\n\n"
    "*adding stuff:*\n"
    "/add — guided buttons 4 new events\n"
    "or just type naturally — i'll figure it out 😎\n\n"
    "*viewing ur life:*\n"
    "/list — all upcoming events (next 30 days)\n"
    "/today — 2day's shift + events\n"
    "/shift — ur shift 4 next 7 days\n"
    "/stats — how many things ur juggling\n"
    "/countdown — trips, exams, key dates coming up\n\n"
    "*managing events:*\n"
    "/delete <id> — remove an event (id from /list)\n"
    "/categories — breakdown by type\n\n"
    "*ur work cycle:*\n"
    "/setshift — set up ur 2-morning/2-afternoon/2-off rotation\n\n"
    "*calendar:*\n"
    "/connectcalendar — sync 2 ur google calendar\n"
    "/disconnectcalendar — stop syncing\n"
    "/calendarstatus — check if synced\n\n"
    "*settings:*\n"
    "/setdigesttime <hour> [min] — when should i send ur daily digest (default 7am)\n"
    "/timezone <tz> — ur timezone (default singapore)\n"
    "/joke — random dad joke\n\n"
    "/cancel — bail out of whatever ur doing\n"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "hey! 👋 i'm ur personal schedule assistant ish.\n"
        "i'll help u keep track of classes, exams, assignments, dates, trips, work shifts, "
        "& all the important stuff — without letting u 4get anything.\n\n"
        "just chat w/ me naturally or use the commands below!\n\n"
        + HELP_TEXT,
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")
