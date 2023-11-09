from datetime import datetime

import discord
from discord.ext.commands import Context, check
from googletrans import Translator

from resources.checks import is_staff_or_trial
from resources.constants import BLURPLE, RED
from resources.helper_bot import instance as bot


@bot.command("translate", description="Translate text to different languages.", aliases=["tr"])
@check(is_staff_or_trial)
async def translate(ctx: Context, *, translate_string: str = "0"):
    """Translate provided text to another language."""
    try:
        if translate_string == "0":
            raise Exception(
                "Missing argument `translate_string`. Please provide the string you would like to translate."
            )

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


@discord.app_commands.context_menu(name="Translate")
async def translate_menu(interaction: discord.Interaction, message: discord.Message):
    allowed_to_run = await is_staff_or_trial(interaction)
    if not allowed_to_run:
        await interaction.response.send_message(
            content="You are not allowed to use this context menu!",
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions(users=False),
        )
        return

    translator = Translator()
    translation = translator.translate(message.content, dest="en")

    success_embed = discord.Embed()
    success_embed.title = "<:BloxlinkHappy:823633735446167552> Translation Complete"
    success_embed.description = (
        f"Processed text from `{translation.src}` (detected) to "
        f"`en`\n\n**Translated Text:**\n```{translation.text}```"
    )
    success_embed.color = BLURPLE
    success_embed.timestamp = datetime.now()
    success_embed.set_footer(text="Bloxlink Helper", icon_url=interaction.user.display_avatar)

    await interaction.response.send_message(
        embed=success_embed,
        ephemeral=True,
        allowed_mentions=discord.AllowedMentions(users=False),
    )


bot.tree.add_command(translate_menu)
