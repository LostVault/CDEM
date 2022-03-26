from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass(order=True)
class CalendarEvent:
    sort_index: int = field(init=False)
    drupal_id: str
    start_datetime: datetime
    end_datetime: datetime
    title: str
    activity_type: str
    location: str
    description: str
    eligibility: str | None
    requirements: str | None
    addition_requirements: str | None
    info_link: str | None
    video_link: str | None
    image_link: str | None

    def __post_init__(self):
        self.sort_index = int(self.start_datetime.timestamp())
        if self.addition_requirements == "None":
            self.addition_requirements = None
