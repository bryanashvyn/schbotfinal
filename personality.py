"""personality.py — all messages in bryan's voice.
lowercase, casual, shortforms, genuinely funny dad jokes + puns, no cringe."""
import random
import json
from datetime import datetime, timedelta
from dateutil import parser as dtparser

import db

# Dad jokes and puns (rotating, no repeats per user per day)
DAD_JOKES = [
    "why did the exam go to the gym? cos it wanted to test its strength lol",
    "i told my class schedule it was too demanding. it didn't take it personally tho 😅",
    "assignments r like dad jokes — they just keep coming and nobody asked for them",
    "what did the calendar say to the clock? 'u're always on time, i'm just trying to get through the day'",
    "exam season? more like 'why-am-i-even-alive' season eh",
    "i used to hate monday mornings. then i realised every morning is a monday 4 someone",
    "coffee & i have a relationship. it keeps me awake, i keep it warm",
    "why don't deadlines ever win at poker? they always show their hand too early lol",
    "procrastination is like a credit card — it's fun until u get the bill (aka exam day)",
    "i tried to make a chemistry joke but there was no reaction. much like my social life ah",
    "time flies when ur having fun. time crawls when ur in an exam. physics is weird",
    "they say knowledge is power. clearly they've never met someone sleep-deprived b4 an exam",
    "life hack: replace all ur stress with dad jokes. spoiler: doesn't work but u'll laugh",
    "if ur reading this instead of studying, high five. we're in this 2gether",
    "my therapist: what's stressing u? me: everything. also dad jokes",
    "u know what they call a trip without planning? an adventure. u know what they call planning 2 much? still an adventure, just with anxiety eh",
    "i'm not saying i'm addicted 2 planning trips but i've got tabs open 4 47 hotels rn",
    "trip planning: where 'leaving 2morrow' becomes 'leaving... eventually' 💀",
    "packing 4 a trip is just choosing which anxiety 2 travel with",
    "the only thing longer than a flight is the checklist 2 prepare 4 it",
]

ENCOURAGEMENT = [
    "u got this, champ 💪",
    "i believe in u even if nobody else does (which they prob do btw)",
    "ur gonna absolutely smash this",
    "so proud of u 4 even trying ah",
    "this is it — ur moment",
    "go show the world what ur made of",
    "i'll b here cheering u on eh",
    "ur stronger than u think, trust me",
    "the fact that ur prepared already means ur halfway there",
]

DATE_VIBES = [
    "ooh date night? cute 🥰",
    "romance alert incoming eh",
    "ahhh someone's getting their love on",
    "this is gonna b so nice, i can feel it",
    "treat her well ok. she's a keeper 💕",
    "going out? fancy fancy. i approve 👍",
]

TRIP_VIBES = [
    "adventures calling! passport ready? ✈️",
    "ooh where u going. i'm excited 4 u eh",
    "travel bucket ticking off soon! nice",
    "go explore, see the world",
    "can't wait 2 hear ur stories when ur back",
    "safe travels bestie! bring back some good memories",
]

WORK_VIBES = [
    "grinding it out, i see 💼",
    "bring ur a-game 2 this one",
    "ur gonna handle this like a pro",
    "work work work, but remember 2 breathe ok",
    "get that bread! 💪",
]

CLASS_VIBES = [
    "class time! learnings incoming 📚",
    "ur brain's about 2 get smarter, buckle up",
    "knowledge is power, go get some",
    "i hope prof's got the good stuff 2 teach 2day",
    "pay attention eh, will help later",
]

ASSIGNMENT_VIBES = [
    "assignment szn. u got this",
    "one more thing 2 the never-ending list 💀",
    "it's not that bad, u'll figure it out",
    "take it one step at a time, no rushing",
    "u've done harder things, this is nothing",
]

EXAM_VIBES = [
    "exam time! show it who's boss 🚀",
    "all those study sessions r about 2 pay off ah",
    "confidence is key. and also preparation. mostly preparation lol",
    "u studied 4 this, trust urself",
    "go in there & ace it, i'm rooting 4 u",
    "exam? more like ur time 2 shine ✨",
]

CATEGORY_VIBES = {
    "exam": EXAM_VIBES,
    "class": CLASS_VIBES,
    "assignment": ASSIGNMENT_VIBES,
    "date": DATE_VIBES,
    "trip": TRIP_VIBES,
    "work": WORK_VIBES,
    "keydate": ENCOURAGEMENT,
    "other": ENCOURAGEMENT,
}


def get_random_vibe(category):
    """Pick a random encouraging message for this category."""
    vibes = CATEGORY_VIBES.get(category, ENCOURAGEMENT)
    return random.choice(vibes)


def get_daily_joke(chat_id):
    """Get a joke, rotating so no repeats per user per day."""
    # Store which jokes user's seen today
    today = datetime.now().date().isoformat()
    seen_key = f"jokes_seen:{chat_id}:{today}"
    
    try:
        seen_ids = json.loads(db.get_user_state(chat_id, seen_key) or "[]")
    except:
        seen_ids = []
    
    # Get a fresh joke not in seen list
    available = [i for i, _ in enumerate(DAD_JOKES) if i not in seen_ids]
    if not available:
        # Reset if they've seen them all (unlikely)
        available = list(range(len(DAD_JOKES)))
        seen_ids = []
    
    idx = random.choice(available)
    seen_ids.append(idx)
    db.set_user_state(chat_id, seen_key, json.dumps(seen_ids))
    
    return DAD_JOKES[idx]


def format_reminder(event, occurrence, offset_minutes):
    """Format a reminder message in your voice."""
    category = event["category"]
    vibe = get_random_vibe(category)
    
    when_text = _humanize_offset(offset_minutes)
    
    text = (
        f"⏰ *{event['title']}*\n"
        f"{vibe}\n\n"
        f"when: {occurrence.strftime('%a %d %b, %I:%M %p')}\n"
        f"reminder: {when_text}"
    )
    if event.get("notes"):
        text += f"\nnotes: {event['notes']}"
    
    return text


def format_digest_entry(event, occurrence):
    """Format a single event for the daily digest."""
    category = event["category"]
    cat_emoji = {
        "exam": "📝",
        "class": "📚",
        "assignment": "✍️",
        "date": "❤️",
        "trip": "✈️",
        "work": "💼",
        "keydate": "🔑",
        "other": "📌",
    }.get(category, "📌")
    
    return f"  {occurrence.strftime('%I:%M %p')} · {cat_emoji} {event['title']}"


def format_countdown(event):
    """Format countdown for trips/exams/important dates."""
    start_dt = dtparser.isoparse(event["start_dt"])
    now = datetime.now().astimezone()
    delta = start_dt - now
    
    if delta.total_seconds() < 0:
        return None  # Event is in the past
    
    days = delta.days
    hours = delta.seconds // 3600
    
    if days > 7:
        return f"{days} days away"
    elif days > 0:
        return f"{days}d {hours}h away"
    elif hours > 0:
        return f"{hours}h away (soon!)"
    else:
        return "happening now or very soon!"


def format_countdowns(chat_id):
    """Format all upcoming countdowns (trips, exams, key dates) for digest."""
    events = db.get_active_events(chat_id)
    
    important = [
        e for e in events
        if e["category"] in ("trip", "exam", "keydate")
    ]
    
    if not important:
        return None
    
    lines = ["🎯 coming up:\n"]
    for event in important[:5]:  # Top 5 only
        countdown = format_countdown(event)
        if countdown:
            lines.append(f"  • {event['title']} — {countdown}")
    
    return "\n".join(lines) if len(lines) > 1 else None


def format_stats(chat_id):
    """Show fun stats about their schedule."""
    events = db.get_active_events(chat_id)
    
    if not events:
        return "no events yet, pretty chill 😎"
    
    counts = {}
    for event in events:
        counts[event["category"]] = counts.get(event["category"], 0) + 1
    
    total = sum(counts.values())
    
    lines = [f"📊 ur juggling {total} things:\n"]
    emojis = {"exam": "📝", "class": "📚", "assignment": "✍️", "date": "❤️",
              "trip": "✈️", "work": "💼", "keydate": "🔑"}
    
    for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
        emoji = emojis.get(cat, "📌")
        lines.append(f"  {emoji} {count} {cat}{'s' if count != 1 else ''}")
    
    # Fun commentary
    if total > 10:
        lines.append("\n(ok someone's busy eh, take a break sometimes 🤍)")
    elif total > 5:
        lines.append("\n(steady pace, i like it)")
    else:
        lines.append("\n(pretty relaxed, nice)")
    
    return "\n".join(lines)


def _humanize_offset(minutes):
    """Convert minutes to human text."""
    if minutes == 0:
        return "at event time"
    if minutes % (60 * 24) == 0:
        days = minutes // (60 * 24)
        return f"{days} day{'s' if days != 1 else ''} before"
    if minutes % 60 == 0:
        hours = minutes // 60
        return f"{hours}h before"
    return f"{minutes}min before"

