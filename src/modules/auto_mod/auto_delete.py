import asyncio
import contextlib
import logging
import re

import discord
from discord import Embed, app_commands
from discord.ext import commands

from resources.constants import ADMIN_ROLES, BLOXLINK_GUILD, RED
from resources.helper_bot import HelperBot

NAME_REGEX = re.compile(r"(image|\d|\d_[a-zA-Z0-9]{7,})\.(jpg|jpeg|png|webm|gif|mov|mp4|gifv)")
_logger = logging.getLogger(__name__)


@app_commands.guild_only()
class AutoDeleteCryptoSpam(commands.GroupCog, name="automod_delete_crypto"):
    def __init__(self, bot):
        self.bot: HelperBot = bot
        super().__init__()

    @commands.Cog.listener("on_message")
    async def message_handler(self, message: discord.Message):
        if (
            message.author.bot
            or not message.guild
            or not type(message.author) == discord.Member
            or not message.attachments
            or not message.guild.id == BLOXLINK_GUILD
        ):
            return

        # Log single msg attachments (to use for reference for common formats.)
        # Some spambots only post 1 image, using this as a baseline.
        if len(message.attachments) == 1 and NAME_REGEX.search(message.attachments[0].filename) is not None:
            _logger.info(message.attachments[0].filename)
            return

        # Filter out if there is less than 3 images.
        if len(message.attachments) < 3:
            return

        check = []
        for item in message.attachments:
            check.append(NAME_REGEX.search(item.filename) is not None)

        # debug
        filenames = [item.filename for item in message.attachments]
        _logger.info(filenames)

        if not all(check):
            return

        volunteers_role = ADMIN_ROLES["hq_volunteers"]
        dev_role = ADMIN_ROLES["dev"]
        author_roles = [x.id for x in message.author.roles]
        if volunteers_role in author_roles or dev_role in author_roles:
            # Let helpers & admins bypass it.
            return

        log_channels = await self.bot.db.get_log_channels(guild_id=str(message.guild.id))
        if not log_channels:
            log_channels = {}
        log_channel = log_channels.get("moderation", "")

        if log_channel:
            lc = self.bot.get_channel(log_channel)
            if not lc:
                lc = await self.bot.fetch_channel(log_channel)

            if lc:
                await lc.send(
                    embed=Embed(
                        title="Moderation Action",
                        description=f"Deleted message & removed user for crypto image spam.\n"
                        f"\n- User: `{message.author.name}`\n- ID: `{message.author.id}`",
                        color=RED,
                    )
                )

        with contextlib.suppress(discord.NotFound):
            await message.delete()

        _logger.info("Removed user %s", message.author.id)
        await message.author.ban(delete_message_days=1, reason="Image spam for crypto - compromised account.")
        await asyncio.sleep(0.5)
        await message.author.unban(
            reason="Softban - user removed for crypto image spam - compromised account."
        )


async def setup(bot: HelperBot):
    await bot.add_cog(AutoDeleteCryptoSpam(bot))
