import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional, Type

import certifi
import discord
from discord.app_commands import CommandTree
from discord.ext import commands
from motor import motor_asyncio

from resources.constants import DEVELOPMENT_GUILDS, TEAM_CENTER_GUILD

instance: "HelperBot" = None  # type: ignore
logger = logging.getLogger()


class HelperBot(commands.Bot):
    def __init__(
        self,
        command_prefix: str,
        mongodb_url: str,
        modules: list[str],
        *,
        help_command: Optional[commands.HelpCommand] = None,
        tree_cls: Type[CommandTree] = CommandTree,
        description: Optional[str] = None,
        intents: discord.Intents,
        sync_commands: bool = True,
        **options: Any,
    ) -> None:
        """Initialize the Helper Bot class.

        Args:
            command_prefix (str): Default prefix for chat commands.
            mongodb_url (str): URL to connect to MongoDB with.
            modules (list[str]): Directories under src/modules that contain commands and cogs to be loaded by Discord.py.
            intents (discord.Intents): Intents for the bot.
            help_command (Optional[commands.HelpCommand], optional): See discord.py docs. Defaults to None.
            tree_cls (Type[CommandTree], optional): See discord.py docs. Defaults to CommandTree.
            description (Optional[str], optional): See discord.py docs. Defaults to None.
        """
        global instance

        self.sync_commands = sync_commands

        super().__init__(
            command_prefix,
            help_command=help_command,
            tree_cls=tree_cls,
            description=description,
            intents=intents,
            **options,
        )

        self.modules = modules

        self.started_at = datetime.now(timezone.utc)
        self.button_handlers = {}
        self.select_menu_handlers = {}

        if mongodb_url:
            self.db = MongoDB(mongodb_url)
        else:
            logger.error("NO MONGODB URL WAS FOUND.")

        instance = self

    async def setup_hook(self):
        # Load commands and cogs. Reads directories under "src/modules", specifically the ones
        # passed as the "modules" parameter.
        for module in self.modules:
            path = os.path.join("src", "modules", module)

            files = [
                filename.removesuffix(".py")
                for filename in os.listdir(path)
                if filename.endswith(".py") and not filename.startswith("__init__")
            ]

            for file in files:
                # Can't have "src." at the start of the path like when we got the files.
                module_path = os.path.join("modules", module, file).replace("/", ".")

                try:
                    logger.info(f"Loading module {module_path}")
                    # Use discord.py's "load_extension" method so our cogs work.
                    await self.load_extension(module_path)
                except commands.errors.NoEntryPointError:
                    # Because of how we're registering commands as not-cogs but still loading them
                    # with load_extension, DPY says this is "wrong". It can be fixed by adding a
                    # setup function to each file that does nothing, but for now it will stay complaining since
                    # the commands work as expected.
                    logger.info(
                        f"D.PY complained about a lack of entry point for {module_path}, "
                        "but it's still loaded!"
                    )

        if self.sync_commands:
            logging.info("Syncing slash commands...")
            await self.tree.sync()

            logging.info("Syncing guild commands...")
            guilds_to_sync = {*DEVELOPMENT_GUILDS, TEAM_CENTER_GUILD}
            for guild in guilds_to_sync:
                try:
                    await self.tree.sync(guild=discord.Object(guild))
                    logging.info(f"Synced guild commands for {guild}.")
                except discord.Forbidden:
                    logging.warning(f"Could not sync guild commands for {guild}.")
        else:
            logging.warning("Commands were not synced with Discord.")

    @property
    def uptime(self) -> timedelta:
        """The current uptime of the bot as a timedelta."""
        return datetime.now(timezone.utc) - self.started_at

    def register_button_handler(self, custom_id_prefix: str):
        """Decorator to register a handler to handle a custom_id for a button.

        Args:
            custom_id_prefix (str): The custom ID that this handler will be for.
        """

        # Basic form of a decorator except we're just using it to add the handler
        # to the relevant dictionary
        def inner(func):
            self.button_handlers[custom_id_prefix] = func

        return inner

    def register_select_menu_handler(self, custom_id_prefix: str):
        """Decorator to register a handler to handle a custom_id for a selection menu.

        Args:
            custom_id_prefix (str): The custom ID that this handler will be for.
        """

        # Basic form of a decorator except we're just using it to add the handler
        # to the relevant dictionary
        def inner(func):
            self.select_menu_handlers[custom_id_prefix] = func

        return inner


class MongoDB:
    def __init__(self, connection_string: str) -> None:
        """Initializes the MongoDB connection.

        Args:
            connection_string (str): The URL to connect to MongoDB with.
        """
        logger.info("Connecting to MongoDB.")
        self.client = motor_asyncio.AsyncIOMotorClient(connection_string, tlsCAFile=certifi.where())
        self.db = self.client["bloxlink_helper"]
        logger.info("MongoDB initialized.")

    ####
    ####################---------TAG METHODS-----------########################
    ####
    async def get_all_tags(self) -> list:
        """Return a list of all the tags in the database.

        Returns:
            list: List of the tags, each tag is a dictionary.
        """
        cursor = self.db["tags"].find()
        return await cursor.to_list(None)

    async def get_tag(self, name: str) -> dict | None:
        """Get a single tag from the database

        Args:
            name (str): The name or alias of the tag to find.

        Returns:
            dict | None: The tag data if it exists, otherwise None.
        """
        name = name.lower()
        query = {
            "$or": [
                {"_id": name},
                {"aliases": name},
            ],
        }

        cursor = await self.db["tags"].find_one(query)
        return cursor

    async def update_tag(
        self,
        name: str,
        content: Optional[str] = None,
        aliases: Optional[list[str]] = None,
        author: Optional[str] = None,
        use_count: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Insert or update a tag in the database based on its name or alias.

        Only updates values based on what you give it, example if you don't include use_count
        it will not modify it.

        Args:
            name (str): Name of the tag that should be updated.
            content (str): The content that the tag should show.
            aliases (list[str], optional): Alternate names for the tag if any. Defaults to None.
                KEY NOTE: MUST BE AN EXHAUSTIVE LIST OF *ALL* ALIASES FOR THIS TAG.
            author (str, optional): ID of the author. Defaults to None.
            use_count (int, optional): Number of times the tag has been used. Defaults to 0.
            created_at (datetime, optional): Date the command was created at. Defaults to None.
            updated_at (datetime, optional): Date the command was last updated at. Defaults to None.
        """
        name = name.lower()
        data = {}

        if content is not None:
            data["content"] = str(content)

        if aliases is not None:
            aliases = [x.lower() for x in aliases]
            data["aliases"] = aliases

        if use_count is not None:
            data["use_count"] = use_count

        if author is not None:
            data["author"] = str(author)

        if created_at is not None:
            data["created_at"] = created_at.isoformat()

        if updated_at is not None:
            data["updated_at"] = updated_at.isoformat()

        if not data:
            logger.warning(f"No data was found when updating the tag {name}.")
            return

        filter_query = {
            "$or": [
                {"_id": name},
                {"aliases": name},
            ],
        }

        await self.db["tags"].update_one(
            filter=filter_query,
            update={"$set": data, "$setOnInsert": {"_id": name}},
            upsert=True,
        )

    async def delete_tag(self, name: str):
        """Removes a tag from the database based on a name or alias.

        Args:
            name (str): The name or alias of the tag.
        """
        name = name.lower()
        query = {
            "$or": [
                {"_id": name},
                {"aliases": name},
            ],
        }
        await self.db["tags"].delete_one(query)

    ####
    ####################---------STAFF METRIC METHODS-----------########################
    ####
    async def update_staff_metric(
        self,
        staff_id: int,
        msg_count: int,
        staff_pos: str,
        tag_count: Optional[int] = 0,
        updated_at: Optional[datetime] = None,
    ):
        """Create a staff metric in the database

        Args:
           staff_id (int): The staff members user ID.
           msg_count (int): Number of messages the staff member has sent.
           staff_pos (str): The Staff members position.
           tag_count (int, optional): Number of tags the staff member has used.
           updated_at (datetime, optional): Date of last message. Defaults to None.
        """
        data = {
            "msg_count": msg_count,
            "staff_pos": staff_pos,
        }

        if updated_at is not None:
            data["updated_at"] = updated_at.isoformat()
        if tag_count is not None:
            data["tag_count"] = tag_count
        filter_query = {
            "$or": [
                {"_id": staff_id},
            ],
        }

        await self.db["metrics"].update_one(
            filter=filter_query,
            update={"$set": data, "$setOnInsert": {"_id": staff_id}},
            upsert=True,
        )

    async def get_staff_metrics(self, staff_id):
        """Get specific metrics for a staff user."""
        cursor = await self.db["metrics"].find_one({"_id": staff_id})
        return cursor

    async def get_all_staff_metrics(self) -> list:
        """Return a list of all the Staff metrics in the database.

        Returns:
            list: List of the Staff activity, each tag is a dictionary.
        """
        cursor = self.db["metrics"].find({"staff_pos": "Staff"})
        return await cursor.to_list(None)

    async def get_all_trial_metrics(self) -> list:
        """Return a list of all the Trial metrics in the database.

        Returns:
            list: List of the Trial activity, each tag is a dictionary.
        """
        cursor = self.db["metrics"].find({"staff_pos": "Trial"})
        return await cursor.to_list(None)

    ####
    ####################---------LOG CHANNEL METHODS-----------########################
    ####
    async def set_log_channel(
        self,
        guild_id: str,
        premium_support: Optional[str] = None,
        tag_updates: Optional[str] = None,
    ):
        """Set the log channel(s) in a guild

        Args:
            guild_id (str): The guild to set the log channels in.
            premium_support (str, optional): Channel to send logs of open support tickets to. Defaults to None.
            tag_updates (str, optional): Channel to send logs of tags being updated to. Defaults to None.
        """
        data = {}
        if premium_support is not None:
            data["premium_support"] = premium_support
        if tag_updates is not None:
            data["tag_updates"] = tag_updates

        if not data:
            return

        await self.db["config"].update_one(
            {"_id": str(guild_id)},
            update={"$set": data},
            upsert=True,
        )

    async def get_log_channels(self, guild_id: str):
        """Get all the log channels in a guild"""
        cursor = await self.db["config"].find_one({"_id": str(guild_id)})
        return cursor

    async def unset_log_channel(self, guild_id: str, log_type: Literal["premium_support", "tag_updates"]):
        """Unset a log channel

        Args:
            guild_id (str): The guild ID to modify the settings for.
            log_type ("Literal['premium_support', 'tag_updates']"): The type of log to remove from the database.
        """
        await self.db["config"].update_one({"_id": str(guild_id)}, update={"$unset": {log_type: ""}})

    ####
    ####################---------AUTO RESPONDER METHODS-----------########################
    ####
    async def update_autoresponse(
        self,
        name: str,
        response_message: Optional[str] = None,
        message_triggers: Optional[list[str]] = None,
        author: Optional[str] = None,
        auto_deletion: Optional[int] = None,
    ):
        """Insert or update an auto responder in the database based on its name.

        Only updates values based on what you give it, example if you don't include auto_deletion
        it will not modify it.

        Args:
            name (str): Name of the auto response trigger that should be updated.
            response_message (str): The message that will be sent in response to a given trigger message.
            message_triggers (list[str], optional): Strings that will result in the response_message being sent.
                KEY NOTE: MUST BE AN EXHAUSTIVE LIST OF *ALL* TRIGGER STRINGS FOR THIS TAG.
            author (str, optional): ID of the author. Defaults to None.
            auto_deletion (int, optional): Time that will be waited until the messages by the author and the bot are removed.
        """
        name = name.lower()
        data = {}

        if response_message is not None:
            data["response_message"] = str(response_message)

        if message_triggers is not None:
            data["message_triggers"] = message_triggers

        if author is not None:
            data["author"] = str(author)

        if auto_deletion is not None and auto_deletion >= 0:
            data["auto_deletion"] = auto_deletion

        if not data:
            logger.warning(f"No data was found when updating the auto response {name}.")
            return

        await self.db["auto_response"].update_one(
            filter={"_id": name},
            update={"$set": data, "$setOnInsert": {"_id": name}},
            upsert=True,
        )

    async def get_all_autoresponses(self) -> list:
        """Return a list of all the auto responses in the database.

        Returns:
            list: List of the auto responses, each response is a dictionary.
        """
        cursor = self.db["auto_response"].find()
        return await cursor.to_list(None)

    async def get_autoresponse(self, name: str) -> dict | None:
        """Get a single auto response from the database

        Args:
            name (str): The name of the auto response to find.

        Returns:
            dict | None: The response data if it exists, otherwise None.
        """
        name = name.lower()
        cursor = await self.db["auto_response"].find_one({"_id": name})
        return cursor

    async def delete_autoresponse(self, name: str):
        """Removes an auto responder from the database based on the given name.

        Args:
            name (str): The name of the auto responder.
        """
        name = name.lower()
        await self.db["auto_response"].delete_one({"_id": name})
