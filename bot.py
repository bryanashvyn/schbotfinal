"""Entry point: wires up handlers and starts polling + the reminder scheduler."""
import logging
import os

from dotenv import load_dotenv
load_dotenv()  # must run before any module-level os.environ reads below

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import db
from handlers.start import start, help_cmd
from handlers.add_event import build_conversation_handler
from handlers.shift import build_setshift_handler, shift_show
from handlers.browse import list_events, today, delete_event, categories
from handlers.export_calendar import build_export_handler
from handlers.settings import build_settings_handlers
from handlers.edit import build_edit_handler
from handlers.casual_chat import get_casual_chat_handler
from scheduler import setup_scheduler
import nlu

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


async def on_startup(application):
    setup_scheduler(application)

async def main():
    import db
    db.init_db()  # Initialize Postgres tables
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
def main():
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in your .env file first (see .env.example).")

    db.init_db()

    app = ApplicationBuilder().token(TOKEN).post_init(on_startup).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(build_conversation_handler())
    app.add_handler(build_setshift_handler())
    app.add_handler(CommandHandler("shift", shift_show))
    app.add_handler(CommandHandler("list", list_events))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("delete", delete_event))
    app.add_handler(CommandHandler("categories", categories))
    app.add_handler(build_edit_handler())
    app.add_handler(build_export_handler())
    for handler in build_settings_handlers():
        app.add_handler(handler)

    # Casual chat (hi, bye, thanks) runs BEFORE NLU
    app.add_handler(get_casual_chat_handler())

    # Registered last: only fires when no /add or /setshift conversation is
    # active for this chat, since those own their own text states.
    async def nlu_router(update, context):
        await nlu.handle_message(update, context, update.message.text)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, nlu_router))

    app.run_polling()


if __name__ == "__main__":
    main()
