import traceback
from dataclasses import dataclass, field, asdict
import aiohttp
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
    image_link: str | None  # if image link is invalid or not exists, it is None

    async def validate_image(self):
        # print(f'Checking image validity for {self.image_link!r}')
        if self.image_link is None:
            # print('image_link is None')
            return

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.image_link) as r:
                    r.raise_for_status()

            except Exception:
                self.image_link = None
                print(f'URL check failed for: {self.image_link!r}')
                print(traceback.format_exc())
                return

        # print('Link is valid')

    def __post_init__(self):
        self.sort_index = int(self.start_datetime.timestamp())
        if self.addition_requirements == "None":
            self.addition_requirements = None
