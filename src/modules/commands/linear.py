from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from resources.checks import is_staff
from resources.constants import BLURPLE, DEVELOPMENT_GUILDS, TEAM_CENTER_GUILD
from resources.helper_bot import HelperBot
from resources.linear_api import LinearAPI, LinearIssue, LinearTeam


@app_commands.guild_only()
class Linear(commands.GroupCog, group_name="linear"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="issue")
    @app_commands.check(is_staff)
    @app_commands.describe(
        title="Short description of the issue",
        description="Long description of the issue",
        team="The team this issue is for",
    )
    @app_commands.guilds(TEAM_CENTER_GUILD, *DEVELOPMENT_GUILDS)
    async def issue(
        self,
        ctx: discord.Interaction,
        title: str,
        description: str,
        team: Literal["bot", "website"],
    ):
        """Log an issue for the Bloxlink developers! Staff only."""
        linear: LinearAPI = LinearAPI.connect()
        teams = await linear.get_teams()

        chosen_team: LinearTeam = None
        for linear_team in teams:
            if linear_team.name.lower() == team:
                chosen_team = linear_team
                break

        if not chosen_team:
            await ctx.response.send_message(
                "Could not find the team you are creating an issue for! :cry:",
                ephemeral=True,
                mention_author=False,
            )
            return

        description = "\n".join(description.split("\\n"))
        description += f"\n\n> *Created by {ctx.user.name} ({ctx.user.id}) on Discord.*"
        created_issue = await linear.create_issue(chosen_team.id, title=title, description=description)

        if not created_issue:
            await ctx.response.send_message(
                "There was a problem when creating your issue! :pensive:",
                ephemeral=True,
                mention_author=False,
            )
            return

        embed = discord.Embed()
        embed.title = f"{created_issue.identifier} - {created_issue.title}"
        embed.url = created_issue.url
        embed.description = description
        embed.color = BLURPLE

        await ctx.response.send_message(
            content=f"Issue [{created_issue.identifier}]({created_issue.url}) created.", embed=embed
        )


async def setup(bot: HelperBot):
    await bot.add_cog(Linear(bot))
