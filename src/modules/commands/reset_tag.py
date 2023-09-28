from datetime import datetime

import discord
import requests
from discord.ext.commands import Context, check

from resources.constants import BLURPLE, RED
from resources.checks import is_dev
from resources.helper_bot import instance as bot


@bot.command("reset_tag", description="Reset some information about a tag.", aliases=["rt"])
@check(is_dev)
async def reset_tag(ctx: Context, tag_name: str = "0"):
    """Reset tag use count."""
    try:
        if tag_name == "0":
            raise Exception("Missing argument `tag_name`. Please provide a valid tag name.")
        
        else:
            tag = await bot.db.get_tag(tag_name)
            if tag is None:
                raise Exception(f'The tag "{tag_name}" was not found!')
            await bot.db.update_tag(
                tag['_id'],
                tag['content'],
                use_count=0,
                )
             
    except Exception as Error:
        embed_var = discord.Embed(
            title="<:BloxlinkDead:823633973967716363> Error",
            description=Error,
            color=RED,
        )
        embed_var.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)
        embed_var.timestamp = datetime.now()

        await ctx.reply(embed=embed_var)