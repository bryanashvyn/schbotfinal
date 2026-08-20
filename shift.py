"""/setshift conversation + /shift display command."""
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)

import db
import event_ops
import utils
from recurrence import shift_for_date, SHIFT_LABELS

ANCHOR_DATE, ANCHOR_SHIFT = range(2)

SHIFT_CHOICES = {
    "morning": "🌅 Morning",
    "afternoon": "☀️ Afternoon",
    "off": "💤 Off",
}


async def setshift_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setshift — ask 4 date."""
    await update.message.reply_text(
        "let's set up ur shift cycle (2 morning/2 afternoon/2 off)\n"
        "what date does ur next cycle start? (e.g., 'tmr', '18 aug', 'next monday')"
    )
    return ANCHOR_DATE


async def anchor_date_given(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse anchor date."""
    date_input = update.message.text.strip()
    
    # Use flexible parsing
    parsed_dt = utils.parse_datetime_flexible(date_input)
    if not parsed_dt:
        await update.message.reply_text(
            "couldn't parse that. try: 'tmr', '18 aug', 'next monday'"
        )
        return ANCHOR_DATE
    
    anchor_date = parsed_dt.date()
    context.user_data["shift_anchor"] = anchor_date.isoformat()
    
    # Ask 4 which shift on that date
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"ashift:{key}")]
        for key, label in SHIFT_CHOICES.items()
    ]
    
    date_str = anchor_date.strftime("%a %d %b")
    await update.message.reply_text(
        f"{date_str} — what shift?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return ANCHOR_SHIFT


async def anchor_shift_given(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store shift & create cycle."""
    query = update.callback_query
    await query.answer()
    
    shift = query.data.split(":", 1)[1]
    chat_id = update.effective_chat.id
    
    from dateutil import parser as dtparser
    anchor_date = dtparser.isoparse(context.user_data["shift_anchor"]).date()
    
    # Create shift cycle
    synced = event_ops.set_shift(chat_id, anchor_date, shift)
    
    sync_note = " (synced 2 apple 📅)" if synced else ""
    
    await query.edit_message_text(
        f"shift cycle set up ✅\n"
        f"starting {anchor_date.strftime('%a %d %b')}, {shift} shift"
        f"{sync_note}"
    )


async def shift_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/shift — show ur shift 4 next 7 days."""
    chat_id = update.effective_chat.id
    shift_cycle = db.get_shift_cycle(chat_id)
    
    if not shift_cycle:
        await update.message.reply_text(
            "u haven't set up a shift cycle yet. use /setshift 2 start 🌅"
        )
        return
    
    lines = ["🌅 ur shifts:\n"]
    today = datetime.now().date()
    
    for i in range(7):
        date = today + timedelta(days=i)
        shift = shift_for_date(shift_cycle, date)
        shift_label = SHIFT_LABELS.get(shift, shift)
        lines.append(f"  {date.strftime('%a %d %b')}: {shift_label}")
    
    await update.message.reply_text("\n".join(lines))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel /setshift."""
    await update.message.reply_text("ok, cancelled 👍")
    return ConversationHandler.END


def build_setshift_handler():
    """Build /setshift conversation."""
    return ConversationHandler(
        entry_points=[CommandHandler("setshift", setshift_start)],
        states={
            ANCHOR_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, anchor_date_given)],
            ANCHOR_SHIFT: [CallbackQueryHandler(anchor_shift_given, pattern="^ashift:")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
