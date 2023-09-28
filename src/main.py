import logging
import os
import time

from discord import AllowedMentions, Intents, utils

from resources.helper_bot import HelperBot
from resources.secrets import BOT_TOKEN, MONGO_URL  # pylint: disable=E0611

print("Sleeping for 10 seconds")
time.sleep(10)
print("Continuing with setup")

utils.setup_logging(level=logging.INFO)

allowed_mentions = AllowedMentions(roles=False, users=True, everyone=False)

intents = Intents(guilds=True, message_content=True, guild_messages=True, emojis=True)
bot = HelperBot(command_prefix=".", mongodb_url=MONGO_URL, intents=intents, allowed_mentions=allowed_mentions)

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

    bot.run(token=BOT_TOKEN, log_handler=None)
