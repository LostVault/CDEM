import asyncio
import dataclasses
import os
import signal
import traceback
from typing import AsyncGenerator, List
import aiohttp
import discord
import discord.ext.tasks
import Constants
from CalendarEvent import CalendarEvent
from CalendarEventDiscordTemplate import CalendarEventDiscordTemplate
from datetime import datetime
import DB


# As a DPY background task:
# 1. Request api
# 2. Check if we have new records
# 3. Send new records to discord


def parse_timestamp(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')


async def new_events_generator() -> AsyncGenerator[str, None]:
    async with aiohttp.ClientSession() as session:
        async with session.get(Constants.EVENTS_FEED) as r:
            r.raise_for_status()
            json_response = await r.json()

    raw_events = json_response['data']
    included = json_response['included']

    events: List[CalendarEvent] = list()

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

    # noinspection PyTypeChecker
    events: List[CalendarEvent] = sorted(events)
    for event in events:
        if DB.CalendarEvents.select().where(DB.CalendarEvents.drupal_id == event.drupal_id).count() == 0:
            await event.validate_image()
            # We don't have this record in DB
            # print(f'Yielding {event.title}')
            yield str(CalendarEventDiscordTemplate(event))
            DB.CalendarEvents.create(**dataclasses.asdict(event))


class CommunityDrivenEventsMonitor(discord.Client):
    def __init__(self, channel_id: int, *args, **kwargs):
        super().__init__(**kwargs)
        # signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        print('Shutdown callbacks registered')
        self.channel_id = channel_id

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        self.notifier_background_task.start()

    def shutdown(self, sig, frame):
        print(f'Shutting down by signal: {sig}')
        asyncio.create_task(self.close())

    @discord.ext.tasks.loop(seconds=float(os.environ['CDEM_EVENTS_PULL_INTERVAL']))
    async def notifier_background_task(self):
        # noinspection PyBroadException
        try:
            channel: discord.channel.TextChannel = self.get_channel(self.channel_id)
            async for msg in new_events_generator():
                message = await channel.send(msg)
                if os.environ.get('CDEM_PUBLISH', 'True').lower() == 'True'.lower():
                    await message.publish()

        except Exception:
            print(traceback.format_exc())

    @notifier_background_task.before_loop
    async def notifier_wait_ready(self):
        await self.wait_until_ready()


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = CommunityDrivenEventsMonitor(int(os.environ['CDEM_DISCORD_CHANNEL_ID']), loop=loop)
loop.run_until_complete(client.start(os.environ['CDEM_DISCORD_TOKEN']))
