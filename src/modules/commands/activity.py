from datetime import datetime

import discord
from discord.ext.commands import Context, check

from resources.checks import is_cm, is_hr
from resources.constants import BLURPLE
from resources.exceptions import HelperError
from resources.helper_bot import instance as bot

MAX_USERS_PER_PAGE = 10


@bot.hybrid_group("activity", description="Send (staff) activity leaderboard to this channel!", fallback="lb")
@discord.app_commands.guild_only()
@check(is_cm)
async def activity_base(ctx: Context):
    """Activity of all Staff members."""
    # Get activity from the db, get their msg_count, then sort by highest to lowest
    activity_list = await bot.db.get_all_staff_metrics()
    activity_list.sort(key=lambda x: x["msg_count"], reverse=True)
    description = ""
    username = ""
    for i, tag in enumerate(activity_list):
        user = await bot.fetch_user(tag["_id"])
        if user is not None:
            username = user.name
        description += f"{i+1}. <@{tag['_id']}> ({username}) - {tag['msg_count']} message(s)\n"
    embed = discord.Embed(
        title="Activity Leaderboard",
        description=description,
        color=BLURPLE,
    )
    await ctx.reply(embed=embed, mention_author=False, ephemeral=True)


@activity_base.command("trials", description="View activity for trials.")
@check(is_hr)
async def trials(ctx: Context):
    """Activity of all Trial members."""
    # Get activity from the db, get their msg_count, then sort by highest to lowest
    activity_list = await bot.db.get_all_trial_metrics()
    activity_list.sort(key=lambda x: x["msg_count"], reverse=True)
    description = ""
    username = ""
    for i, tag in enumerate(activity_list):
        user = await bot.fetch_user(tag["_id"])
        if user is not None:
            username = user.name
        else:
            username = ""
        description += f"{i+1}. <@{tag['_id']}> ({username}) - {tag['msg_count']} message(s)\n"
    embed = discord.Embed(
        title="Activity Leaderboard [Trial Staff]",
        description=description,
        color=BLURPLE,
    )
    await ctx.reply(embed=embed, mention_author=False, ephemeral=True)


@activity_base.command("view", description="View activity for specific user.")
@check(is_cm)
async def activity_view(ctx: Context, staff_id):
    """Fetch information about activity from a certain user."""
    if staff_id == 0:
        raise HelperError("Missing argument `staff_id`. Please provide a valid Discord ID.")

    if len(str(staff_id)) < 17:
        raise HelperError("Invalid Argument `id`. Please provide a valid Discord ID.")

    data = await bot.db.get_staff_metrics(int(staff_id))
    if data is None:
        raise HelperError("There is no data for this user.")

    success_embed = discord.Embed()
    success_embed.title = "Activity Log"
    success_embed.description = f"Below is the activity log for <@{staff_id}>."
    success_embed.color = BLURPLE
    success_embed.add_field(name="Message Count (last 30 days)", value=data["msg_count"])
    success_embed.add_field(name="Last Message Sent", value=data["updated_at"])
    success_embed.timestamp = datetime.now()
    success_embed.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)

    await ctx.reply(embed=success_embed, mention_author=False, ephemeral=True)
