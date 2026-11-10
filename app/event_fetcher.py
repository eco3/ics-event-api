import datetime as dt
import os
from collections import defaultdict
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

# (connect, read) timeout in seconds for fetching the upstream calendar
FETCH_TIMEOUT = (5, 15)


def fetch_ics(url: Optional[str] = None) -> bytes:
    """
    Fetches the content of an ICS file from the given URL (defaults to ICS_URL).
    Args:
        url (str): The URL of the ICS file.
    Returns:
        bytes: The content of the ICS file as bytes.
    Raises:
        requests.RequestException: If the request fails, times out or returns a non-successful status code.
    """
    response = requests.get(url or ICS_URL, timeout=FETCH_TIMEOUT)
    response.raise_for_status()  # Ensure we notice bad responses
    return response.content


def _first_rrule(component) -> str:
    """Returns the component's RRULE as a string. icalendar gives a list when there are several; use the first."""
    rrule = component.get('RRULE')
    if isinstance(rrule, list):
        rrule = rrule[0]
    return rrule.to_ical().decode()

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

    # Group VEVENTs by UID so a recurring master is expanded together with its
    # RECURRENCE-ID overrides (moved or edited single occurrences)
    series = defaultdict(list)
    for index, component in enumerate(gcal.walk('VEVENT')):
        series[str(component.get('UID') or f'no-uid-{index}')].append(component)

    for components in series.values():
        master = next((c for c in components if 'RRULE' in c), None)

        if master is not None:
            series_calendar = Calendar()
            for component in components:
                series_calendar.add_component(component)

            occurrences = recurring_ical_events.of(series_calendar).after(week_start)
            next_occurrence = next(iter(occurrences), None)

            if next_occurrence:
                event = Event.from_ical_event(next_occurrence)
                event.recurrence = EventRecurrence(_first_rrule(master))
                events.append(event)
        else:
            for component in components:
                event = Event.from_ical_event(component)
                # Keep events that are still running at the week start
                if event.end_datetime > week_start or event.start_datetime >= week_start:
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

    ics_content = fetch_ics()
    events: EventList = _get_events_from_ics(ics_content, current_time)

    return events
