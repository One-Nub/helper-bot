import importlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Type

import discord
from discord.app_commands import CommandTree
from discord.ext import commands

instance: "HelperBot" = None
logger = logging.getLogger()


class HelperBot(commands.Bot):
    def __init__(
        self,
        command_prefix: str,
        *,
        help_command: Optional[commands.HelpCommand] = None,
        tree_cls: Type[CommandTree] = CommandTree,
        description: Optional[str] = None,
        intents: discord.Intents,
        **options: Any,
    ) -> None:
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
