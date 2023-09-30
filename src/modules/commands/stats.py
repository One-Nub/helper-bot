import math  # for tracking memory usage
from os import getpid  # for tracking memory usage

import discord
from discord.ext import commands
from psutil import Process  # for tracking memory usage

from resources.constants import BLURPLE
from resources.helper_bot import instance as bot


@bot.hybrid_command("stats", description="View some information about me!")
async def stats(ctx: commands.Context):
    process = Process(getpid())
    process_mem = math.floor(process.memory_info().rss / 1024**2)

    # send the info embed
    info_embed = discord.Embed(
        color=BLURPLE,
    )

    # bot avatar + bot name at the top
    info_embed.set_author(
        name=f"{ctx.bot.user.name}#{ctx.bot.user.discriminator}", icon_url=ctx.bot.user.avatar
    )

    uptime_split = str(bot.uptime).split(":")
    hr = uptime_split[0]
    hr = f"{hr} hours" if hr != "0" else None

    mins = uptime_split[1]
    mins = f"{mins} minutes" if mins != "00" else ""

    sec = f"{uptime_split[2][:2]} seconds"

    uptime_str = ", ".join(filter(None, [hr, mins, sec]))

    info_embed.description = f"- **Uptime:** {uptime_str}\n- **Memory:** {process_mem} MB\n- **Prefix:** `.`"

    info_embed.add_field(name="Users", value=len(ctx.bot.users), inline=True)

    info_embed.add_field(name="Guilds", value=len(ctx.bot.guilds), inline=True)

    await ctx.reply(embed=info_embed, mention_author=False)
