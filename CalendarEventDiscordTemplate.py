from CalendarEvent import CalendarEvent
from dataclasses import asdict
from typing import Any


class CalendarEventDiscordTemplate:
    def __init__(self, event: CalendarEvent):
        self.event = event
        event.start_datetime = int(event.start_datetime.timestamp())
        event.end_datetime = int(event.end_datetime.timestamp())

        event.description = self.cut_string(event.description, 100)
        event.eligibility = self.cut_string(event.eligibility, 50)
        event.requirements = self.cut_string(event.requirements, 50)

        self.event_as_dict = asdict(event)
        self._str = str()

        self._append_not_none(Templates.HEADER, True)
        self._append_not_none(Templates.ELIGIBILITY, self.event.eligibility)
        self._append_not_none(Templates.REQUIREMENTS, self.event.requirements)
        self._append_not_none(Templates.ADDITIONAL_REQUIREMENTS, self.event.addition_requirements)
        self._append_not_none(Templates.INFO_LINK, self.event.info_link)
        self._append_not_none(Templates.VIDEO_LINK, self.event.video_link)
        self._append_not_none(Templates.IMAGE_LINK, self.event.image_link)

    def _append_not_none(self, template: str, variable: Any = True):
        if variable is not None:
            self._str += template.format(**self.event_as_dict) + '\n'

    def __str__(self):
        return self._str

    @staticmethod
    def cut_string(the_string: str, chars_limit: int) -> str:
        if the_string is not None:
            if len(the_string) > chars_limit:
                return the_string[:chars_limit] + '...'

            else:
                return the_string


class Templates:
    HEADER = """
⠀
⠀
> {activity_type}
> <t:{start_datetime}> – <t:{end_datetime}>
> <{event_link}>
```fix
{title}
```
{description}

**Location**
{location}"""[1:]

    ELIGIBILITY = """
**Eligibility**
{eligibility}"""

    REQUIREMENTS = """
**Requirements**
{requirements}"""

    ADDITIONAL_REQUIREMENTS = """
**Additional Requirements**
{addition_requirements}"""

    INFO_LINK = """
> **Details:**
<{info_link}>"""

    VIDEO_LINK = """
> **Trailer: **
<{video_link}>"""

    IMAGE_LINK = """
{image_link}"""
