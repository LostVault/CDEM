import asyncio
import queue
import signal
import threading
from threading import Thread
import discord
from queue import Queue
from discord.ext import tasks


class DiscordNotifier(discord.Client):
    thread: Thread

    def __init__(self, channel_id: int, *args, **kwargs):
        super().__init__(**kwargs)
        self.messages_queue = Queue()
        self.channel_id = channel_id

    async def on_ready(self):
        # print(f'Logged in as {self.user} (ID: {self.user.id})')
        self.notifier_background_task.start()

    @tasks.loop(seconds=1.0)
    async def notifier_background_task(self):
        try:
            msg: str = self.messages_queue.get_nowait()
            if msg is None:
                self.notifier_background_task.stop()
                await self.close()
                return

            channel: discord.channel.TextChannel = self.get_channel(self.channel_id)
            message = await channel.send(msg)
            await message.publish()

        except queue.Empty:
            return

        except discord.HTTPException:
            return

    @notifier_background_task.before_loop
    async def notifier_wait_ready(self):
        await self.wait_until_ready()

    def send(self, msg: str | None) -> None:
        self.messages_queue.put(msg)

    def schedule_stop(self) -> None:
        self.messages_queue.put(None)

    def run_in_thread(self, *args, **kwargs) -> Thread:
        self.thread = Thread(target=lambda: self.loop.run_until_complete(self.start(*args, **kwargs)), daemon=True)
        self.thread.start()
        return self.thread

    def stop(self):
        self.send(None)
        self.thread.join()
