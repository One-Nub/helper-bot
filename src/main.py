import argparse
import logging

import uvloop
from discord import AllowedMentions, Intents

from resources.constants import MODULES
from resources.helper_bot import HelperBot
from resources.secrets import BOT_TOKEN, MONGO_URL  # pylint: disable=E0611 # type: ignore

# cspell: disable-next-line
logging.basicConfig(format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", level=logging.INFO)

parser = argparse.ArgumentParser(prog="helper-bot")
parser.add_argument("-ns", "--no-sync", action="store_true")
args = parser.parse_args()


async def main():
    allowed_mentions = AllowedMentions(roles=False, users=True, everyone=False)
    intents = Intents(guilds=True, message_content=True, guild_messages=True, emojis=True)

    bot = HelperBot(
        command_prefix=".",
        mongodb_url=MONGO_URL,
        intents=intents,
        allowed_mentions=allowed_mentions,
        modules=MODULES,
        sync_commands=(not args.no_sync),
    )

    await bot.start(token=BOT_TOKEN)


if __name__ == "__main__":
    uvloop.run(main())
