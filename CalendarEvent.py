from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass(order=True)
class CalendarEvent:
    sort_index: int = field(init=False)
    drupal_id: int  # int(drupal_internal__nid.__str__ + drupal_internal__vid.__str__)
    start_datetime: datetime
    end_datetime: datetime
    title: str
    location: str
    description: str
    eligibility: str
    requirements: str
    addition_requirements: str
    info_link: str
    video_link: str
    image_link: str

    def __post_init__(self):
        self.sort_index = int(self.start_datetime.timestamp())


def format_calendar_event(event: CalendarEvent) -> str:
    import json

    def serialize_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

    return json.dumps(asdict(event), default=serialize_datetime, indent=4)
