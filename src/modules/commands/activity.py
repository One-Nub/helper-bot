import typing
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context, check

from resources.checks import is_cm, is_hr
from resources.constants import ADMIN_ROLES, BLURPLE, SUPPORT_CHANNEL, TRIAL_ROLE
from resources.exceptions import HelperError
from resources.helper_bot import HelperBot
from resources.helper_bot import instance as bot
from resources.utils.base_embeds import StandardEmbed


class DateConverter(commands.Converter):
    """Converts a given string to a set YYYY-MM format.

    "/" is replaced with "-" in the given input
    Accepted formats:
        MM
        YYYY-MM
        YYYY MM
        MM-YYYY
        MM YYYY
        Jan YYYY
        January YYYY
        Jan
        January
    """

    async def convert(self, ctx: Context, argument: str) -> str | None:
        now = datetime.now(timezone.utc)
        if argument.isdigit():
            arg_time = datetime.strptime(
                f"{now.year}-{argument}", "%Y-%m"
            )  # so we force the month to the right format
            return arg_time.strftime("%Y-%m")

        argument = argument.replace("/", "-")
        # YYYY-mm
        try:
            arg_time = datetime.strptime(argument, "%Y-%m")
            return arg_time.strftime("%Y-%m")
        except ValueError:
            pass

        # YYYY mm
        try:
            arg_time = datetime.strptime(argument, "%Y %m")
            return arg_time.strftime("%Y-%m")
        except ValueError:
            pass

        # mm-YYYY
        try:
            arg_time = datetime.strptime(argument, "%m-%Y")
            return arg_time.strftime("%Y-%m")
        except ValueError:
            pass

        # mm YYYY
        try:
            arg_time = datetime.strptime(argument, "%m %Y")
            return arg_time.strftime("%Y-%m")
        except ValueError:
            pass

        # Jan/Feb/Mar... YYYY
        try:
            arg_time = datetime.strptime(argument, "%b %Y")
            return arg_time.strftime("%Y-%m")
        except ValueError:
            pass

        # January/February/March... YYYY
        try:
            arg_time = datetime.strptime(argument, "%B %Y")
            return arg_time.strftime("%Y-%m")
        except ValueError:
            pass

        # Fallback for "Feb" or "February" (month only input)
        if len(argument.strip()) == 3:
            try:
                arg_time = datetime.strptime(f"{argument} {now.year}", "%b %Y")
                return arg_time.strftime("%Y-%m")
            except ValueError:
                pass
        else:
            try:
                arg_time = datetime.strptime(f"{argument} {now.year}", "%B %Y")
                return arg_time.strftime("%Y-%m")
            except ValueError:
                pass

        return None


class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot: HelperBot = bot
        super().__init__()

    @commands.Cog.listener("on_message")
    async def message_listener(self, message: discord.Message):
        if (
            message.author.bot
            or not message.guild
            or not type(message.author) == discord.Member
            # or message.channel.id != SUPPORT_CHANNEL
        ):
            return

        author_roles = set([role.id for role in message.author.roles])
        staff_roles = set(ADMIN_ROLES.values())

        if TRIAL_ROLE in author_roles:
            await bot.db.update_staff_metric(str(message.author.id), "trial", incr_message=True)
        elif author_roles.intersection(staff_roles):
            await bot.db.update_staff_metric(str(message.author.id), "volunteer", incr_message=True)

    @commands.hybrid_group(name="activity")
    @check(is_hr)
    async def activity_group(
        self,
        ctx: Context,
        team: typing.Optional[typing.Literal["volunteer", "trial"]] = "volunteer",
        *,
        date: typing.Optional[typing.Annotated[str, DateConverter]] = None,
    ):
        # Not using fallback because fallback had some weird behavior with the arguments.
        return await self.leaderboard(ctx, team, date=date)

    @activity_group.command(  # type: ignore
        name="leaderboard",
        description="Send the activity leaderboard to this channel!",
        aliases=["lb"],
    )
    @app_commands.describe(team="Volunteers or Trials", date="Month & year (or just month)")
    @check(is_hr)
    async def leaderboard(
        self,
        ctx: Context,
        team: typing.Optional[typing.Literal["volunteer", "trial"]] = "volunteer",
        *,
        date: typing.Optional[typing.Annotated[str, DateConverter]] = None,
    ):
        if team == "volunteer":
            allowed = await is_cm(ctx)
            if not allowed:
                if ctx.message:
                    await ctx.message.delete(delay=7.0)
                return await ctx.reply(
                    "You don't have permissions to check this leaderboard.",
                    ephemeral=True,
                    delete_after=7,
                )

        if not date:
            now = datetime.now(timezone.utc)
            date = now.strftime("%Y-%m")  # type: ignore

        month_metrics = await bot.db.get_month_metrics(date)
        if not month_metrics:
            if ctx.message:
                await ctx.message.delete(delay=7.0)
            return await ctx.reply(
                f"No data found for the month of `{date}`.",
                ephemeral=True,
                delete_after=7,
            )

        metric_list = month_metrics.staff if team == "volunteer" else month_metrics.trial_staff
        metric_list.sort(key=(lambda x: x.messages + x.tags), reverse=True)

        desc_output = []
        for user in metric_list:
            duser = bot.get_user(int(user.id)) or await bot.fetch_user(int(user.id))
            desc_output.append(
                f"<@{user.id}> ({duser.name}): "
                f"`{user.messages}` message{'s' if user.messages != 1 else ''}; "
                f"`{user.tags}` tag{'s' if user.tags != 1 else ''} ran"
            )

        date_obj = datetime.strptime(date, "%Y-%m")
        embed = StandardEmbed(
            title=f"Volunteer Metrics for {date_obj.strftime('%B %Y')}",
            description="\n".join(desc_output),
            footer_icon_url=ctx.author.display_avatar.url,
        )
        await ctx.reply(embed=embed, mention_author=False, ephemeral=True)


async def setup(bot: HelperBot):
    await bot.add_cog(Activity(bot))
