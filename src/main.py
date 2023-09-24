import logging
import os

from discord import Intents, utils

import config
from helper_bot import HelperBot

intents = Intents(guilds=True, message_content=True, guild_messages=True, emojis=True)
bot = HelperBot(command_prefix=".", intents=intents)

MODULES = ["modules/commands", "modules/events"]

if __name__ == "__main__":
    utils.setup_logging(level=logging.INFO)

    for directory in MODULES:
        files = [
            name
            for name in os.listdir("src/" + directory.replace(".", "/"))
            if name[:1] != "." and name[:2] != "__" and name != "_DS_Store"
        ]

        for filename in [f.replace(".py", "") for f in files]:
            if filename in ("bot", "__init__"):
                continue

            bot.load_module(f"{directory.replace('/','.')}.{filename}")

    bot.run(token=config.BOT_TOKEN, log_handler=None)
