import asyncio
import logging
import os

from discord import AllowedMentions, Intents, utils

from resources.helper_bot import HelperBot
from resources.secrets import BOT_TOKEN, LINEAR_API_KEY, MONGO_URL  # pylint: disable=E0611

utils.setup_logging(level=logging.INFO)


async def main():
    allowed_mentions = AllowedMentions(roles=False, users=True, everyone=False)

    intents = Intents(guilds=True, message_content=True, guild_messages=True, emojis=True)
    bot = HelperBot(
        command_prefix=".",
        mongodb_url=MONGO_URL,
        intents=intents,
        allowed_mentions=allowed_mentions,
        linear_api_key=LINEAR_API_KEY,
    )

    MODULES = ["modules/commands", "modules/events", "modules/premium_support"]

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

    await bot.start(token=BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
