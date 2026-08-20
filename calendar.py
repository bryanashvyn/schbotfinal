"""Calendar handlers for Apple iCloud Calendar sync."""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters

import db
import calendar_sync_apple as calendar_sync

# Conversation states
WAITING_EMAIL = 1
WAITING_PASSWORD = 2


async def connect_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Apple Calendar connection flow."""
    await update.message.reply_text(
        "let's connect ur apple calendar! 📅\n\n"
        "first, what's ur icloud email? (the one u use 4 ur apple account)"
    )
    return WAITING_EMAIL


async def connect_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store email and ask for password."""
    email = update.message.text.strip()
    context.user_data["apple_email"] = email
    
    await update.message.reply_text(
        f"got it — {email}\n\n"
        "now, what's ur icloud password? (this is stored securely & only used 2 sync ur calendar)\n\n"
        "⚠️ if u have 2FA enabled, use an app-specific password instead\n"
        "(create one here: https://appleid.apple.com/account/manage)"
    )
    return WAITING_PASSWORD


async def connect_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test connection and store credentials."""
    password = update.message.text.strip()
    email = context.user_data["apple_email"]
    chat_id = update.effective_chat.id
    
    # Test connection
    success, msg = calendar_sync.test_connection(email, password)
    
    if not success:
        await update.message.reply_text(f"connection failed: {msg}\n\nlet's try again — what's ur icloud email?")
        return WAITING_EMAIL
    
    # Store credentials
    calendar_sync.store_credentials(chat_id, email, password)
    
    await update.message.reply_text(
        f"apple calendar connected ✅\n"
        f"ur events will now sync 2 ur icloud calendar automatically 🎉"
    )
    return ConversationHandler.END


async def connect_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel connection flow."""
    await update.message.reply_text("ok, cancelled. use /connectcalendar when ur ready 👍")
    return ConversationHandler.END


async def disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disconnect Apple Calendar."""
    calendar_sync.delete_credentials(update.effective_chat.id)
    await update.message.reply_text(
        "apple calendar disconnected 👋\n\n"
        "(events already synced stay in ur calendar — delete them there if u want)"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Apple Calendar connection status."""
    connected = calendar_sync.check_connection(update.effective_chat.id)
    
    if connected:
        await update.message.reply_text("apple calendar: ✅ connected & syncing")
    else:
        await update.message.reply_text(
            "apple calendar: not connected.\n"
            "use /connectcalendar 2 set it up 📅"
        )


def build_calendar_handlers():
    """Build all calendar-related handlers."""
    connect_handler = ConversationHandler(
        entry_points=[CommandHandler("connectcalendar", connect_start)],
        states={
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, connect_email)],
            WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, connect_password)],
        },
        fallbacks=[CommandHandler("cancel", connect_cancel)],
    )
    
    return [
        connect_handler,
        CommandHandler("disconnectcalendar", disconnect),
        CommandHandler("calendarstatus", status),
    ]
