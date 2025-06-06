import logging

from discord import CustomActivity, Status

from resources.helper_bot import instance as bot


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=CustomActivity(name="Your local helper bot!"),
        status=Status.online,
    )

    if bot.user:
        logging.info(f"Bot ({bot.user.name}#{bot.user.discriminator}) has finished initializing!")
    else:
        logging.error("Bot is ready without being logged in. This is probably not intentional!")


async def setup(bot): ...
