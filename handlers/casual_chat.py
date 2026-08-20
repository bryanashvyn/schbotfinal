"""Simple casual chat responses."""
import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# Casual messages & responses
CASUAL_PATTERNS = {
    r"^(hi|hey|hello|yo|sup|hiya)": [
        "yo! what's up 👋",
        "hey there! 😎",
        "hello! need help w/ ur schedule?",
        "sup! 👋",
    ],
    r"(bye|goodbye|see u|cya|later|adios)": [
        "catch u later! 👋",
        "bye! take care 🤍",
        "see u soon! 👋",
        "adios! 🌊",
    ],
    r"^(thanks|thank u|thx|ty|appreciate)": [
        "anytime! happy 2 help 🤍",
        "np! 😊",
        "ur welcome! 👍",
        "glad i could help!",
    ],
    r"^(lol|haha|lmao|rofl)": [
        "😂",
        "haha 💀",
        "lol 😅",
        "u got it 👌",
    ],
    r"(how r u|how are u|how u doing|how's it going|wbu)": [
        "living my best bot life! 🤖 how's ur day going?",
        "all good! just here 2 keep ur schedule tight. u good?",
        "can't complain! how's ur schedule looking?",
    ],
    r"(what's up|whatsup|wat up)": [
        "nm, just helping u stay organized 📅",
        "same old same old! u?",
        "just vibing, what about u?",
    ],
    r"(good morning|morning|gm)": [
        "good morning! ☀️ ready 4 the day?",
        "morning! 🌅 check ur digest yet?",
    ],
    r"(good night|night|gnight|sleep well)": [
        "good night! sleep tight 😴",
        "nite! 🌙",
    ],
    r"(ok|alright|sounds good|got it)": [
        "awesome 👍",
        "nice! 😎",
        "let's go! 🚀",
    ],
    r"(sorry|my bad|oops)": [
        "no worries! happens 2 all of us 🤍",
        "all good lah! 👍",
        "no stress!",
    ],
}


async def handle_casual_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respond 2 casual messages."""
    text = update.message.text.strip().lower()
    
    # Check if it's a casual message
    for pattern, responses in CASUAL_PATTERNS.items():
        if re.search(pattern, text):
            response = responses[hash(text) % len(responses)]
            await update.message.reply_text(response)
            return True
    
    return False


def get_casual_chat_handler():
    """Return a handler 4 casual chat."""
    # This should run BEFORE other handlers
    return MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        _casual_chat_wrapper
    )


async def _casual_chat_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wrapper that checks 4 casual chat b4 passing 2 NLU."""
    if await handle_casual_chat(update, context):
        # Casual message was handled, don't pass 2 NLU
        return
    
    # If not casual, pass 2 NLU
    import nlu
    await nlu.handle_message(update, context, update.message.text)
