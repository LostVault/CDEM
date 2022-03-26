import os
from DiscordNotifier import DiscordNotifier
import Constants
import requests
from CalendarEvent import CalendarEvent
from CalendarEventDiscordTemplate import CalendarEventDiscordTemplate
from datetime import datetime
import DB


# 1. Request api
# 2. Check if we have new records
# 3. Send new records to discord


def parse_timestamp(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')


r = requests.get(Constants.EVENTS_FEED)
r.raise_for_status()

raw_events = r.json()['data']
included = r.json()['included']

events = list()

for raw_event in raw_events:
    event_id = raw_event['id']
    raw_event_relationships = raw_event['relationships']
    activity_type_id = raw_event_relationships['field_cal_activity_types']['data'][0]['id']

    activity_name: str | None = None
    for include in included:
        if include['id'] == activity_type_id:
            activity_name = include['attributes']['name']
            break

    raw_event_attributes = raw_event['attributes']
    events.append(
        CalendarEvent(
            drupal_id=event_id,
            title=raw_event_attributes['title'],
            start_datetime=parse_timestamp(raw_event_attributes['field_cal_start_date_time']),
            end_datetime=parse_timestamp(raw_event_attributes['field_cal_end_date_time']),
            activity_type=activity_name,
            location=raw_event_attributes['field_cal_location'],
            description=raw_event_attributes['field_cal_plain_description'],
            eligibility=raw_event_attributes['field_cal_eligibility'],
            requirements=raw_event_attributes['field_cal_requirements'],
            addition_requirements=raw_event_attributes['field_cal_add_reqs'],
            info_link=raw_event_attributes['field_cal_link']['uri'],
            video_link=raw_event_attributes['field_cal_video_url'],
            image_link=raw_event_attributes['field_cal_image_url']
        )
    )

discord_notifier = DiscordNotifier(int(os.environ['CDEM_DISCORD_CHANNEL_ID']))
discord_notifier.run_in_thread(os.environ['CDEM_DISCORD_TOKEN'])

# noinspection PyTypeChecker
events = sorted(events)
for event in events:
    if DB.CalendarEvents.select().where(DB.CalendarEvents.drupal_id == event.drupal_id).count() == 0:
        # We don't have this record in DB
        discord_notifier.send(str(CalendarEventDiscordTemplate(event)))
        # DB.CalendarEvents.create(**dataclasses.asdict(event))

discord_notifier.stop()
