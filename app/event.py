import re
from dataclasses import dataclass, field
from typing import Optional
from marshmallow_dataclass import class_schema
from marshmallow import EXCLUDE
import datetime as dt
import dateutil.rrule


@dataclass
class EventRecurrence:
    text: str = field(init=False)
    rrule: str


    def __post_init__(self):
        
        try:
            rrule_object = dateutil.rrule.rrulestr(self.rrule)
            self.text = self._rrule_to_text(rrule_object)
        except Exception as e:
            # Handle invalid rrule strings
            self.text = f"Invalid rrule: {self.rrule}"
            print(f"Error initializing rrule: {e}")

    def _rrule_to_text(self, rrule: dateutil.rrule.rrule) -> str:
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

@dataclass
class Event:
    title_raw: str
    description: str
    start_datetime: dt.datetime = field(metadata={"exclude": True})
    end_datetime: dt.datetime  = field(metadata={"exclude": True})
    recurrence: Optional[EventRecurrence] = None

    title: str = field(init=False)
    start: str = field(init=False)
    end: str = field(init=False)
    is_all_day: bool = field(init=False)


    def __post_init__(self):
        self.title_raw = self.title_raw.strip()
        self.title = ' '.join(self.title_raw.split()[:3]).upper()

        self.start = self.start_datetime.isoformat()
        self.end = self.end_datetime.isoformat()

        self.is_all_day = self.start_datetime.time() == dt.time.min and self.end_datetime.time() == dt.time.min

        self.description = self._clean_html(self.description) if self.description else ''

    def _clean_html(self, input_string):
        # Replace various tags that imply new lines with \n
        input_string = re.sub(r'<br\s*/?>', '\n', input_string, flags=re.IGNORECASE)    # <br>
        input_string = re.sub(r'<hr\s*/?>', '\n', input_string, flags=re.IGNORECASE)    # <hr>
        
        # Replace newline HTML entities with \n
        input_string = re.sub(r'&#10;', '\n', input_string)  # ASCII Line Feed (LF)
        input_string = re.sub(r'&#13;', '\n', input_string)  # ASCII Carriage Return (CR)
        
        # Remove all other HTML tags
        cleaned_string = re.sub(r'<[^>]+>', '', input_string)
        
        # Strip leading/trailing whitespace
        return cleaned_string.strip()


BaseEventSchema = class_schema(Event)

class EventSchema(BaseEventSchema):
    def __init__(self, *args, **kwargs):
        # Set default options
        kwargs.setdefault("many", True)
        kwargs.setdefault("unknown", EXCLUDE)
        super().__init__(*args, **kwargs)