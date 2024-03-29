import asyncio
import dataclasses
import os
import signal
import traceback
from typing import AsyncGenerator
import aiohttp
import discord
import discord.ext.tasks
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


async def new_events_generator() -> AsyncGenerator[CalendarEvent, None]:
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            async with session.get(DB.get_latest_url()) as r:
                r.raise_for_status()
                json_response = await r.json()

            raw_events = json_response['data']
            included = json_response['included']

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

                event = CalendarEvent(
                    drupal_internal_nid=raw_event_attributes['drupal_internal__nid'],
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
                    info_link=(raw_event_attributes.get('field_cal_link', {}) or {}).get('uri', None),
                    video_link=raw_event_attributes['field_cal_video_url'],
                    image_link=raw_event_attributes['field_cal_image_url']
                )

                await event.validate_image()

                if DB.CalendarEvents.select().where(DB.CalendarEvents.drupal_id == event.drupal_id).count() == 0:
                    # We don't have this record in DB
                    # print(f'Yielding {event.title}')
                    yield event
                    DB.CalendarEvents.create(**dataclasses.asdict(event))

            next_url: str | None = json_response.get('links', {}).get('next', {}).get('href')
            if next_url is not None:
                DB.set_latest_url(next_url)

            else:
                break


class CommunityDrivenEventsMonitor(discord.Client):
    def __init__(self, channel_id: int, *args, **kwargs):
        super().__init__(**kwargs)
        # signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        print('Shutdown callbacks registered')
        self.channel_id = channel_id
        self.task_started = False

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        if not self.task_started:
            self.notifier_background_task.start()
            self.task_started = True

    def shutdown(self, sig, frame):
        print(f'Shutting down by signal: {sig}')
        asyncio.create_task(self.close())

    @discord.ext.tasks.loop(seconds=float(os.environ['CDEM_EVENTS_PULL_INTERVAL']))
    async def notifier_background_task(self):
        # noinspection PyBroadException
        try:
            channel: discord.channel.TextChannel = self.get_channel(self.channel_id)
            async for new_event in new_events_generator():
                message = await channel.send(str(CalendarEventDiscordTemplate(new_event)))
                if os.environ.get('CDEM_PUBLISH', 'True').lower() == 'True'.lower():
                    await message.publish()

        except Exception:
            print(traceback.format_exc())

    @notifier_background_task.before_loop
    async def notifier_wait_ready(self):
        await self.wait_until_ready()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = CommunityDrivenEventsMonitor(
        int(os.environ['CDEM_DISCORD_CHANNEL_ID']),
        loop=loop,
        intents=discord.Intents.default()
    )
    loop.run_until_complete(client.start(os.environ['CDEM_DISCORD_TOKEN']))
