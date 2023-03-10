"""
Builds a Discord Bot with certain flags enabled and a database
connection, as needed by the Fake Basketball Bot.
Copyright (C) 2022 Fake CBB Developers

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from aiosqlite import Connection
import discord
from discord.ext import commands


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        allowed_mentions = discord.AllowedMentions.all()
        allowed_mentions.replied_user = False
        intents = discord.Intents.default()
        intents.members, intents.message_content = True, True

        self.db: Connection = kwargs.pop("db")
        self.logger = kwargs.pop('logger')

        async def fetchone(*args):
            """Executes and returns the first of certain query to the database."""
            return list(await self.db.execute_fetchall(*args))[0]
        self.fetchone = fetchone

        async def fetchval(*args):
            """Like fetchone, but returns the first value."""
            if len(row := await self.fetchone(*args)):
                return row[0]
        self.fetchval = fetchval

        super().__init__(**kwargs, allowed_mentions=allowed_mentions, intents=intents)
