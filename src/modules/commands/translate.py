from datetime import datetime
import discord
from discord.ext.commands import Context, check

from resources.constants import BLURPLE, RED
from resources.checks import is_staff
from resources.helper_bot import instance as bot
from googletrans import Translator

@bot.command("translate", description="Translate text to different languages.", aliases=["tr"])
@check(is_staff)
async def translate(ctx: Context, *, translate_string: str = "0"):
    """Translate provided text to another language."""
    try:
        if translate_string == "0":
            raise Exception("Missing argument `translate_string`. Please provide the string you would like to translate.")
        
        else:
            translator = Translator()
            translation = translator.translate(translate_string, dest="en")
            translation_src = translation.src
            success_embed = discord.Embed()
            success_embed.title = "<:BloxlinkHappy:823633735446167552> Translation Complete"
            success_embed.description = f"Processed text from `{translation_src}` (detected) to `en`\n\n**Translated Text:**\n```{translation.text}```"
            success_embed.color = BLURPLE
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