"""Conservative English deadline normalization anchored to the source timestamp."""
import re
from datetime import datetime, timedelta
from dateutil import parser

WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

def normalize_deadline(text: str | None, timestamp: datetime):
    if not text or not text.strip():
        return None, None, None
    value = text.lower().strip()
    day = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    # Relative days take precedence over a parenthesized weekday.
    if 'tomorrow' in value:
        day += timedelta(days=1)
    elif 'today' in value or re.search(r'\bthis (morning|evening|afternoon)\b', value):
        pass
    elif 'this week' in value:
        day += timedelta(days=(4 - day.weekday()) % 7)
    else:
        weekday = next((i for i, name in enumerate(WEEKDAYS) if name in value), None)
        if weekday is not None and not re.search(r'\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', value):
            delta = (weekday - day.weekday()) % 7
            if 'next ' in value and delta == 0:
                delta = 7
            day += timedelta(days=delta)
        elif re.search(r'\d{4}-\d{2}-\d{2}|\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', value):
            try:
                day = parser.parse(value, fuzzy=True, default=day).replace(hour=0, minute=0, second=0, microsecond=0)
            except (ValueError, OverflowError):
                return None, 'UNRESOLVED', 'The date expression could not be resolved safely.'
        elif not any(x in value for x in ('end of day', 'eod', 'morning', 'evening', 'afternoon')):
            # A time-only expression is permitted; other ambiguous text stays unknown.
            if not re.search(r'\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b', value):
                return None, 'UNRESOLVED', 'No supported date anchor in evidence.'
    clock = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', value)
    iso_clock = re.search(r'(?:t|\s)(\d{2}):(\d{2})(?::\d{2})?', value)
    if clock:
        hour, minute = int(clock[1]), int(clock[2] or 0)
        if not 1 <= hour <= 12 or minute > 59:
            return None, 'UNRESOLVED', 'Invalid clock time.'
        hour = hour % 12 + (12 if clock[3] == 'pm' else 0)
        return day.replace(hour=hour, minute=minute), 'EXACT', None
    if iso_clock:
        try:
            return day.replace(hour=int(iso_clock[1]), minute=int(iso_clock[2])), 'EXACT', None
        except ValueError:
            return None, 'UNRESOLVED', 'Invalid clock time.'
    for phrase, hour in [('morning', 12), ('afternoon', 17), ('evening', 20)]:
        if phrase in value:
            return day.replace(hour=hour), 'PART_OF_DAY', f'{phrase} is represented by its configured window end ({hour:02}:00); the source gave no exact time.'
    if value.startswith('before '):
        return day, 'DAY_BOUNDARY', 'Before the named day is represented by the start of that day; no meeting time was inferred.'
    return day.replace(hour=23, minute=59, second=59), 'DAY', 'Date-only / end-of-day deadline represented as 23:59:59, not an asserted business closing time.'
