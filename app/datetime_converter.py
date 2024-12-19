import datetime as dt
from datetime import date, datetime
from typing import Union

from dateutil import tz


def ensure_datetime(timestamp: Union[date, datetime]) -> datetime:
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