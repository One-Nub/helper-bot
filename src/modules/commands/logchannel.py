import typing

from discord import Embed, Interaction, Permissions, TextChannel, app_commands
from discord.app_commands import Choice

from helper_bot import instance as bot

logchannel = app_commands.Group(
    name="logchannel",
    description="Commands related to managing log channels.",
    default_permissions=Permissions(manage_guild=True),
    guild_only=True,
)


@logchannel.command(name="set", description="Set the channels that the helper bot logs to.")
@app_commands.describe(
    log_type="What type of log channel are you setting?",
    channel="The channel that logs will be sent to",
)
@app_commands.choices(
    log_type=[
        Choice(name="Premium Support logs", value=0),
        Choice(name="General logs", value=1),
    ]
)
async def set_log_channels(
    interaction: Interaction, log_type: Choice[int], channel: typing.Optional[TextChannel]
):
    namespace = interaction.namespace

    log_type = namespace.log_type
    channel = namespace.channel

    channel = channel.id if channel else None

    if channel is not None:
        if log_type == 0:
            await bot.db.set_log_channel(
                interaction.guild_id, premium_support=channel if channel is not None else ""
            )
        elif log_type == 1:
            await bot.db.set_log_channel(interaction.guild_id, tag_updates=channel)
    else:
        log_type_str = "premium_support" if log_type == 0 else "tag_updates"
        await bot.db.unset_log_channel(interaction.guild.id, log_type_str)

    content = "premium support threads" if log_type == 0 else "tag updates"
    channel_str = f"set to <#{channel}>" if channel else "unset"

    await interaction.response.send_message(
        f"Your log channel for {content} has been {channel_str}!", ephemeral=True
    )


@logchannel.command(name="view", description="View your currently set log channels.")
async def view_log_channels(interaction: Interaction):
    data = await bot.db.get_log_channels(interaction.guild_id)

    premium = data.get("premium_support")
    general = data.get("tag_updates")

    premium = f"<#{premium}>" if premium else "`Unset`"
    general = f"<#{general}>" if general else "`Unset`"

    embed = Embed()
    embed.description = (
        "### Your set log channels!\n\n" f"- Premium Logs: {premium}\n" f"- Tag Updates/Misc: {general}"
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


bot.tree.add_command(logchannel)
