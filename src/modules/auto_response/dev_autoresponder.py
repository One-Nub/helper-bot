import discord
from discord import app_commands
from discord.ext import commands

from resources.constants import ADMIN_ROLES
from resources.helper_bot import HelperBot


@app_commands.guild_only()
class DevAutoresponder(commands.GroupCog, name="dev_autoresponder"):
    TIME_TO_DELETE = 10

    def __init__(self, bot):
        self.bot: HelperBot = bot
        super().__init__()

    @commands.Cog.listener("on_message")
    async def message_handler(self, message: discord.Message):
        if (
            message.author.bot
            or not message.guild
            or not type(message.author) == discord.Member
            or not message.reference
            or not message.mentions
        ):
            return

        referenced_message = message.reference.cached_message or await message.channel.fetch_message(
            message.reference.message_id  # type: ignore
        )
        if not referenced_message:
            # could not find the referenced message.
            return

        volunteers_role = ADMIN_ROLES["hq_volunteers"]
        dev_role = ADMIN_ROLES["dev"]
        author_roles = [x.id for x in message.author.roles]
        if volunteers_role in author_roles or dev_role in author_roles:
            # Let helpers & admins bypass it.
            return

        referenced_author = referenced_message.author
        if type(referenced_author) == discord.User:
            # Convert to member
            referenced_author = message.guild.get_member(
                referenced_message.author.id
            ) or await message.guild.fetch_member(referenced_message.author.id)

        if referenced_author is None:
            # Failed to convert to member
            return

        if referenced_author.id not in [x.id for x in message.mentions]:
            # message contained a mention, but it likely is not on the message reply
            return

        ref_author_roles = [x.id for x in referenced_author.roles]  # type: ignore
        if dev_role not in ref_author_roles:
            # allow other people to reply to each other
            return

        reply_msg = await message.reply(
            content=(
                "Please do not ping the developer when replying to him. "
                "Send your message again, but do not ping him in your reply, thanks!\n"
                "-# This is an automated message and will self destruct in 10 seconds."
            )
        )

        await message.delete(delay=self.TIME_TO_DELETE)
        await reply_msg.delete(delay=self.TIME_TO_DELETE)


async def setup(bot: HelperBot):
    await bot.add_cog(DevAutoresponder(bot))
