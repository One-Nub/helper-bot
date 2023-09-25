from discord import (
    ButtonStyle,
    Color,
    Embed,
    Interaction,
    TextChannel,
    app_commands,
    ui,
)

from constants import BLURPLE
from helper_bot import instance as bot


@bot.tree.command(
    name="premium_support_message",
    description="Send the premium support message to a channel.",
)
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(channel="The channel to send the message to.")
@app_commands.guild_only()
async def send_premium_msg(interaction: Interaction, channel: TextChannel):
    view: ui.View = ui.View(timeout=None)

    support_button: ui.Button = ui.Button(
        style=ButtonStyle.blurple,
        label="Get Support!",
        custom_id="premium_support",
    )

    view.add_item(support_button)

    embed: Embed = Embed(color=Color(BLURPLE))
    embed.description = (
        "### <:BloxlinkConfused:823633690910916619> Need some help with something related to Bloxlink?\n"
        "Use the button below to open a private thread to get support and our staff team will get back "
        "to you as soon as possible!"
    )

    await channel.send(embed=embed, view=view)
    await interaction.response.send_message("The message was successfully sent!", ephemeral=True)
