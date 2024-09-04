from dataclasses import dataclass
from typing import Optional
from marshmallow_dataclass import class_schema


@dataclass
class EventRecurrence:
    text: str
    rrule: str

@dataclass
class Event:
    title: str
    title_raw: str
    description: str
    start: str
    end: str
    is_all_day: bool
    recurrence: Optional[EventRecurrence]

EventSchema = class_schema(Event)
