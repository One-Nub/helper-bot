import math
from datetime import datetime, timedelta

import discord
from discord import ui
from discord.ext.commands import Context, check

from resources.checks import is_cm
from resources.constants import BLURPLE, RED, UNICODE_LEFT, UNICODE_RIGHT
from resources.helper_bot import instance as bot

MAX_USERS_PER_PAGE = 10


@bot.hybrid_group("activity", description="Send (staff) activity leaderboard to this channel!", fallback="lb")
@check(is_cm)
async def activity_base(ctx: Context):
    """Activity of all Staff members."""
    # Get activity from the db, get their msg_count, then sort by highest to lowest
    activity_list = await bot.db.get_all_staff_metrics()
    activity_list.sort(key=lambda x: x["msg_count"], reverse=True)
    description = ""
    for i, tag in enumerate(activity_list):
        description += f"{i+1}. <@{tag['_id']}> - {tag['msg_count']} message(s)\n"
    embed = discord.Embed(
        title="Activity Leaderboard",
        description=description,
        color=BLURPLE,
    )
    await ctx.reply(embed=embed)


@activity_base.command("trials", description="View activity for trials.")
@check(is_cm)
async def trials(ctx: Context):
    """Activity of all Trial members."""
    # Get activity from the db, get their msg_count, then sort by highest to lowest
    activity_list = await bot.db.get_all_trial_metrics()
    activity_list.sort(key=lambda x: x["msg_count"], reverse=True)
    description = ""
    for i, tag in enumerate(activity_list):
        description += f"{i+1}. <@{tag['_id']}> - {tag['msg_count']} message(s)\n"
    embed = discord.Embed(
        title="Activity Leaderboard [Trial Staff]",
        description=description,
        color=BLURPLE,
    )
    await ctx.reply(embed=embed, mention_author=False, ephemeral=True)


@activity_base.command("view", description="View activity for specific user.")
@check(is_cm)
async def activity_view(ctx: Context, staff_id: int = 0):
    """Fetch information about activity from a certain user."""
    try:
        if staff_id == 0:
            raise Exception("Missing argument `staff_id`. Please provide a valid Discord ID.")

        elif len(str(staff_id)) < 17:
            raise Exception("Invalid Argument `id`. Please provide a valid Discord ID.")

        else:
            data = await bot.db.get_staff_metrics(staff_id)
            if data is None:
                raise Exception("There is no data for this user.")

            success_embed = discord.Embed()
            success_embed.title = "Activity Log"
            success_embed.description = f"Below is the activity log for <@{staff_id}>."
            success_embed.color = BLURPLE
            success_embed.add_field(name="Message Count (last 30 days)", value=data["msg_count"])
            success_embed.timestamp = datetime.now()
            success_embed.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)

            await ctx.reply(embed=success_embed, mention_author=False, ephemeral=True)
    except Exception as Error:
        embed_var = discord.Embed(
            title="<:BloxlinkDead:823633973967716363> Error",
            description=Error,
            color=RED,
        )
        embed_var.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)
        embed_var.timestamp = datetime.now()

        await ctx.reply(embed=embed_var)
