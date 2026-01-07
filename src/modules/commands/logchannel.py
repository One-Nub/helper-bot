import typing

from discord import Embed, Interaction, Permissions, TextChannel, app_commands
from discord.app_commands import Choice

from resources.checks import is_staff
from resources.helper_bot import instance as bot

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
        Choice(name="Mod logs", value=2),
    ]
)
@app_commands.check(is_staff)
async def set_log_channels(
    interaction: Interaction, log_type: Choice[int], channel: typing.Optional[TextChannel]
):
    # ngl, I can't remember why we needed to use namespace here, but it breaks without it.
    namespace = interaction.namespace
    log_type = namespace.log_type
    channel = namespace.channel

    channel_id = str(channel.id) if channel else None

    if channel_id is not None:
        match log_type:
            case 0:
                await bot.db.set_log_channel(
                    str(interaction.guild_id), premium_support=channel_id if channel is not None else ""
                )
            case 1:
                await bot.db.set_log_channel(str(interaction.guild_id), tag_updates=channel_id)
            case 2:
                await bot.db.set_log_channel(str(interaction.guild_id), moderation=channel_id)

    else:
        log_type_str = (
            "premium_support" if log_type == 0 else "tag_updates" if log_type == 1 else "moderation"
        )
        await bot.db.unset_log_channel(str(interaction.guild_id), log_type_str)

    content = "premium support threads" if log_type == 0 else "tag updates" if log_type == 1 else "moderation"
    channel_str = f"set to <#{channel_id}>" if channel else "unset"

    await interaction.response.send_message(
        f"Your log channel for {content} has been {channel_str}!", ephemeral=True
    )


@logchannel.command(name="view", description="View your currently set log channels.")
@app_commands.check(is_staff)
async def view_log_channels(interaction: Interaction):
    data = await bot.db.get_log_channels(str(interaction.guild_id))
    if data is None:
        data = {}

    premium = data.get("premium_support")
    general = data.get("tag_updates")
    mod = data.get("moderation")

    premium = f"<#{premium}>" if premium else "`Unset`"
    general = f"<#{general}>" if general else "`Unset`"
    mod = f"<#{mod}>" if mod else "`Unset`"

    embed = Embed()
    embed.description = (
        "### Your set log channels!\n\n"
        f"- Premium Logs: {premium}\n"
        f"- Tag Updates/Misc: {general}\n"
        f"- Moderation Logs: {mod}"
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@logchannel.error
async def on_error(interaction: Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            content="You do not have permissions to use this command!",
            ephemeral=True,
        )
        return

    raise error


async def setup(bot):
    bot.tree.add_command(logchannel)
