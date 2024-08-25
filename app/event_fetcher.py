import datetime as dt
import os
from datetime import date, datetime
from typing import Union, Optional

import requests
from dateutil import tz
from dateutil.rrule import rrulestr
from dotenv import load_dotenv
from icalendar import Calendar

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
            event = {}
            dtstart = _ensure_datetime(component.get('dtstart').dt)
            dtend = _ensure_datetime(component.get('dtend').dt)

            event['title'] = component.get('summary')
            event['description'] = component.get('description')
            event['start'] = dtstart.isoformat()
            event['end'] = dtend.isoformat()
            event['recurrence'] = False

            if 'RRULE' in component:
                rrule = rrulestr(component.get('RRULE').to_ical().decode(), dtstart=dtstart)
                next_event_occurance = rrule.after(week_start)

                if next_event_occurance:
                    event['start'] = next_event_occurance.isoformat()
                    event['end'] = (next_event_occurance + (dtend - dtstart)).isoformat()
                    event['recurrence'] = component.get('RRULE')
                    
                    # Flatten dict if only value has only one element
                    event['recurrence'] = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in event['recurrence'].items()}
                    
                    if 'UNTIL' in event['recurrence']:
                        event['recurrence']['UNTIL'] = _ensure_datetime(event['recurrence']['UNTIL'])
                        event['recurrence']['UNTIL'] = event['recurrence']['UNTIL'].isoformat()

                    events.append(event)
            elif dtstart >= week_start:
                events.append(event)

    # Sort events by start date
    events = sorted(events, key=lambda x: x['start'])

    return events

def fetch_events(current_time: Optional[datetime]=None) -> dict:
    """
    Fetches events from a given ICS URL and returns them as a dictionary.

    Args:
        current_time (datetime, optional): The current time to filter events. Defaults to None.

    Returns:
        dict: A dictionary containing the fetched events or an error message.
    """

    if current_time is None:
        current_time = datetime.now(tz=tz.UTC)

    try:
        ics_content = _fetch_ics_from_url(ICS_URL)
        events = _get_events_from_ics(ics_content, current_time)
    except Exception as e:
        return {"events": None, "error": str(e)}

    return {"events": events}
