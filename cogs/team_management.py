"""
File that provides team management functions for the Fake Basketball Bot.
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

import discord
from discord.ext import commands

from bot import Bot


class TeamManagement(commands.Cog, name='Team Management'):
    """Create, manage, and delete teams."""
    def __init__(self, bot: Bot):
        self.bot = bot
        self.team_id = None  # i found this in a 0 upvote slack overflow post and this is incredibly stupid.
        # is there really not a better way to pass command args to subcommands?

    @commands.group()
    async def team(self, ctx, team_id: str):
        team_id = team_id.lower()
        # if team_id == 'list':
        #     team_pages = commands.Paginator(max_size=1000)
        #     teams = list(await self.bot.db.execute_fetchall('SELECT id, name FROM teams'))
        #     teams.sort(key=lambda a: a[0])
        #     for team in teams:
        #         team_pages.add_line(f'{team[0]}: {team[1]}')
        #     embed = discord.Embed(title=f'Team ID List', description=team_pages.pages, color=0)
        #     return
        if ctx.invoked_subcommand is None:
            return await ctx.reply(f'Please specify a command to perform. See `{self.bot.command_prefix}help team` for more info.')
        self.team_id = team_id

    @team.command()
    async def info(self, ctx):
        try:
            team = await self.bot.fetchone('SELECT * FROM teams WHERE id = ?', (self.team_id,))
        except IndexError:
            return await ctx.reply('Team not found.')
        c = discord.utils.get(ctx.guild.roles, name=f'{team[1]} {team[2]}') or 0
        if isinstance(c, discord.Role):
            c = c.color
        embed = discord.Embed(title=f'{team[1]} Team Info', color=c)
        embed.add_field(name='Name', value='None' if team[1] is None else team[1], inline=True)
        embed.add_field(name='Mascot', value='None' if team[2] is None else team[2], inline=True)
        embed.add_field(name='Coach', value='None' if team[3] is None else f'<@{team[3]}>', inline=True)
        embed.add_field(name='Offense', value='None' if team[4] is None else ['5-Out', '4-Out', 'Iso'][team[4]], inline=True)
        embed.add_field(name='Defense', value='None' if team[5] is None else ['1-3-1', 'Man', '2-3'][team[5]], inline=True)
        return await ctx.reply(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(TeamManagement(bot))
