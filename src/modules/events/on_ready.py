import logging

from discord import CustomActivity, Status

from resources.helper_bot import instance as bot


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=CustomActivity(name="Your local helper bot!"),
        status=Status.online,
    )

    logging.info("Syncing slash commands...")
    await bot.tree.sync()

    logging.info(f"Bot ({bot.user.name}#{bot.user.discriminator}) has finished initializing!")
