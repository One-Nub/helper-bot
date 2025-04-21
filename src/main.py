import asyncio
import logging

from discord import AllowedMentions, Intents, utils

from resources.constants import MODULES
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
        modules=MODULES,
    )

    await bot.start(token=BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
