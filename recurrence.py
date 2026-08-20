"""Helpers for turning a stored event into concrete occurrence datetimes,
and for reading rotating shift patterns."""
import json
from dateutil.rrule import rrulestr
from dateutil import parser as dtparser


def parse_dt(s):
    return dtparser.isoparse(s) if isinstance(s, str) else s


def occurrences_between(event, window_start, window_end):
    """Return a list of datetime occurrences for `event` within [window_start, window_end]."""
    start_dt = parse_dt(event["start_dt"])
    if not event.get("rrule"):
        if window_start <= start_dt <= window_end:
            return [start_dt]
        return []

    rule = rrulestr(event["rrule"], dtstart=start_dt)
    return list(rule.between(window_start, window_end, inc=True))


SHIFT_LABELS = {
    "morning": "🌅 Morning shift",
    "afternoon": "☀️ Afternoon shift",
    "off": "💤 Day off",
}


def shift_for_date(shift_cycle, target_date):
    """Return the shift label (e.g. 'morning') for `target_date`,
    given a shift_cycle row (anchor_date + pattern)."""
    if not shift_cycle:
        return None
    anchor = dtparser.isoparse(shift_cycle["anchor_date"]).date()
    pattern = shift_cycle["pattern"]
    if isinstance(pattern, str):
        pattern = json.loads(pattern)
    delta_days = (target_date - anchor).days
    idx = delta_days % len(pattern)
    return pattern[idx]
