import logging
import os

from discord import Intents, utils

import config
from helper_bot import HelperBot

BOT_TOKEN = os.environ.get("BOT_TOKEN", config.BOT_TOKEN)
MONGO_URL = os.environ.get("MONGO_URL", config.MONGO_URL)

utils.setup_logging(level=logging.INFO)

intents = Intents(guilds=True, message_content=True, guild_messages=True, emojis=True)
bot = HelperBot(command_prefix=".", mongodb_url=MONGO_URL, intents=intents)

MODULES = ["modules/commands", "modules/events", "modules/premium_support"]

if __name__ == "__main__":
    ## loop through all the files under the commands folder, that's how we check for commands
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
