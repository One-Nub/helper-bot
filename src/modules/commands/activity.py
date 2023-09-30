from datetime import datetime

import discord
from discord.ext.commands import Context, check

from resources.checks import is_cm
from resources.constants import BLURPLE, RED
from resources.helper_bot import instance as bot


@bot.command("activity", description="Staff activity check.")
@check(is_cm)
async def activity(ctx: Context, staff_id: int = 0):
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

            await ctx.reply(embed=success_embed, mention_author=False)
    except Exception as Error:
        embed_var = discord.Embed(
            title="<:BloxlinkDead:823633973967716363> Error",
            description=Error,
            color=RED,
        )
        embed_var.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)
        embed_var.timestamp = datetime.now()

        await ctx.reply(embed=embed_var)
