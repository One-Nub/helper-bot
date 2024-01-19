import logging
from datetime import datetime
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from resources.checks import is_staff
from resources.constants import BLURPLE, DEVELOPMENT_GUILDS, TEAM_CENTER_GUILD
from resources.helper_bot import HelperBot
from resources.linear_api import LinearAPI, LinearIssue, LinearTeam

logger = logging.getLogger("CMDS")


@app_commands.guild_only()
class Linear(commands.GroupCog, group_name="linear"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="issue")
    @app_commands.describe(
        title="Short description of the issue",
        description="Long description of the issue",
        team="The team this issue is for",
    )
    @app_commands.check(is_staff)
    @app_commands.guilds(TEAM_CENTER_GUILD, *DEVELOPMENT_GUILDS)
    async def issue(
        self,
        ctx: discord.Interaction,
        title: str,
        description: str,
        team: Literal["bot", "website"],
    ):
        """Log an issue for the Bloxlink developers! Staff only."""
        await ctx.response.defer()

        linear: LinearAPI = LinearAPI.connect()
        teams = await linear.get_teams()

        chosen_team: LinearTeam = None
        for linear_team in teams:
            if linear_team.name.lower() == team:
                chosen_team = linear_team
                break

        if not chosen_team:
            await ctx.followup.send(
                "Could not find the team you are creating an issue for! :cry:",
                ephemeral=True,
                mention_author=False,
            )
            return

        description = "\n".join(description.split("\\n"))
        description += f"\n\n> *Created by {ctx.user.name} ({ctx.user.id}) on Discord.*"
        created_issue: LinearIssue = await linear.create_issue(
            chosen_team.id, title=title, description=description
        )

        if not created_issue:
            await ctx.followup.send(
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
        embed.set_footer(icon_url=ctx.user.avatar.url, text=chosen_team.name)
        embed.timestamp = datetime.utcnow()

        if created_issue.state:
            embed.add_field(name="Status", value=created_issue.state.name)

        await ctx.followup.send(
            content=f"Issue [{created_issue.identifier}]({created_issue.url}) created.", embed=embed
        )

    @app_commands.check(is_staff)
    async def search_autocomplete(self, interaction: discord.Interaction, user_input: str):
        """Display issues from linear to the user."""
        if not user_input:
            await interaction.response.autocomplete([])
            return

        linear: LinearAPI = LinearAPI.connect()
        issues = await linear.search_for_issues(user_input)

        choices = [
            app_commands.Choice(name=f"{issue.identifier} - {issue.title}"[:100], value=issue.id)
            for issue in issues[:25]
        ]

        await interaction.response.autocomplete(choices)

    @app_commands.command(name="search")
    @app_commands.describe(query="What are you searching for?")
    @app_commands.autocomplete(query=search_autocomplete)
    @app_commands.check(is_staff)
    @app_commands.guilds(TEAM_CENTER_GUILD, *DEVELOPMENT_GUILDS)
    async def search(self, ctx: discord.Interaction, query: str):
        """Search for an issue on Linear!"""
        await ctx.response.send_message(query)

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        match error:
            case app_commands.CheckFailure():
                error = "You are not allowed to use this command!"

            case _ as err:
                logger.error(err)

        if not interaction.response.is_done():
            await interaction.response.send_message(content=error, ephemeral=True)
        else:
            await interaction.followup.send(content=error, ephemeral=True)


async def setup(bot: HelperBot):
    await bot.add_cog(Linear(bot))
