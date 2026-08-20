CATEGORIES = {
    "class": "📚 Class",
    "exam": "📝 Exam",
    "assignment": "🧾 Assignment",
    "date": "❤️ Date",
    "trip": "✈️ Trip",
    "work": "💼 Work",
    "keydate": "🔑 Key date",
    "other": "📌 Other",
}

"""/add conversation: simple & natural flow with flexible date parsing."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)

import db
import event_ops
import utils

# States
WAITING_TITLE = 1
WAITING_DATE = 2
WAITING_RECURRENCE = 3
WAITING_WEEKDAYS = 4
WAITING_REMINDERS = 5
CONFIRM = 6

RECURRENCE_OPTIONS = event_ops.RECURRENCE_OPTIONS
WEEKDAY_CODES = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /add — ask 4 event name."""
    context.user_data["event_data"] = {}
    await update.message.reply_text(
        "what's the event? (e.g., 'exam', 'lunch w/ sarah', 'ippt')"
    )
    return WAITING_TITLE


async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process title, detect category, ask 4 date."""
    title = update.message.text.strip()
    if not title or len(title) > 100:
        await update.message.reply_text("give me a title 1-100 chars")
        return WAITING_TITLE
    
    # Auto-detect category
    category = utils.detect_category(title)
    
    context.user_data["event_data"]["title"] = title
    context.user_data["event_data"]["category"] = category
    
    await update.message.reply_text(
        f"ok — '{title}' ({category})\n\n"
        f"when? (e.g., 'tmr', 'tmr 2pm', 'sep 20 8am', 'next monday')"
    )
    return WAITING_DATE


async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse date/time, ask 4 recurrence."""
    date_input = update.message.text.strip()
    
    # Try flexible parsing
    parsed_dt = utils.parse_datetime_flexible(date_input)
    if not parsed_dt:
        await update.message.reply_text(
            "couldn't parse that. try: 'tmr', 'tmr 2pm', 'sep 20', 'next monday'"
        )
        return WAITING_DATE
    
    context.user_data["event_data"]["datetime"] = parsed_dt
    
    # Format 4 display
    date_str = parsed_dt.strftime("%a %d %b")
    time_str = parsed_dt.strftime("%I:%M %p")
    
    # Ask 4 recurrence
    keyboard = [
        [InlineKeyboardButton("One-off", callback_data="recur:none")],
        [InlineKeyboardButton("Weekly", callback_data="recur:weekly")],
        [InlineKeyboardButton("Every 2 weeks", callback_data="recur:biweekly")],
        [InlineKeyboardButton("Monthly", callback_data="recur:monthly")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{date_str}, {time_str}\n\nrepeat?",
        reply_markup=reply_markup
    )
    return WAITING_RECURRENCE


async def handle_recurrence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle recurrence choice."""
    query = update.callback_query
    await query.answer()
    
    choice = query.data.split(":")[1]
    context.user_data["event_data"]["recurrence"] = choice
    
    # If weekly/biweekly, ask 4 weekdays
    if choice in ("weekly", "biweekly"):
        keyboard = [
            [
                InlineKeyboardButton("Mo", callback_data="day:MO"),
                InlineKeyboardButton("Tu", callback_data="day:TU"),
                InlineKeyboardButton("We", callback_data="day:WE"),
                InlineKeyboardButton("Th", callback_data="day:TH"),
            ],
            [
                InlineKeyboardButton("Fr", callback_data="day:FR"),
                InlineKeyboardButton("Sa", callback_data="day:SA"),
                InlineKeyboardButton("Su", callback_data="day:SU"),
            ],
            [InlineKeyboardButton("Done", callback_data="day:done")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "pick days (tap again 2 toggle):",
            reply_markup=reply_markup
        )
        context.user_data["event_data"]["weekdays"] = []
        return WAITING_WEEKDAYS
    
    # Otherwise skip 2 reminders
    await ask_for_reminders(query, context)
    return WAITING_REMINDERS


async def handle_weekdays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle weekday selection."""
    query = update.callback_query
    await query.answer()
    
    choice = query.data.split(":")[1]
    
    if choice == "done":
        await ask_for_reminders(query, context)
        return WAITING_REMINDERS
    
    # Toggle the selected day
    weekdays = context.user_data["event_data"]["weekdays"]
    if choice in weekdays:
        weekdays.remove(choice)
    else:
        weekdays.append(choice)
    
    context.user_data["event_data"]["weekdays"] = weekdays
    
    # Redraw buttons with selection
    keyboard = [
        [
            InlineKeyboardButton(
                f"Mo {'✓' if 'MO' in weekdays else ''}", callback_data="day:MO"
            ),
            InlineKeyboardButton(
                f"Tu {'✓' if 'TU' in weekdays else ''}", callback_data="day:TU"
            ),
            InlineKeyboardButton(
                f"We {'✓' if 'WE' in weekdays else ''}", callback_data="day:WE"
            ),
            InlineKeyboardButton(
                f"Th {'✓' if 'TH' in weekdays else ''}", callback_data="day:TH"
            ),
        ],
        [
            InlineKeyboardButton(
                f"Fr {'✓' if 'FR' in weekdays else ''}", callback_data="day:FR"
            ),
            InlineKeyboardButton(
                f"Sa {'✓' if 'SA' in weekdays else ''}", callback_data="day:SA"
            ),
            InlineKeyboardButton(
                f"Su {'✓' if 'SU' in weekdays else ''}", callback_data="day:SU"
            ),
        ],
        [InlineKeyboardButton("Done", callback_data="day:done")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "pick days (tap again 2 toggle):",
        reply_markup=reply_markup
    )
    return WAITING_WEEKDAYS


async def ask_for_reminders(query_or_update, context):
    """Helper 2 ask 4 reminder settings."""
    keyboard = [
        [InlineKeyboardButton("At time", callback_data="rem:0")],
        [InlineKeyboardButton("15 min before", callback_data="rem:15")],
        [InlineKeyboardButton("1h before", callback_data="rem:60")],
        [InlineKeyboardButton("1 day before", callback_data="rem:1440")],
        [InlineKeyboardButton("Custom", callback_data="rem:custom")],
        [InlineKeyboardButton("Skip", callback_data="rem:skip")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    title = context.user_data["event_data"]["title"]
    
    if hasattr(query_or_update, "edit_message_text"):
        # It's a callback query
        await query_or_update.edit_message_text(
            f"remind me about '{title}'?",
            reply_markup=reply_markup
        )
    else:
        # It's a regular update
        await query_or_update.reply_text(
            f"remind me about '{title}'?",
            reply_markup=reply_markup
        )


async def handle_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reminder choice."""
    query = update.callback_query
    await query.answer()
    
    choice = query.data.split(":")[1]
    
    if choice == "custom":
        await query.edit_message_text(
            "how many mins/hours/days before? (e.g., '1 hour', '2 days')"
        )
        return WAITING_REMINDERS
    elif choice == "skip":
        context.user_data["event_data"]["reminders"] = [0]
        await create_event(query, context)
        return ConversationHandler.END
    else:
        context.user_data["event_data"]["reminders"] = [int(choice)]
        await create_event(query, context)
        return ConversationHandler.END


async def create_event(query, context):
    """Create the event & show confirmation."""
    data = context.user_data["event_data"]
    chat_id = query.from_user.id
    
    event_id, synced = event_ops.create_event(
        chat_id=chat_id,
        title=data["title"],
        category=data["category"],
        start_dt=data["datetime"],
        recurrence=data.get("recurrence", "none"),
        weekdays=data.get("weekdays", []),
        reminder_offsets=data.get("reminders", [0]),
    )
    
    if not event_id:
        await query.edit_message_text("oops, something went wrong 😅")
        return
    
    # Format confirmation
    date_str = data["datetime"].strftime("%a %d %b")
    time_str = data["datetime"].strftime("%I:%M %p")
    
    reminders_str = ""
    if data.get("reminders") and data["reminders"] != [0]:
        reminder_labels = [utils.humanize_offset(r) for r in data["reminders"]]
        reminders_str = f"\nremind: {', '.join(reminder_labels)}"
    
    sync_note = " (synced 2 apple 📅)" if synced else ""
    
    await query.edit_message_text(
        f"got it — {data['title']}\n"
        f"when: {date_str}, {time_str}"
        f"{reminders_str}"
        f"{sync_note}"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel /add."""
    await update.message.reply_text("ok, cancelled 👍")
    return ConversationHandler.END


def build_conversation_handler():
    """Build the /add conversation."""
    return ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            WAITING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title)],
            WAITING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date)],
            WAITING_RECURRENCE: [CallbackQueryHandler(handle_recurrence, pattern="^recur:")],
            WAITING_WEEKDAYS: [CallbackQueryHandler(handle_weekdays, pattern="^day:")],
            WAITING_REMINDERS: [CallbackQueryHandler(handle_reminders, pattern="^rem:")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
