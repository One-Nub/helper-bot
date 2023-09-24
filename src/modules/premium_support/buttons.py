from discord import AllowedMentions, ButtonStyle, ChannelType, Embed, Interaction, ui

from constants import BLURPLE
from helper_bot import instance as bot


@bot.register_button_handler("premium_support")
async def support_button_handler(interaction: Interaction):
    """Creates a private support thread for the user who pressed the button.

    Creates the thread and sends a basic introduction embed telling the user what they can do
    in the thread, as well as adding a lock button so that they (or anyone else in the thread) can
    close the thread.

    The bot also sends a log message to the set thread log channel, which shows active/open threads for staff.

    Args:
        interaction (Interaction): The button press interaction.
    """
    channel = interaction.channel
    user = interaction.user

    thread = await channel.create_thread(name=f"{user.name}")
    await thread.add_user(user)

    embed = Embed(color=BLURPLE)
    embed.set_author(
        name=f"Support Thread | {user.name}#{user.discriminator}",
        icon_url=user.display_avatar.url,
    )
    embed.description = (
        ":wave: Welcome to your support thread!\n\n"
        "Our helpers will be with you shortly! In the meantime though, please post some messages about "
        "what it is you need help with.\n\n"
        "> *Are we taking too long? If 10 minutes have passed, ping the "
        # Trial helper and helper roles
        "<@&818919735193632858> and <@&412791520316358656> roles!*"
    )

    view = ui.View(timeout=None)

    # TODO: With database added, get the log channel and send a log msg to it saying a thread has been
    # opened. THEN for the created message, add it to the button custom_id so that way on thread close
    # the message is deleted.
    button = ui.Button(style=ButtonStyle.secondary, emoji="🔒", label="Close", custom_id=f"lock_thread")
    view.add_item(button)

    await thread.send(
        embed=embed,
        view=view,
        content=f"{user.mention} has opened a thread!",
        allowed_mentions=AllowedMentions(users=False),
    )

    await interaction.response.send_message(content="Your support thread has been opened!", ephemeral=True)


@bot.register_button_handler("lock_thread")
async def lock_button_handler(interaction: Interaction):
    """Closes the support thread.

    On close the bot sends a message saying who closed the thread, and then archives and locks the thread.
    The bot then deletes the log message from the active/open thread log channel.

    Args:
        interaction (Interaction): The button press interaction.
    """
    channel = interaction.channel
    user = interaction.user

    await interaction.response.send_message(content=f"This support thread has been closed by {user.mention}!")

    if channel.type is ChannelType.private_thread:
        await channel.edit(archived=True, locked=True)

    # TODO: Delete message from log channel
