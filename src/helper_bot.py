import importlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Type

import discord
from discord.app_commands import CommandTree
from discord.ext import commands
from motor import motor_asyncio

instance: "HelperBot" = None
logger = logging.getLogger()


class HelperBot(commands.Bot):
    def __init__(
        self,
        command_prefix: str,
        mongodb_url: str,
        *,
        help_command: Optional[commands.HelpCommand] = None,
        tree_cls: Type[CommandTree] = CommandTree,
        description: Optional[str] = None,
        intents: discord.Intents,
        **options: Any,
    ) -> None:
        """Initialize the Helper Bot class.

        Args:
            command_prefix (str): Default prefix for chat commands.
            mongodb_url (str): URL to connect to MongoDB with.
            intents (discord.Intents): Intents for the bot.
            help_command (Optional[commands.HelpCommand], optional): See discord.py docs. Defaults to None.
            tree_cls (Type[CommandTree], optional): See discord.py docs. Defaults to CommandTree.
            description (Optional[str], optional): See discord.py docs. Defaults to None.
        """
        global instance

        super().__init__(
            command_prefix,
            help_command=help_command,
            tree_cls=tree_cls,
            description=description,
            intents=intents,
            **options,
        )

        self.started_at = datetime.utcnow()
        self.button_handlers = {}
        if mongodb_url:
            self.db = MongoDB(mongodb_url)
        else:
            logging.error("NO MONGODB URL WAS FOUND.")
        instance = self

    @property
    def uptime(self) -> timedelta:
        """The current uptime of the bot as a timedelta."""
        return datetime.utcnow() - self.started_at

    @staticmethod
    def load_module(import_name: str) -> None:
        """Loads a python module based on the import name

        Args:
            import_name (str): The name of the module to import.
        """
        try:
            importlib.import_module(import_name)

        except (ImportError, ModuleNotFoundError) as e:
            logger.error(f"Failed to import {import_name}: {e}")
            raise e

        except Exception as e:
            logger.error(f"Module {import_name} errored: {e}")
            raise e

        logging.info(f"Loaded module {import_name}")

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


class MongoDB:
    def __init__(self, connection_string: str) -> None:
        """Initializes the MongoDB connection.

        Args:
            connection_string (str): The URL to connect to MongoDB with.
        """
        logging.info("Connecting to MongoDB.")
        self.client = motor_asyncio.AsyncIOMotorClient(connection_string)
        self.db = self.client["bloxlink_helper"]
        logging.info("MongoDB initialized.")

    async def get_all_tags(self) -> list:
        """Return a list of all the tags in the database.

        Returns:
            list: List of the tags, each tag is a dictionary.
        """
        cursor = self.db["tags"].find()
        return await cursor.to_list(None)

    async def get_tag(self, name: str):
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
        content: str,
        aliases: list[str] = None,
        author: str = None,
        use_count: int = 0,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        """Insert or update a tag in the database based on its name or alias.

        Args:
            name (str): Name of the tag that should be updated.
            content (str): The content that the tag should show.
            aliases (list[str], optional): Alternate names for the tag if any. Defaults to None.
            author (str, optional): ID of the author. Defaults to None.
            use_count (int, optional): Number of times the tag has been used. Defaults to 0.
            created_at (datetime, optional): Date the command was created at. Defaults to None.
            updated_at (datetime, optional): Date the command was last updated at. Defaults to None.
        """
        data = {
            "content": content,
            "aliases": aliases if aliases else [],
            "use_count": use_count,
        }
        if author is not None:
            data["author"] = author

        if created_at is not None:
            data["created_at"] = created_at.isoformat()

        if updated_at is not None:
            data["updated_at"] = updated_at.isoformat()

        filter_query = {
            "$or": [
                {"_id": name},
                {"aliases": name},
            ],
        }

        await self.db["tags"].update_one(
            filter=filter_query,
            update={"$set": data},
            upsert=True,
        )

    async def delete_tag(self, name: str):
        """Removes a tag from the database based on a name or alias.

        Args:
            name (str): The name or alias of the tag.
        """
        query = {
            "$or": [
                {"_id": name},
                {"aliases": name},
            ],
        }
        await self.db["tags"].delete_one(query)
