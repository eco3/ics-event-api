import datetime as dt
import os
from datetime import date, datetime
from typing import Optional, Union

import dateutil.rrule
import requests
from dateutil import tz
from dotenv import load_dotenv
from icalendar import Calendar

from app.event import Event, EventRecurrence

load_dotenv()

ICS_URL = os.getenv('ICS_URL')


def _fetch_ics_from_url(url: str) -> bytes:
    """
    Fetches the content of an ICS file from the given URL.
    Args:
        url (str): The URL of the ICS file.
    Returns:
        bytes: The content of the ICS file as bytes.
    Raises:
        requests.HTTPError: If the HTTP request to the URL fails or returns a non-successful status code.
    """
    response = requests.get(url)
    response.raise_for_status()  # Ensure we notice bad responses
    return response.content

def _ensure_datetime(timestamp: Union[date, datetime]) -> datetime:
    """
    Ensures that the given datetime object is in UTC timezone.
    Args:
        timestamp (date or datetime): The datetime object to be ensured.
    Returns:
        datetime: The datetime object in UTC timezone.
    """
    if isinstance(timestamp, date) and not isinstance(timestamp, datetime):
        timestamp = datetime.combine(timestamp, dt.time.min, tzinfo=tz.UTC)
    
    # convert to UTC timezone
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=tz.UTC)
    else:
        timestamp = timestamp.astimezone(tz.UTC)

    return timestamp

def _rrule_to_text(rrule: dateutil.rrule.rrule) -> str:
    """
    Converts a dateutil rrule object to a human-readable text representation.
    Args:
        rrule (dateutil.rrule.rrule): The rrule object to be converted.
    Returns:
        str: The human-readable text representation of the rrule.
    """
    freq_map = {
        dateutil.rrule.DAILY: "DAILY",
        dateutil.rrule.WEEKLY: "WEEKLY",
        dateutil.rrule.MONTHLY: "MONTHLY",
        dateutil.rrule.YEARLY: "YEARLY"
    }
    
    interval = rrule._interval
    freq = rrule._freq
    
    if freq in freq_map:
        if interval == 1:
            return freq_map[freq]
        elif interval == 2 and freq == dateutil.rrule.WEEKLY:
            return "BI-WEEKLY"
        elif interval == 2 and freq == dateutil.rrule.DAILY:
            return "BI-DAILY"
        else:
            return f"EVERY {interval} {freq_map[freq]}"
    else:
        return "REPEATING"

def _get_events_from_ics(ics_content: bytes, current_time: datetime) -> list[dict]:
    """
    Retrieves events from an iCalendar (ICS) content.
    Args:
        ics_content (bytes): The iCalendar content as bytes.
        current_time datetime: The current time.
    Returns:
        list: A list of event dictionaries, each containing the following keys:
            - 'title': The title of the event.
            - 'description': The description of the event.
            - 'start': The start date and time of the event in ISO format.
            - 'end': The end date and time of the event in ISO format.
            - 'recurrence': A dictionary representing the RRULE of the event, or False if the event does not recur.
    Raises:
        Exception: If an error occurs while parsing the iCalendar content.
    """
    gcal = Calendar.from_ical(ics_content)
    events = []

    # Ensure current_time is in UTC timezone if provided else use current time
    current_time = _ensure_datetime(current_time)

    # Get the start of the week, meaning monday of the current week at midnight
    week_start = current_time - dt.timedelta(days=current_time.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    for component in gcal.walk():
        if component.name == "VEVENT":
            dtstart = _ensure_datetime(component.get('dtstart').dt)
            dtend = _ensure_datetime(component.get('dtend').dt)

            title_raw = component.get('summary')
            title = ' '.join(title_raw.strip().split()[:3]).upper()
            description = component.get('description')
            start = dtstart.isoformat()
            end = dtend.isoformat()
            is_all_day = dtstart.time() == dt.time.min and dtend.time() == dt.time.min
            recurrence = None

            event = Event(title, title_raw, description, start, end, is_all_day, recurrence)

            if 'RRULE' in component:
                rrule_raw = component.get('RRULE').to_ical().decode()
                rrule = dateutil.rrule.rrulestr(rrule_raw, dtstart=dtstart)
                next_event_occurance = rrule.after(week_start)

                if next_event_occurance:
                    event.start = next_event_occurance.isoformat()
                    event.end = (next_event_occurance + (dtend - dtstart)).isoformat()

                    event.recurrence = EventRecurrence(text=_rrule_to_text(rrule), rrule=rrule_raw)

                    events.append(event)
            elif dtstart >= week_start:
                events.append(event)

    # Sort events by start date
    events = sorted(events, key=lambda x: x.start)

    return events

def fetch_events(current_time: Optional[datetime]=None) -> list[dict]:
    """
    Fetches events from the ICS URL and returns a list of dictionaries representing the events.
    Args:
        current_time (Optional[datetime]): The current time to use for filtering events. If not provided, the current UTC time will be used.
    Returns:
        list[dict]: A list of dictionaries representing the events. Each dictionary contains information about an event.
    """
    if current_time is None:
        current_time = datetime.now(tz=tz.UTC)

    ics_content = _fetch_ics_from_url(ICS_URL)
    events = _get_events_from_ics(ics_content, current_time)

    return events
