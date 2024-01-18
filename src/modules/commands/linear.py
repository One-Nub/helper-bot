from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from resources.checks import is_staff
from resources.constants import DEVELOPMENT_GUILDS, TEAM_CENTER_GUILD
from resources.helper_bot import HelperBot


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
        ctx: commands.Context,
        title: str,
        description: str,
        team: Literal["bot", "website"],
    ):
        """Log an issue for the Bloxlink developers! Staff only."""
        print("SPOKOY")


async def setup(bot: HelperBot):
    await bot.add_cog(Linear(bot))
