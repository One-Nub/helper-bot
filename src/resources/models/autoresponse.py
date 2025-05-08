from datetime import datetime
from typing import Optional

import discord
from attrs import Factory, define, field

from resources.constants import BLOXLINK_HAPPY, UNICODE_ZERO_WIDTH_SPACE
from resources.utils.base_embeds import StandardEmbed


def default2int(x) -> int:
    if x is None:
        return 0
    return int(x)


@define(kw_only=True)
class AutoResponse:
    name: str
    response_message: str
    author: str = field(converter=str)
    message_triggers: list[str] = field(default=Factory(list))
    auto_deletion: Optional[int] = field(converter=default2int, default=0)

    @classmethod
    def from_database(cls, data: dict):
        data["name"] = data["_id"]
        del data["_id"]

        return cls(**data)  # automatically assign variables to db values

    @property
    def embed(self) -> discord.Embed:
        embed = StandardEmbed()
        embed.title = f"{BLOXLINK_HAPPY} Auto Responder Info: {self.name}"

        trigger_strings = [f"`{trigger_str}`" for trigger_str in self.message_triggers]
        final_trigger_string = ", ".join(trigger_strings)

        embed.add_field(name="Trigger Strings", value=final_trigger_string, inline=False)
        embed.add_field(name="Response", value=f"{self.codeblock_response_msg}", inline=False)
        embed.add_field(
            name="Auto Delete",
            value=(
                "Message does not auto delete."
                if self.auto_deletion == 0
                else f"After `{self.auto_deletion}` seconds"
            ),
        )
        embed.add_field(name="Author", value=f"<@{self.author}> ({self.author})")

        return embed

    @property
    def codeblock_response_msg(self) -> str:
        # TODO: this breaks copying and pasting a raw message with code blocks in it... as long as people
        # don't use code blocks in their replies it's fine
        altered_msg = self.response_message.replace(
            "```",
            f"{UNICODE_ZERO_WIDTH_SPACE}`{UNICODE_ZERO_WIDTH_SPACE}`{UNICODE_ZERO_WIDTH_SPACE}`{UNICODE_ZERO_WIDTH_SPACE}",
        )
        return f"```{altered_msg}```"

    def __str__(self) -> str:
        # trigger_strings = [f"`{trigger_str}`" for trigger_str in self.message_triggers]
        auto_del_str = (
            "Message does not auto delete."
            if self.auto_deletion == 0
            else f"After `{self.auto_deletion}` seconds"
        )

        return (
            f"__Name__: `{self.name}`"
            f"\n__Trigger Strings__: ```{self.message_triggers}```"
            f"\n__Message__: ```{self.response_message}```"
            f"\n__Auto Deletion Time__: ```{auto_del_str}```"
        )
