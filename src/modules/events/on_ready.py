import logging

from discord import CustomActivity, Forbidden, Object, Status

from resources.constants import DEVELOPMENT_GUILDS, TEAM_CENTER_GUILD
from resources.helper_bot import instance as bot


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=CustomActivity(name="Your local helper bot!"),
        status=Status.online,
    )

    logging.info("Syncing slash commands...")
    await bot.tree.sync()

    logging.info("Syncing guild commands...")
    guilds_to_sync = {*DEVELOPMENT_GUILDS, TEAM_CENTER_GUILD}
    for guild in guilds_to_sync:
        try:
            await bot.tree.sync(guild=Object(guild))
        except Forbidden:
            logging.warn(f"Could not sync guild commands for {guild}.")

    logging.info(f"Bot ({bot.user.name}#{bot.user.discriminator}) has finished initializing!")
