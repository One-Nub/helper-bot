import logging

import discord

import resources.responder_parsing as resp_parsing
from resources.exceptions import InvalidTriggerFormat
from resources.helper_bot import HelperBot
from resources.models.autoresponse import AutoResponse
from resources.utils.base_embeds import ErrorEmbed, StandardEmbed

from .shared_cache import stored_trigger_map


class MessageEditModal(discord.ui.Modal, title="Update Message"):
    def __init__(self, *, timeout: float | None = None, custom_id: str) -> None:
        super().__init__(timeout=timeout, custom_id=custom_id)

    response_msg: discord.ui.TextInput = discord.ui.TextInput(
        label="Message to send in response", custom_id="message_str", row=1, style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.data is None:
            logging.error("Attempted to respond to request with no interaction data.")
            return

        custom_id: str = str(interaction.data.get("custom_id"))
        custom_data = custom_id.split(":")
        custom_data.pop(0)  # remove "med" segment

        author_id = custom_data[0]
        responder_name = custom_data[1]

        if type(interaction.client) is not HelperBot:
            logging.error("Client wasn't the same as the main instance.")
            return

        bot: HelperBot = interaction.client
        await bot.db.update_autoresponse(
            responder_name,
            response_message=self.response_msg.value,
            author=author_id,
        )
        stored_trigger_map.clear()

        ar = AutoResponse(name=responder_name, response_message=self.response_msg.value, author=author_id)
        embed = StandardEmbed(footer_icon_url=str(interaction.user.display_avatar))
        embed.title = f":BloxlinkHappy: Success! Auto responder `{responder_name}` has been updated."
        embed.add_field(name="New Message:", value=ar.codeblock_response_msg)

        await interaction.response.send_message(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            "An unexpected error occurred. A log has been left for the devs 🫡"
        )
        return await super().on_error(interaction, error)


class NewResponderModal(discord.ui.Modal, title="New Auto Response"):
    def __init__(self, *, timeout: float | None = None, custom_id: str) -> None:
        super().__init__(timeout=timeout, custom_id=custom_id)

    trigger_string: discord.ui.TextInput = discord.ui.TextInput(
        label="Text to trigger response", custom_id="trigger_str", row=0
    )
    response_msg: discord.ui.TextInput = discord.ui.TextInput(
        label="Message to send in response", custom_id="message_str", row=1, style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.data is None:
            logging.error("Attempted to respond to request with no interaction data.")
            return

        custom_id: str = str(interaction.data.get("custom_id"))
        custom_data = custom_id.split(":")
        custom_data.pop(0)  # remove "mcr" segment

        author_id = custom_data[0]
        responder_name = custom_data[1]
        auto_delete = int(custom_data[2])

        resp_parsing.validate_trigger_string(self.trigger_string.value)

        if type(interaction.client) is not HelperBot:
            logging.error("Client wasn't the same as the main instance.")
            return

        bot: HelperBot = interaction.client
        await bot.db.update_autoresponse(
            responder_name,
            response_message=self.response_msg.value,
            message_triggers=[self.trigger_string.value],
            author=author_id,
            auto_deletion=auto_delete,
        )
        stored_trigger_map.clear()

        ar = AutoResponse(
            name=responder_name,
            response_message=self.response_msg.value,
            author=author_id,
            message_triggers=[self.trigger_string.value],
            auto_deletion=auto_delete,
        )

        await interaction.response.send_message(
            (
                f"Success! Your new auto responder has been saved.\n"
                "*If you want to add more trigger strings, use `/autoresponder trigger add`*"
            ),
            embed=ar.embed.set_footer(text="Bloxlink Helper", icon_url=interaction.user.display_avatar),
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if type(error) == InvalidTriggerFormat:
            embed = ErrorEmbed(footer_icon_url=str(interaction.user.display_avatar))
            embed.title = ":BloxlinkDead: Invalid Trigger String."
            embed.add_field(name="Trigger string:", value=self.trigger_string.value)

            # Not using AutoResponse class bc we would have to parse the name out and stuff again.
            clean_message = self.response_msg.value.replace("```", r"\`\`\`")
            embed.add_field(name="Message:", value=f"```{clean_message}```")

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                "An unexpected error occurred. A log has been left for the devs 🫡"
            )
            return await super().on_error(interaction, error)
