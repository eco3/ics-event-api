import re
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

    def __post_init__(self):
        self.description = self._clean_html(self.description) if self.description else ''

    def _clean_html(self, input_string):
        # Replace various tags that imply new lines with \n
        input_string = re.sub(r'<br\s*/?>', '\n', input_string, flags=re.IGNORECASE)    # <br>
        input_string = re.sub(r'<hr\s*/?>', '\n', input_string, flags=re.IGNORECASE)    # <hr>
        
        # Replace newline HTML entities with \n
        input_string = re.sub(r'&#10;', '\n', input_string)  # ASCII Line Feed (LF)
        input_string = re.sub(r'&#13;', '\n', input_string)  # ASCII Carriage Return (CR)
        
        # Remove all other HTML tags
        cleaned_string = re.sub(r'<[^>]+>', ' ', input_string)
        
        # Strip leading/trailing whitespace
        return cleaned_string.strip()

EventSchema = class_schema(Event)
