"""Edit existing events: /edit command."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)

import db
import utils

# States
WAITING_EVENT_ID = 1
WAITING_FIELD = 2
WAITING_NEW_VALUE = 3
CONFIRM = 4

EDIT_FIELDS = {
    "title": "Title",
    "datetime": "Date & time",
    "reminders": "Reminders",
    "category": "Category",
}


async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /edit — show events 2 choose from."""
    chat_id = update.effective_chat.id
    events = db.get_active_events(chat_id)
    
    if not events:
        await update.message.reply_text("u don't have any events 2 edit 📭")
        return ConversationHandler.END
    
    # Show first 10 events
    lines = ["pick an event 2 edit:\n"]
    buttons = []
    
    for event in events[:10]:
        event_id = event["id"]
        title = event["title"]
        start_dt = utils.parse_datetime_flexible(event["start_dt"])
        
        if start_dt:
            date_str = start_dt.strftime("%a %d %b %I:%M %p")
        else:
            date_str = "unknown date"
        
        lines.append(f"  {event_id}. {title} ({date_str})")
        buttons.append([InlineKeyboardButton(f"{event_id}. {title}", callback_data=f"edit_ev:{event_id}")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("\n".join(lines), reply_markup=reply_markup)
    
    return WAITING_EVENT_ID


async def handle_event_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked an event 2 edit."""
    query = update.callback_query
    await query.answer()
    
    event_id = int(query.data.split(":")[1])
    event = db.get_event(event_id)
    
    if not event or event["chat_id"] != update.effective_chat.id:
        await query.edit_message_text("event not found 🤔")
        return ConversationHandler.END
    
    context.user_data["editing_event_id"] = event_id
    context.user_data["editing_event"] = event
    
    # Show field options
    keyboard = [
        [InlineKeyboardButton("Title", callback_data="edit_field:title")],
        [InlineKeyboardButton("Date & time", callback_data="edit_field:datetime")],
        [InlineKeyboardButton("Reminders", callback_data="edit_field:reminders")],
        [InlineKeyboardButton("Category", callback_data="edit_field:category")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"editing '{event['title']}'\n\nwhich field?",
        reply_markup=reply_markup
    )
    
    return WAITING_FIELD


async def handle_field_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked a field 2 edit."""
    query = update.callback_query
    await query.answer()
    
    field = query.data.split(":")[1]
    context.user_data["editing_field"] = field
    
    event = context.user_data["editing_event"]
    
    if field == "title":
        await query.edit_message_text(
            f"current title: '{event['title']}'\n\nnew title?"
        )
    elif field == "datetime":
        dt = utils.parse_datetime_flexible(event["start_dt"])
        if dt:
            current = dt.strftime("%a %d %b %I:%M %p")
        else:
            current = "unknown"
        await query.edit_message_text(
            f"current: {current}\n\nnew date/time? (e.g., 'tmr 2pm', 'sep 20 8am')"
        )
    elif field == "reminders":
        reminders = event.get("reminder_offsets") or [0]
        reminder_strs = [utils.humanize_offset(r) for r in reminders]
        await query.edit_message_text(
            f"current: {', '.join(reminder_strs)}\n\nnew reminders? (e.g., '1 hour before', '2 days before')"
        )
    elif field == "category":
        await query.edit_message_text(
            f"current: {event['category']}\n\nnew category? (exam, class, assignment, date, trip, work, keydate, other)"
        )
    
    return WAITING_NEW_VALUE


async def handle_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User entered new value."""
    new_value = update.message.text.strip()
    field = context.user_data["editing_field"]
    event = context.user_data["editing_event"]
    event_id = context.user_data["editing_event_id"]
    
    # Validate & parse
    if field == "title":
        if not new_value or len(new_value) > 100:
            await update.message.reply_text("title must b 1-100 chars")
            return WAITING_NEW_VALUE
        context.user_data["new_value"] = new_value
    
    elif field == "datetime":
        parsed_dt = utils.parse_datetime_flexible(new_value)
        if not parsed_dt:
            await update.message.reply_text("couldn't parse that. try: 'tmr 2pm', 'sep 20'")
            return WAITING_NEW_VALUE
        context.user_data["new_value"] = parsed_dt
    
    elif field == "reminders":
        reminders = utils.parse_reminder_input(new_value)
        if not reminders:
            reminders = [0]
        context.user_data["new_value"] = reminders
    
    elif field == "category":
        valid_cats = ["exam", "class", "assignment", "date", "trip", "work", "keydate", "other"]
        if new_value.lower() not in valid_cats:
            await update.message.reply_text(f"pick one: {', '.join(valid_cats)}")
            return WAITING_NEW_VALUE
        context.user_data["new_value"] = new_value.lower()
    
    # Show confirmation
    old_value = event.get(field) or "unknown"
    new_display = context.user_data["new_value"]
    
    if field == "datetime":
        old_dt = utils.parse_datetime_flexible(str(old_value))
        old_display = old_dt.strftime("%a %d %b %I:%M %p") if old_dt else str(old_value)
        new_display = new_display.strftime("%a %d %b %I:%M %p")
    elif field == "reminders":
        old_display = ", ".join([utils.humanize_offset(r) for r in (event.get("reminder_offsets") or [0])])
        new_display = ", ".join([utils.humanize_offset(r) for r in new_display])
    else:
        old_display = str(old_value)
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_edit:yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="confirm_edit:no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{field.upper()}\n"
        f"old: {old_display}\n"
        f"new: {new_display}\n\n"
        f"ok?",
        reply_markup=reply_markup
    )
    
    return CONFIRM


async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User confirmed the change."""
    query = update.callback_query
    await query.answer()
    
    choice = query.data.split(":")[1]
    
    if choice == "no":
        await query.edit_message_text("cancelled 👍")
        return ConversationHandler.END
    
    # Apply the change
    event_id = context.user_data["editing_event_id"]
    field = context.user_data["editing_field"]
    new_value = context.user_data["new_value"]
    
    # Update database
    if field == "title":
        db.update_event_field(event_id, "title", new_value)
    elif field == "datetime":
        db.update_event_field(event_id, "start_dt", new_value.isoformat())
    elif field == "reminders":
        db.update_event_field(event_id, "reminder_offsets", new_value)
    elif field == "category":
        db.update_event_field(event_id, "category", new_value)
    
    await query.edit_message_text(f"{field} updated ✅")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel /edit."""
    await update.message.reply_text("ok, cancelled 👍")
    return ConversationHandler.END


def build_edit_handler():
    """Build /edit conversation."""
    return ConversationHandler(
        entry_points=[CommandHandler("edit", edit_start)],
        states={
            WAITING_EVENT_ID: [CallbackQueryHandler(handle_event_choice, pattern="^edit_ev:")],
            WAITING_FIELD: [CallbackQueryHandler(handle_field_choice, pattern="^edit_field:")],
            WAITING_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_value)],
            CONFIRM: [CallbackQueryHandler(handle_confirm, pattern="^confirm_edit:")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
