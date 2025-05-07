from datetime import datetime, timezone
from typing import Any, Literal

import discord

from resources.constants import BLOXLINK_DEAD, BLURPLE, RED


class StandardEmbed(discord.Embed):
    def __init__(
        self,
        *,
        title: Any | None = None,
        type: (
            Literal["rich"]
            | Literal["image"]
            | Literal["video"]
            | Literal["gifv"]
            | Literal["article"]
            | Literal["link"]
            | Literal["poll_result"]
        ) = "rich",
        url: Any | None = None,
        description: Any | None = None,
        timestamp: datetime | None = datetime.now(timezone.utc),
        footer_icon_url: str | None = None,
    ):
        super().__init__(
            color=BLURPLE,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

        if footer_icon_url:
            self.set_footer(text="Bloxlink Helper", icon_url=footer_icon_url)


class ErrorEmbed(discord.Embed):
    def __init__(
        self,
        *,
        title: Any | None = f"{BLOXLINK_DEAD} Error",
        type: (
            Literal["rich"]
            | Literal["image"]
            | Literal["video"]
            | Literal["gifv"]
            | Literal["article"]
            | Literal["link"]
            | Literal["poll_result"]
        ) = "rich",
        url: Any | None = None,
        description: Any | None = None,
        timestamp: datetime | None = datetime.now(timezone.utc),
        footer_icon_url: str | None = None,
    ):
        super().__init__(
            color=RED,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

        if footer_icon_url:
            self.set_footer(text="Bloxlink Helper", icon_url=footer_icon_url)
