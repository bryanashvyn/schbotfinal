"""Shared utilities for parsing, date handling, category detection."""
from datetime import datetime, timedelta
from dateutil import parser as dtparser
import re


def humanize_offset(minutes):
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


def parse_datetime_flexible(date_str, time_str=None):
    """
    Parse date & time flexibly.
    Accepts: "tomorrow", "tmr", "next monday", "18 aug", "18/8", "aug 18", "8am", "2:30pm", etc.
    Returns: aware datetime object or None
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_str = date_str.strip().lower()
    time_str = (time_str or "").strip().lower() if time_str else ""
    
    # Handle special cases
    now = datetime.now().astimezone()
    
    if date_str in ("tmr", "tomorrow", "2morrow"):
        date_obj = now + timedelta(days=1)
        date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_str == "today":
        date_obj = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_str.startswith("next "):
        # "next monday", "next week", etc.
        day_name = date_str[5:].strip()
        try:
            # Find the next occurrence of this day
            test_date = now
            for i in range(1, 8):
                test_date = now + timedelta(days=i)
                if test_date.strftime("%A").lower().startswith(day_name[:3]):
                    date_obj = test_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    break
            else:
                return None
        except:
            return None
    else:
        # Try to parse with dateutil (flexible parser)
        try:
            date_obj = dtparser.parse(date_str, fuzzy=True, default=now.replace(hour=0, minute=0, second=0, microsecond=0))
            date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        except:
            return None
    
    # Parse time
    hour, minute = 8, 0  # Default 2 8am if no time given
    
    if time_str:
        # Handle "8am", "2:30pm", "14:00", "morning", "afternoon", etc.
        time_str = time_str.replace(".", "").strip()
        
        if time_str in ("morning",):
            hour = 8
        elif time_str in ("afternoon",):
            hour = 14
        elif time_str in ("evening", "night"):
            hour = 18
        else:
            # Try 2 extract time with regex
            time_match = re.search(r"(\d{1,2})\s*(?::(\d{2}))?\s*(am|pm)?", time_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                am_pm = time_match.group(3)
                
                if am_pm == "pm" and hour != 12:
                    hour += 12
                elif am_pm == "am" and hour == 12:
                    hour = 0
    
    # Combine date & time
    result = date_obj.replace(hour=hour, minute=minute)
    return result.astimezone()


def detect_category(text):
    """
    Auto-detect event category from text.
    Returns: category string (exam, class, assignment, date, trip, work, keydate, other)
    """
    text = text.lower()
    
    # Keywords 4 each category
    exam_keywords = ["exam", "test", "quiz", "final", "midterm", "assessment"]
    class_keywords = ["class", "lecture", "lesson", "cs101", "math", "meet"]
    assignment_keywords = ["assignment", "assign", "homework", "hw", "project", "paper", "essay", "submission"]
    date_keywords = ["date", "dinner", "lunch", "hangout", "coffee", "movie", "sarah"]
    trip_keywords = ["trip", "travel", "vacation", "holiday", "flight", "airport", "bali", "bombay", "tour"]
    work_keywords = ["ippt", "work", "meeting", "presentation", "report", "deadline", "shift", "standup"]
    keydate_keywords = ["birthday", "anniversary", "wedding", "graduation", "promotion"]
    
    # Check keywords (order matters — check specific b4 general)
    for keyword in exam_keywords:
        if keyword in text:
            return "exam"
    for keyword in trip_keywords:
        if keyword in text:
            return "trip"
    for keyword in assignment_keywords:
        if keyword in text:
            return "assignment"
    for keyword in work_keywords:
        if keyword in text:
            return "work"
    for keyword in class_keywords:
        if keyword in text:
            return "class"
    for keyword in date_keywords:
        if keyword in text:
            return "date"
    for keyword in keydate_keywords:
        if keyword in text:
            return "keydate"
    
    return "other"


def parse_reminder_input(text):
    """
    Parse custom reminder input like "1 hour", "2 days", "30 min", etc.
    Returns: list of minute offsets, or [] if parse fails
    """
    text = text.strip().lower()
    matches = re.findall(r"(\d+)\s*(min|hour|day|week)s?", text)
    
    offsets = []
    for amount_str, unit in matches:
        amount = int(amount_str)
        if unit == "min":
            offsets.append(amount)
        elif unit == "hour":
            offsets.append(amount * 60)
        elif unit == "day":
            offsets.append(amount * 24 * 60)
        elif unit == "week":
            offsets.append(amount * 7 * 24 * 60)
    
    return sorted(offsets) if offsets else []
