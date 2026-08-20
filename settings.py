"""Settings commands: /setdigesttime, /stats, /countdown, /timezone"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

import db
import personality


async def set_digest_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set when you want your daily digest. /setdigesttime 8 30 for 8:30am"""
    if not context.args or len(context.args) < 1:
        current_hour, current_min = db.get_digest_time(update.effective_chat.id)
        await update.message.reply_text(
            f"usage: /setdigesttime <hour> [minute]\n"
            f"example: /setdigesttime 8 30 for 8:30am\n\n"
            f"ur digest time rn: {current_hour:02d}:{current_min:02d}"
        )
        return
    
    try:
        hour = int(context.args[0])
        minute = int(context.args[1]) if len(context.args) > 1 else 0
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("hour must b 0-23, minute must b 0-59")
        
        db.set_digest_time(update.effective_chat.id, hour, minute)
        await update.message.reply_text(
            f"got it! ur digest is now @ {hour:02d}:{minute:02d} every morning 🌅"
        )
    except (ValueError, IndexError):
        await update.message.reply_text("that didn't look right eh. try `/setdigesttime 8 30`")


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show schedule stats"""
    chat_id = update.effective_chat.id
    stats = personality.format_stats(chat_id)
    await update.message.reply_text(stats)


async def show_countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show countdowns for upcoming trips, exams, key dates"""
    chat_id = update.effective_chat.id
    countdowns = personality.format_countdowns(chat_id)
    
    if countdowns:
        await update.message.reply_text(countdowns)
    else:
        await update.message.reply_text("nothing major coming up soon, ur good 😎")


async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set your timezone. /timezone Asia/Singapore or Asia/Kolkata"""
    if not context.args:
        current_tz = db.get_user_timezone(update.effective_chat.id)
        await update.message.reply_text(
            f"usage: /timezone <timezone>\n"
            f"examples: Asia/Singapore, Asia/Kolkata, Europe/London\n"
            f"ur current timezone: {current_tz}\n\n"
            f"see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones 4 full list"
        )
        return
    
    tz_name = " ".join(context.args)
    try:
        from pytz import timezone as pytz_timezone
        pytz_timezone(tz_name)  # Validate it exists
        
        db.set_digest_time(update.effective_chat.id, 7, 0, tz_name)
        await update.message.reply_text(f"timezone set 2 {tz_name}! all times will b in ur local zone now 🌍")
    except:
        await update.message.reply_text(f"hmm, {tz_name} isn't a valid timezone. check the list here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones")


async def daily_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get a random dad joke"""
    joke = personality.get_daily_joke(update.effective_chat.id)
    await update.message.reply_text(f"😂 {joke}")


def build_settings_handlers():
    return [
        CommandHandler("setdigesttime", set_digest_time),
        CommandHandler("stats", show_stats),
        CommandHandler("countdown", show_countdown),
        CommandHandler("timezone", set_timezone),
        CommandHandler("joke", daily_joke),
    ]
