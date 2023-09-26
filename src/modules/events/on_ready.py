import logging

from resources.helper_bot import instance as bot


@bot.event
async def on_ready():
    logging.info("Syncing slash commands...")
    await bot.tree.sync()
    logging.info("Bot has been initialized.")
