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
    "i told my class the schedule it was too demanding. it didn't take it personally tho 😅",
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
    "i'm not saying i'm addicted 2 planning trips but i've got tabs open for 47 hotels rn",
    "trip planning: where 'leaving 2morrow' becomes 'leaving... eventually' 💀",
    "packing 4 a trip is just choosing which anxiety 2 travel with",
    "the only thing longer than a flight is the checklist 2 prepare 4 it",
    "i tried 2 make a chemistry joke but there was no reaction. much like my social life ah",
    "why did the scarecrow win an award? he was outstanding in his field",
    "i would avoid the sushi if i were u. it's a little fishy",
    "why don't scientists trust atoms? because they make up everything",
    "did u hear about the mathematician who's afraid of negative numbers? he'll stop at nothing 2 avoid them",
    "why did the coffee file a police report? it got mugged",
    "i'm reading a book on anti-gravity. it's impossible 2 put down",
    "what do u call a bear with no teeth? a gummy bear",
    "why don't eggs tell jokes? they'd crack each other up",
    "i used 2 hate facial hair, but then it grew on me",
    "what's the best thing about switzerland? i dunno, but their flag is a big plus",
    "why did the student do multiplication problems on the floor? the teacher told him not 2 use tables",
    "i'm afraid 4 the calendar. its days r numbered",
    "what do u call a sleeping bull? a bulldozer",
    "why did the golfer bring 2 pairs of pants? in case he got a hole in one",
    "what did the ocean say 2 the beach? nothing, it just waved",
    "why don't skeletons fight each other? they don't have the guts",
    "what do u call a fake noodle? an impasta",
    "why did the chicken go 2 the séance? 2 talk 2 the other side",
    "i would tell u a udp joke, but u might not get it",
    "what's orange and sounds like a parrot? a carrot",
    "why did the programmer quit his job? because he didn't get arrays",
    "why do java developers wear glasses? because they can't c#",
    "how many programmers does it take 2 change a light bulb? none, that's a hardware problem",
    "why did the deadline cross the road? 2 get away from me",
    "what's the difference between a poorly dressed man on a bicycle and a well-dressed man on a tricycle? attire",
    "why don't scientists play cards in the jungle? because of all the cheetahs",
    "what do u call a guy with a rubber toe? roberto",
    "why did the tomato turn red? because it saw the salad dressing",
    "what do u call a alligator in a vest? an investigator",
    "i tried 2 catch some fog yesterday. mist",
    "what do u call a bear in the rain? a drizzly bear",
    "why did the cookie go 2 the doctor? because it felt crumbly",
    "what do u call a dog magician? a labracadabrador",
    "why did the eyeball go 2 the party? 2 get eyeballed",
    "what did one wall say 2 the other wall? i'll meet u at the corner",
    "why don't eggs tell secrets? because they might crack under pressure",
    "what do u call a pile of cats? a meow-ntain",
    "why did the scarecrow go 2 school? 2 get a little brainier",
    "what do u get if u cross a sheep and a kangaroo? a woolly jumper",
    "why did the biscuit go 2 the doctor? because it felt crumbly",
    "what do u call a sleeping dog? a bulldozer (wait, did i already say this one...)",
    "why don't you ever see hippos hiding in trees? because they're so good at it",
    "what's the best thing about switzerland? i don't know, but the flag is a big plus (ok this one too)",
    "why can't you hear a pterodactyl going 2 the bathroom? because the p is silent",
    "what do u call a fish wearing a bowtie? sofishticated",
    "why did the bicycle fall over? it was 2 tired",
    "what do u call a pig that does karate? a pork chop",
    "why did the stadium get hot? all the fans left",
    "what do u call a gorilla with a banana in each ear? anything u want, he can't hear u",
    "why did the music teacher go 2 jail? because she got caught with her sharp object",
    "what do u call a bear with no teeth and no hair? a gummy bear (ok that's 2)",
    "why don't oysters share their pearls? because they're shellfish",
    "what do u call a nosy pepper? jalapeno",
    "i would tell u a secret but u probably already know it. it's all over reddit",
    "why did the person put their calendar in the safe? they wanted 2 keep their days numbered",
    "what do u call a bear that plays in the rain? a rainy day bear",
    "why don't scientists trust atoms? they make up everything (yes, again, it's that good)",
    "what's a programmer's favorite hangout place? foo bar",
    "why did the schedule go 2 therapy? it had too many issues 2 handle",
    "what do u call a military alarm? an alert",
    "why did the recruit bring a ladder 2 the base? they wanted 2 take training 2 the next level",
    "what do u call a shift that never ends? overtime... literally",
    "why do programmers prefer dark mode? because light attracts bugs",
    "i'm on a seafood diet. i see food and i eat it",
    "what's the difference between a poorly dressed man on a bicycle and a well-dressed man on a tricycle? attire (this one's worth repeating)",
    "why don't we ever tell secrets in the cornfield? because the corn has ears",
    "what do u call a sleeping parrot? a polygon",
    "why did the invisible man turn down the job? he couldn't see himself doing it",
]

ENCOURAGEMENT = [
    "u got this, champ ",
    "i believe in u even if nobody else does (which they prob do btw)",
    "ur gonna absolutely smash this",
    "so proud of u 4 even trying eh",
    "this is it — ur moment",
    "go show the world what ur made of",
    "i'll b here cheering u on always ok",
    "ur stronger than u think, trust bro trust",
    "the fact that u are trying to prepare already means ur halfway there",
]

DATE_VIBES = [
    "ooh date night? cute 🥰",
    "ahhhh someone is a romantic today",
    "ahhh someone's getting their love on",
    "this is gonna be so cute, but you are cuter",
    "treat them well ok. you are a keeper 💕",
    "going out? fancy fancy. i approve 👍",
]

TRIP_VIBES = [
    "adventures calling! passport ready? ✈️",
    "ooh where u going. i'm excited 4 u ",
    "travel bucket ticking off soon! nice",
    "go explore, see the world",
    "can't wait 2 hear ur stories when ur back",
    "safe travels bestie! bring back some good memories",
]

WORK_VIBES = [
    "grinding it out, i see 💼",
    "bring ur A-game 2 this one",
    "ur gonna handle this like a pro",
    "work work work, but remember 2 breathe ok",
    "get that bread! 💪",
]

CLASS_VIBES = [
    "class time! knowledge incoming 📚",
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
    "u studied 4 this, trust urself lol",
    "go in there & ace it, i'm rooting 4 u (but also you dont have a choice)",
    "exam? more like ur time 2 not choke. jk love you ✨",
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

