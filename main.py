from typing import Any

import discord
import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD = os.getenv("DISCORD_GUILD")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))


def _get_intent() -> discord.Intents:
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    return intents


class Client(discord.Client):
    def __init__(self, token: str, guild_name: str) -> None:
        super().__init__(intents=_get_intent())

        self._token = token
        self._guild_name = guild_name

    def run(self, *args: Any, **kwargs: Any) -> None:
        (super().run(self._token))

    async def on_ready(self) -> None:
        channel = self.get_channel(CHANNEL_ID)
        async for h in channel.history(limit=1):
            await channel.send(h.content)


client = Client(DISCORD_TOKEN, DISCORD_GUILD)
client.run()
