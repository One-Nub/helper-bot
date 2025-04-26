from typing import Optional

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from resources.checks import is_staff
from resources.helper_bot import HelperBot

"""
Potential DB structure:
- Id or name to refer to the responder as - common name
- triggers (list of strings)
- message
- auto delete
---

Special characters: 
    * = prefix/suffix matching of a string
    ... = large partial matching (so start-end and it would match "really start wow some random stuff end whee")
        just represents "lots of content" between the start word and the end
        ! cannot be used with prefix/suffix matching in the same trigger string.
        ! cannot be used multiple times in one trigger string.
    , = splits trigger to different words that MUST uniquely exist in the string.

cspell: disable
Example valid triggers:
    "verify"
    "help pls" - must show up exactly as "help pls" in the message (case insensitive)
    "ban*" - matches "ban", "banned", "banning", etc
    "how...verify" (or "how ... verify") - matches "how verify", "how do i verify", "how john cena verify?", "how can i averify"
        but not "verify how" or "verify pls how", nor "hob do i verbify"
    "how, join" - matches "how do i join bloxlink", "how cna i join", but not "how can i joine", "join pls", "how play", "howjoin"

Asterisks in the middle of phrases (i.e. "how*join") shall not be treated as partial matching options.
cspell: enable
"""


@app_commands.guild_only()
class Autoresponder(commands.GroupCog, name="autoresponder"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await is_staff(interaction)

    @commands.Cog.listener("on_message")
    async def message_handler(self, message: discord.Message):
        if message.author.bot:
            return

    @app_commands.command(name="help", description="Learn how to use the command!")
    async def syntax_info(self, ctx: discord.Interaction):
        await ctx.response.send_message("placeholder")

    @app_commands.command(name="all", description="View all set automatic responses")
    async def view_all(self, ctx: discord.Interaction):
        await ctx.response.send_message("placeholder")

    @app_commands.command(name="view", description="View a specific automatic response")
    @app_commands.describe(name="The admin-facing name for the responder")
    async def view_single(self, ctx: discord.Interaction, name: str):
        await ctx.response.send_message(f"placeholder with name {name}")

    @app_commands.command(name="add", description="Create an automatic response")
    @app_commands.describe(
        name="A unique admin-facing name for this responder",
        triggers="Text that will trigger this response. Use the help subcommand to get syntax information.",
        autodelete="How long (in seconds) until the bot vaporizes the original message and response?",
    )
    async def add_responder(
        self,
        ctx: discord.Interaction,
        name: str,
        triggers: str,
        autodelete: Optional[int],
    ):
        await ctx.response.send_message(f"placeholder with name {name} and trigger `{triggers}`")

    @app_commands.command(name="delete", description="Remove an automatic response")
    @app_commands.describe(name="The admin-facing name for the responder")
    async def delete_responder(self, ctx: discord.Interaction, name: str):
        await ctx.response.send_message(f"placeholder with name {name}")


async def setup(bot: HelperBot):
    await bot.add_cog(Autoresponder(bot))
