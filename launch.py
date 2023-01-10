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
import logging
import sys
import traceback

import aiosqlite
import discord
from discord.ext import commands

from bot import Bot


async def login():
    """Logs into Discord and database and runs the bot."""
    # Set up logging
    logger = logging.Logger('fake_basketball_bot')
    logger.setLevel(logging.INFO)

    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)

    handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)
    discord_logger.addHandler(handler)

    # Override default exception hook
    def excepthook(e_type, e_value, e_traceback):
        if issubclass(e_type, KeyboardInterrupt):
            logger.info('KeyboardInterrupt detected, stopping!')
            print('\nStopping!', file=sys.stderr)
            return
        logger.critical(''.join(traceback.format_exception(e_type, e_value, tb=e_traceback)))
        sys.__excepthook__(e_type, e_value, e_traceback)

    sys.excepthook = excepthook

    logger.info('Starting bot...')

    # Opens configuration.json and extracts bot settings
    logger.info('Opening configuration.json...')
    try:
        with open('configuration.json', 'r') as configuration_file:
            configuration = json.load(configuration_file)
        prefix = configuration.pop('prefix')
        database_path = configuration.pop('db')
        token = configuration.pop('token')
    except FileNotFoundError:
        logger.critical('configuration.json not found, generating...')
        with open('configuration.json', 'w') as configuration_file:
            configuration_file.write(json.dumps({'prefix': '!', 'db': '', 'token': ''}, indent=2))
        return print('Configuration file not found! Generated new config at configuration.json. Please fill in token and db.', file=sys.stderr)
    except KeyError:
        logger.critical('configuration.json is invalid! Make sure all required fields are filled.')
        return print('Invalid configuration file! Please fix configuration.json or delete it to regenerate.', file=sys.stderr)
    else:
        logger.info('configuration.json found!')

    # Creates Bot object (finally!)
    async with aiosqlite.connect(database=database_path) as db:  # for some reason just creating a cursor object and manually closing it isn't working.
        activity = discord.Activity(type=discord.ActivityType.listening, name='numbers in your games!')
        client = Bot(command_prefix=prefix, db=db, activity=activity, help_command=commands.MinimalHelpCommand(), logger=logger)

        # Set some handlers
        @client.event
        async def on_ready():
            """Confirms and logs a connection."""
            logger.info(f'Connected to Discord as {client.user} (ID: {client.user.id})')
            print(f'Logged in as\n{client.user}\n{client.user.id}')

        @client.event
        async def on_command(ctx):
            logger.debug(f'{ctx.author} called command {ctx.command.name} with args {ctx.args} in channel {ctx.message.channel.id}')

        @client.event
        async def on_command_completion(ctx):
            logger.debug(f'Command {ctx.command.name} called by {ctx.author} completed without uncaught errors')

        @client.event
        async def on_command_error(ctx, error):
            """Basic error handling, including generic messages to send for common errors."""
            error: Exception = getattr(error, 'original', error)
            if ctx.command and ctx.command.has_error_handler():
                return

            if isinstance(error, commands.CommandNotFound):
                return await ctx.reply(f'Error: Your command was not recognized. Please refer to {client.command_prefix}help for more info.')
            if isinstance(error, commands.MissingRequiredArgument):
                return await ctx.reply('Error: You did not provide the required argument(s). Make sure you typed the command correctly.')
            if isinstance(error, commands.CheckFailure):
                return await ctx.reply('Error: You do not have permission to use this command.')

            formatted_error = ''.join(traceback.format_exception(type(error), error, tb=error.__traceback__))
            logger.error(formatted_error)

            print(f'Exception in command {ctx.command}:', file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

            embed = discord.Embed(color=0xff0000, title='Error', description=f'```py\n{formatted_error}\n```')
            app_info = await client.application_info()
            embed.set_footer(text=f'Please contact {app_info.owner} for help.')
            await ctx.reply(embed=embed)

        @client.event
        async def on_error(event, *args):
            exception = traceback.format_exc()
            print(f'Exception in {event}:', file=sys.stderr)
            print(exception, file=sys.stderr)
            logger.error(exception)

        @client.command()
        @commands.is_owner()
        async def reload(ctx):
            """Reloads the bot's extensions."""
            logger.info('Reload command called! Reloading bot...')
            status_message = await ctx.reply('Reloading bot...')
            for extension in dict(client.extensions):  # create a copy of the mapping
                try:
                    await client.reload_extension(extension)
                except commands.ExtensionFailed as e:
                    await status_message.edit(content=f'{status_message.content}\n{extension}: ❌')
                    raise e.original from None
                else:
                    await status_message.edit(content=f'{status_message.content}\n{extension}: ✅')
            logger.info('Bot reloaded!')

        await client.load_extension('cogs.team_management')
        try:
            await client.start(token)
        except discord.errors.LoginFailure:
            print('Invalid token!', file=sys.stderr)
        finally:
            await client.close()

        @reload.error  # this isn't triggering has_error_handler() for some reason right now
        async def reload_error(ctx, error):
            print('bruh')


if __name__ == '__main__':
    asyncio.run(login())
