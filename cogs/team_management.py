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

import asyncio
from typing import Optional

import discord
from discord.ext import commands

from bot import Bot

RESERVED_IDS = ['list', 'create', 'edit']


class TeamManagement(commands.Cog, name='Team Management'):
    """Create, manage, and delete teams."""
    def __init__(self, bot: Bot):
        self.bot = bot
        self.team_id = None  # i found this in a 0 upvote slack overflow post and this is incredibly stupid.
        # is there really not a better way to pass command args to subcommands?

    @commands.group()
    async def team(self, ctx, team_id: str):
        self.team_id = team_id.lower()
        if self.team_id in RESERVED_IDS:
            # swap two fields
            if len(ctx.message.content.split(' ')) > 2:
                self.team_id = ctx.message.content.split(' ')[2].lower()
            return await ctx.invoke(self.bot.get_command(f'team {team_id.lower()}'))
        if ctx.invoked_subcommand is None:
            return await ctx.reply(f'Please specify a command to perform. See `{self.bot.command_prefix}help team` for more info.')

    @team.command()
    async def info(self, ctx):
        try:
            team = await self.bot.fetchone('SELECT * FROM teams WHERE id = ?', (self.team_id,))
        except IndexError:
            return await ctx.reply('Team not found.')
        c = discord.utils.get(ctx.guild.roles, name=f'{team[1]} {team[2]}') or 0
        if isinstance(c, discord.Role):
            c = c.color
        embed = discord.Embed(title=f'{team[1] or "None"} Team Info', color=c)
        embed.add_field(name='ID', value=self.team_id, inline=True)
        embed.add_field(name='Name', value=team[1] or 'None', inline=True)
        embed.add_field(name='Mascot', value=team[2] or 'None', inline=True)
        embed.add_field(name='Coach', value=f'<@{team[3]}>' if team[3] else 'None', inline=True)
        embed.add_field(name='Offense', value=['5-Out', '4-Out', 'Iso'][team[4]] if team[4] else 'None', inline=True)
        embed.add_field(name='Defense', value=['1-3-1', 'Man', '2-3'][team[5]] if team[5] else 'None', inline=True)
        return await ctx.reply(embed=embed)

    @team.command(name='list')
    async def team_list(self, ctx):
        """Returns a list of team IDs."""
        team_pages = commands.Paginator(max_size=300)
        teams = list(await self.bot.db.execute_fetchall('SELECT id, name FROM teams'))
        teams.sort(key=lambda a: a[0])
        for team in teams:
            team_pages.add_line(f'{team[0]}: {team[1]}')

        embed = discord.Embed(title=f'Team ID List', description=team_pages.pages[0], color=0)
        message = await ctx.reply(embed=embed)

        def reaction_check(reaction, user):  # whittles down all reactions to only the ones that it's looking for.
            return all((reaction.message == message, user == ctx.author, reaction.emoji in ['⬅️', '➡️', '❌']))

        await message.add_reaction('⬅️')
        await message.add_reaction('➡️')
        await message.add_reaction('❌')

        i = 0
        while True:
            try:
                user_reaction = await self.bot.wait_for('reaction_add', timeout=60, check=reaction_check)
            except asyncio.TimeoutError:
                return await message.clear_reactions()
            user_reaction = user_reaction[0]
            await user_reaction.remove(ctx.author)
            if user_reaction.emoji == '❌':
                return await message.clear_reactions()
            if user_reaction.emoji == '⬅️':
                i = len(team_pages.pages) - 1 if i == 0 else i - 1  # wraparound
            if user_reaction.emoji == '➡️':
                i = 0 if i == len(team_pages.pages) - 1 else i + 1
            embed.description = team_pages.pages[i]
            embed.set_footer(text=f'Page {i + 1} of {len(team_pages.pages)}')
            await message.edit(embed=embed)

    @team.command(name='create')
    async def team_create(self, ctx, team_id: Optional[str] = None):
        team_id = team_id or self.team_id
        if team_id == 'create':
            return await ctx.reply('Please specify a team ID.')
        if team_id in RESERVED_IDS:
            return await ctx.reply(f'Error: {team_id} is a reserved word.')
        if int(await self.bot.fetchval('SELECT EXISTS(SELECT 1 FROM teams WHERE id = ?)', (team_id,))):
            return await ctx.reply('Team with ID already exists.')
        await self.bot.db.execute('INSERT INTO teams VALUES(?, NULL, NULL, NULL, NULL, NULL)', (team_id,))
        await self.bot.db.commit()
        embed = discord.Embed(title=f'None Team Info', color=0)
        embed.add_field(name='ID', value=team_id, inline=True)
        embed.add_field(name='Name', value='None', inline=True)
        embed.add_field(name='Mascot', value='None', inline=True)
        embed.add_field(name='Coach', value='None', inline=True)
        embed.add_field(name='Offense', value='None', inline=True)
        embed.add_field(name='Defense', value='None', inline=True)
        return await ctx.reply(content='Team successfully created.', embed=embed)

    @team.group(name='edit')
    @commands.has_role('Bot Access')
    async def team_edit(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.reply(f'Command used incorrectly. Consult `{self.bot.command_prefix}help team edit` for more info.')

    @team_edit.command(name='name')
    @commands.has_role('Bot Access')
    async def edit_name(self, ctx, name: str):
        team_id = self.team_id
        if int(await self.bot.fetchval('SELECT NOT EXISTS(SELECT 1 FROM teams WHERE id = ?)', (team_id,))):
            return await ctx.reply('Team ID does not exist.')
        await self.bot.db.execute('UPDATE teams SET name = ? WHERE id = ?', (name, team_id))
        await self.bot.db.commit()
        return await ctx.reply(f'Success. {team_id}\'s name successfully set to {name}.')

    @team_edit.command(name='mascot')
    @commands.has_role('Bot Access')
    async def edit_mascot(self, ctx, mascot: str):
        team_id = self.team_id
        if int(await self.bot.fetchval('SELECT NOT EXISTS(SELECT 1 FROM teams WHERE id = ?)', (team_id,))):
            return await ctx.reply('Team ID does not exist.')
        await self.bot.db.execute('UPDATE teams SET mascot = ? WHERE id = ?', (mascot, team_id))
        await self.bot.db.commit()
        return await ctx.reply(f'Success. {team_id}\'s mascot successfully set to {mascot}.')

    @team_edit.command(name='coach')
    @commands.has_role('Bot Access')
    async def edit_coach(self, ctx, coach: discord.Member):
        team_id = self.team_id
        coach_id = coach.id
        if int(await self.bot.fetchval('SELECT NOT EXISTS(SELECT 1 FROM teams WHERE id = ?)', (team_id,))):
            return await ctx.reply('Team ID does not exist.')
        await self.bot.db.execute('UPDATE teams SET coach = ? WHERE id = ?', (coach_id, team_id))
        await self.bot.db.commit()
        return await ctx.reply(f'Success. {team_id}\'s coach successfully set to {coach.mention}.')


async def setup(bot: Bot):
    await bot.add_cog(TeamManagement(bot))
