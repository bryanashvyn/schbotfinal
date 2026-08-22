"""Simple casual chat responses."""
import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# Casual messages & responses
CASUAL_PATTERNS = {
    r"^(hi|hey|hello|yo|sup|hiya)": [
        "good morning boss",
        "heyyyyyyy you",
        "hi hi! need help w/ ur schedule?",
        "sup",
        "how can i help you",
        "good morning my fellow brethren, how can i be of assistance",
    ],
    r"(bye|goodbye|see u|cya|later|adios)": [
        "catch u later!",
        "bye! take care",
        "see u next life",
        "adios amigo 🌊",
        "love u bb",
    ],
    r"^(thanks|thank u|thank you|thx|ty|appreciate)": [
        "anytime! happy to help 🤍",
        "np! 😊",
        "ur welcome! 👍",
        "glad i could help!",
    ],
    r"^(lol|haha|lmao|rofl)": [
        "funny fella",
        "💀💀💀",
        "lol",
        "i am a robot",
    ],
    r"(how r u|how are u|how u doing|how's it going|wbu)": [
        "life is tough, how's ur day going?",
        "busy busy busy! u good?",
        "can't complain! how's ur schedule looking?",
    ],
    r"(what's up|whatsup|wat up)": [
        "nm, just helping u stay organized 📅",
        "same old same old! u?",
        "trying to survive, what about u?",
    ],
    r"(good morning|morning|gm)": [
        "good morning! ☀️ lets seize the day lmao",
        "morning! 🌅 with great power comes great responsibility",
    ],
    r"(good night|night|gnight|sleep well)": [
        "good night bb",
        "night is still young my friend!",
        "the world never sleeps",
    ],
    r"(ok|alright|sounds good|got it)": [
        "i gotchu",
        "lets goooooooo",
        "you got this",
    ],
    r"(sorry|my bad|oops)": [
        "no worries! maybe some money next time",
        "all good bro",
        "stress is spelled desserts backwards",
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
