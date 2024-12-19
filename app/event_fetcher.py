import datetime as dt
import os
from datetime import datetime
from typing import Optional

import recurring_ical_events
import requests
from dateutil import tz
from dotenv import load_dotenv
from icalendar import Calendar

from app.datetime_converter import ensure_datetime
from app.event import Event, EventList, EventRecurrence

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

def _get_events_from_ics(ics_content: bytes, current_time: datetime) -> EventList:
    """
    Retrieves events from an iCalendar (ICS) content.
    Args:
        ics_content (bytes): The iCalendar content as bytes.
        current_time datetime: The current time.
    Returns:
        EventList: A list of Event objects.
    Raises:
        Exception: If an error occurs while parsing the iCalendar content.
    """
    gcal = Calendar.from_ical(ics_content)
    events = []

    # Ensure current_time is in UTC timezone if provided else use current time
    current_time = ensure_datetime(current_time)

    # Get the start of the week, meaning monday of the current week at midnight
    week_start = current_time - dt.timedelta(days=current_time.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    for component in gcal.walk():
        if component.name == "VEVENT":
            event = Event.from_ical_event(component)

            if 'RRULE' in component:
                recurring_events = recurring_ical_events.of(component)
                next_event_occurance = next((event for event in recurring_events.after(week_start)), None)

                if next_event_occurance:
                    event = Event.from_ical_event(next_event_occurance)
                    event.recurrence = EventRecurrence(component.get('RRULE').to_ical().decode())

                    events.append(event)
            elif event.start_datetime >= week_start:
                events.append(event)

    # Sort events by start date
    events = sorted(events, key=lambda x: x.start_datetime)

    return EventList(events)

def fetch_events(current_time: Optional[datetime]=None) -> EventList:
    """
    Fetches events from the ICS URL and returns a list of dictionaries representing the events.
    Args:
        current_time (Optional[datetime]): The current time to use for filtering events. If not provided, the current UTC time will be used.
    Returns:
        EventList: A list of Event objects.
    """
    if current_time is None:
        current_time = datetime.now(tz=tz.UTC)

    ics_content = _fetch_ics_from_url(ICS_URL)
    events: EventList = _get_events_from_ics(ics_content, current_time)

    return events
