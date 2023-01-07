"""
File that provides the launch code for the Fake Basketball Bot.
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

import asyncio
import json

import discord
from discord.ext import commands

from bot import Bot


async def login():
    """Logs into Discord and database and runs the bot."""
    with open('configuration.json', 'r') as configuration_file:
        configuration = json.load(configuration_file)
    client = Bot(command_prefix=configuration['prefix'], help_command=commands.MinimalHelpCommand())

    @client.event
    async def on_ready():
        # Saves connection and info to logs
        print(f"Logged in as\n{client.user}\n{client.user.id}")

    @client.command()
    async def ping(ctx):
        return await ctx.reply('Pong!')

    try:
        await client.start(configuration['token'])
    except KeyboardInterrupt:
        await client.close()


if __name__ == '__main__':
    asyncio.run(login())
