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
Would we want multi-string matching? Example, we could have "word" explicitly found, or a "phrase"
But do we want something like discord's partial matching for safety rules, where we can add asterisks 
I don't think I want to support regex, we don't really need that.
I think when triggers are set, the whole string will be the "match", where asterisks will allow for 
prefix or suffix matching - and if it's in the middle of a "string" its anything up until?
Probably need to tokenize the strings.
"""


@app_commands.guild_only()
class Autoresponder(commands.GroupCog, name="autoresponder"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await is_staff(interaction)

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await is_staff(ctx)

    @commands.Cog.listener("on_message")
    async def message_handler(self, message: discord.Message):
        if message.author.bot:
            return

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
        triggers="Text that will trigger this response. Comma separated for multiple words, asterisks for partial matching",
        autodelete="How long until the bot vaporizes the original message and response?",
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
