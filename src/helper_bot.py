import importlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

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
        tree_cls: CommandTree = CommandTree,
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
        instance = self

    @property
    def uptime(self) -> timedelta:
        return datetime.utcnow() - self.started_at

    @staticmethod
    def load_module(import_name: str) -> None:
        try:
            importlib.import_module(import_name)

        except (ImportError, ModuleNotFoundError) as e:
            logger.error(f"Failed to import {import_name}: {e}")
            raise e

        except Exception as e:
            logger.error(f"Module {import_name} errored: {e}")
            raise e

        logging.info(f"Loaded module {import_name}")
