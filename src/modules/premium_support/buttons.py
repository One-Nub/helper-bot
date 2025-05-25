from datetime import datetime, timezone

from discord import AllowedMentions, ButtonStyle, ChannelType, Embed, Interaction, TextChannel, ui

from resources.constants import BLURPLE
from resources.helper_bot import instance as bot


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

    if type(channel) != TextChannel:
        return await interaction.response.send_message(content="Error creating a thread!", ephemeral=True)

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

    if interaction.guild is None:
        # Impossible unless discord freaks out
        return

    log_channels = await bot.db.get_log_channels(guild_id=str(interaction.guild.id))
    if not log_channels:
        log_channels = {}
    log_channel = log_channels.get("premium_support", "")

    custom_id = "lock_thread"

    if log_channel:
        custom_id += f":{log_channel}"

        channel = bot.get_channel(log_channel)
        if not channel:
            channel = await bot.fetch_channel(log_channel)

        if channel:
            log_embed = Embed(color=BLURPLE, title="Support Thread")
            log_embed.add_field(
                name=":book: Author",
                value=f"{user.mention}\n{user.name}#{user.discriminator}",
                inline=True,
            )
            log_embed.add_field(
                name=":thread: Thread",
                value=thread.mention,
                inline=True,
            )
            log_embed.timestamp = datetime.now(timezone.utc)
            message = await channel.send(embed=log_embed)  # type: ignore

            custom_id += f":{message.id}"

    button = ui.Button(style=ButtonStyle.secondary, emoji="🔒", label="Close", custom_id=custom_id)
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

    if channel is None:
        return await interaction.response.send_message(content=f"Channel apparently does not exist.")

    await interaction.response.send_message(content=f"This support thread has been closed by {user.mention}!")

    if channel.type is ChannelType.private_thread:
        await channel.edit(archived=True, locked=True)

    custom_id = interaction.data["custom_id"]  # type: ignore
    if ":" in custom_id:
        split = custom_id.split(":")
        channel_id = split[1]
        message_id = split[2]

        await bot.http.delete_message(channel_id=channel_id, message_id=message_id)


async def setup(bot): ...
