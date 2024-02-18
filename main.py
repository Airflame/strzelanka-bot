import asyncio
from datetime import datetime
from typing import Any, List

import discord
import os
import roman

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD = os.getenv("DISCORD_GUILD")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
THUMBS_DOWN = ['👎', '👎🏼']
INITIAL_ANNOUNCEMENT = """**RUNDA I**
Głosujemy do 18:00 jutro na album który ma odpaść (emotką 👎 ) i nie można zmieniać głosów"""
ANNOUNCEMENT = """Odpada **%album%** %reactions% głosami %draw_msg%
Głosujemy do 18:00 jutro na album który ma odpaść (emotką 👎 ) i nie można zmieniać głosów
**RUNDA %round%**"""
DRAW_ANNOUNCEMENT = "(remis rostrzygnęła runda %draw_round%)"
INITIAL_LEN = 20
HOUR = "18:00"


def _get_intent() -> discord.Intents:
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    return intents


def count_reactions(message: discord.message.Message) -> int:
    thumbs_down = 0
    for reaction in message.reactions:
        if reaction.emoji in THUMBS_DOWN:
            thumbs_down += reaction.count
    return thumbs_down


class Client(discord.Client):
    def __init__(self, token: str, guild_name: str) -> None:
        super().__init__(intents=_get_intent())

        self._token = token
        self._guild_name = guild_name

    def run(self, *args: Any, **kwargs: Any) -> None:
        (super().run(self._token))

    async def time_loop(self):
        while 1:
            await asyncio.sleep(60)
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            if current_time.startswith(HOUR):
                await self.calculate_results()

    async def calculate_results(self) -> None:
        channel = self.get_channel(CHANNEL_ID)
        points: dict = {}
        albums: List[str] = []
        albums_draw: List[str] = []
        draws: int = 0
        async for h in channel.history(limit=100):
            if 'RUNDA' in h.content:
                if draws == 0:
                    albums = list(points.keys())
                max_reactions = max(points.values())
                if list(points.values()).count(max_reactions) == 1:
                    break
                else:
                    if draws == 0:
                        for key, value in points.items():
                            if value == max_reactions:
                                albums_draw.append(key)
                    draws += 1
            if len(albums) == 0 or h.content in albums_draw:
                if h.content not in points:
                    points[h.content] = 0
                points[h.content] += count_reactions(h)
        round_number: int = INITIAL_LEN + 2 - len(albums)
        removed_album: str = max(points, key=points.get)
        await channel.send(ANNOUNCEMENT
                           .replace('%album%', removed_album)
                           .replace('%reactions%', str(max(points.values())))
                           .replace('%round%', roman.toRoman(round_number))
                           .replace('%draw_msg%', DRAW_ANNOUNCEMENT
                                    .replace('%draw_round%', roman.toRoman(round_number - draws - 1)) if draws > 0 else ""))
        albums.remove(removed_album)
        for album in sorted(albums):
            await channel.send(album)

    async def on_ready(self) -> None:
        await self.time_loop()

    async def on_message(self, message: discord.Message) -> None:
        if message.content.startswith('!list'):
            file_name = message.content.split(' ')[1]
            await self.print_list(file_name)

    async def print_list(self, file_name) -> None:
        channel = self.get_channel(CHANNEL_ID)
        user = ""
        albums_points = {}
        albums_individual_votes = {}
        for element in open(file_name, "r", encoding="utf-8").readlines():
            if "-" not in element:
                user = element.strip()
            else:
                album = element.split(";")[-1].strip()
                points = int(element.split(";")[0])
                if album in albums_points:
                    albums_points[album] += points
                else:
                    albums_points[album] = points
                    albums_individual_votes[album] = {}
                albums_individual_votes[album][user] = points
        template = "%place%. %points% pkt - **%album%** _(%users%)_"
        albums_list = sorted(albums_points.items(), key=lambda item: item[1])
        for index, album in enumerate(albums_list):
            place = len(albums_points) - index
            if place > INITIAL_LEN:
                entry = template.replace("%place%", str(place)).replace("%points%",
                                                                                             str(album[1])).replace(
                    "%album%", album[0])
                users_list = []
                for user, points in sorted(albums_individual_votes[album[0]].items(), key=lambda item: item[1],
                                           reverse=True):
                    users_list.append(user + " - " + str(points))
                entry = entry.replace("%users%", ", ".join(users_list))
                await channel.send(entry)
            else:
                await channel.send(INITIAL_ANNOUNCEMENT)
                albums_list_final = sorted([album[0] for album in albums_list[-INITIAL_LEN:]])
                for album_final in albums_list_final:
                    await channel.send(album_final)
                break


client = Client(DISCORD_TOKEN, DISCORD_GUILD)
client.run()
