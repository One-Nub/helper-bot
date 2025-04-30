import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from textdistance import Sorensen

import resources.responder_parsing as resp_parsing
from resources.checks import is_staff
from resources.constants import RED
from resources.exceptions import InvalidTriggerFormat
from resources.helper_bot import HelperBot
from resources.models.autoresponse import AutoResponse

"""
Potential DB structure:
- Id or name to refer to the responder as - common name
- triggers (list of strings)
- message
- auto delete
---

Special characters: 
    * = prefix/suffix matching of a string
    ... = large partial matching (so start-end and it would match "really start wow some random stuff end whee")
        just represents "lots of content" between the start word and the end
        ! cannot be used with prefix/suffix matching in the same trigger string.
        ! cannot be used multiple times in one trigger string.
    , = splits trigger to different words that MUST uniquely exist in the string.

cspell: disable
Example valid triggers:
    "verify"
    "help pls" - must show up exactly as "help pls" in the message (case insensitive)
    "ban*" - matches "ban", "banned", "banning", etc
    "how...verify" (or "how ... verify") - matches "how verify", "how do i verify", "how john cena verify?", "how can i averify"
        but not "verify how" or "verify pls how", nor "hob do i verbify"
    "how, join" - matches "how do i join bloxlink", "how cna i join", but not "how can i joine", "join pls", "how play", "howjoin"

Asterisks in the middle of phrases (i.e. "how*join") shall not be treated as partial matching options.
cspell: enable
"""


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

        # TODO: If caching is added, clear the cache. Or update with added trigger. functools.lru_cache
        bot: HelperBot = interaction.client
        await bot.db.update_autoresponse(
            responder_name,
            response_message=self.response_msg.value,
            message_triggers=[self.trigger_string.value],
            author=author_id,
            auto_deletion=auto_delete,
        )

        ar = AutoResponse(
            name=responder_name,
            response_message=self.response_msg.value,
            author=author_id,
            message_triggers=[self.trigger_string.value],
            auto_deletion=auto_delete,
        )

        # TODO: Improve message (use embed)
        await interaction.response.send_message(
            (
                f"Success! Your new auto responder has been saved.\n"
                "*If you want to add more trigger strings, use `/autoresponder trigger add`*"
            ),
            embed=ar.embed.set_footer(text="Bloxlink Helper", icon_url=interaction.user.display_avatar),
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if type(error) == InvalidTriggerFormat:
            await interaction.response.send_message(
                f"Invalid trigger string: {str(error)}\n"
                f">>> Provided message content: \n__TRIGGER STRING:__ ```{self.trigger_string.value}```\n__MESSAGE__: ```\n{self.response_msg.value}```"
            )
        else:
            await interaction.response.send_message(
                "An unexpected error occurred. A log has been left for the devs 🫡"
            )
            return await super().on_error(interaction, error)


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

        # TODO: If caching is added, clear the cache. Or update with added trigger. functools.lru_cache
        bot: HelperBot = interaction.client
        await bot.db.update_autoresponse(
            responder_name,
            response_message=self.response_msg.value,
            author=author_id,
        )
        # TODO: Improve message (use embed)
        await interaction.response.send_message(
            (
                f"Success! Your new message has been saved.\n"
                f">>> __New Response:__\n```{self.response_msg.value}```"
            ),
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            "An unexpected error occurred. A log has been left for the devs 🫡"
        )
        return await super().on_error(interaction, error)


@app_commands.guild_only()
class Autoresponder(commands.GroupCog, name="autoresponder"):
    def __init__(self, bot):
        self.bot: HelperBot = bot
        super().__init__()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:  # type: ignore[reportIncompatibleMessageOverride] fmt: skip
        return await is_staff(interaction)

    @commands.Cog.listener("on_message")
    async def message_handler(self, message: discord.Message):
        if message.author.bot:
            return

    ####
    ####################---------AUTOFILL-----------########################
    ####

    async def name_autofill(self, interaction: discord.Interaction, user_input: str):
        # TODO: Get from cache instead? Add helper methods for database somewhere?
        auto_responses = await self.bot.db.get_all_autoresponses()
        valid_names = [AutoResponse.from_database(ar).name for ar in auto_responses]

        if user_input == "":
            return [app_commands.Choice(name=name, value=name) for name in valid_names][:25]

        valid_names = [
            item
            for item in valid_names
            if Sorensen().similarity(user_input, item) > 0.65 or user_input in item
        ]
        return [app_commands.Choice(name=name, value=name) for name in valid_names][:25]

    ####
    ####################---------BASE COMMANDS-----------########################
    ####

    @app_commands.command(name="help", description="Learn how to use the command!")
    async def command_help(self, ctx: discord.Interaction):
        await ctx.response.send_message("placeholder")

    @app_commands.command(name="all", description="View all set automatic responses")
    async def view_all(self, ctx: discord.Interaction):
        await ctx.response.send_message("placeholder")

    @app_commands.command(name="view", description="View a specific automatic response")
    @app_commands.describe(name="The admin-facing name for the responder")
    @app_commands.autocomplete(name=name_autofill)
    async def view_single(self, ctx: discord.Interaction, name: str):
        responder = await self.bot.db.get_autoresponse(name=name)
        if responder is None:
            return await ctx.response.send_message(
                f"Could not find the responder associated with the name `{name}`!",
                ephemeral=True,
            )

        ar: AutoResponse = AutoResponse.from_database(responder)

        return await ctx.response.send_message(
            embed=ar.embed.set_footer(text="Bloxlink Helper", icon_url=ctx.user.display_avatar)
        )

    @app_commands.command(name="create", description="Create an automatic response")
    @app_commands.describe(
        name="A unique admin-facing name for this responder",
        autodelete="How long (in seconds) until the bot vaporizes the original message and response?",
    )
    @app_commands.autocomplete(name=name_autofill)
    async def add_responder(
        self,
        ctx: discord.Interaction,
        name: app_commands.Range[str, 1, 50],
        autodelete: Optional[app_commands.Range[int, 0, 60]],
    ):
        # Defer?
        responder = await self.bot.db.get_autoresponse(name=name)
        if responder is not None:
            return await ctx.response.send_message(
                f"A responder with the name `{name}` already exists!", ephemeral=True
            )

        name = name.replace(":", "-")  # remove colons for parsing reasons
        autodelete = autodelete if autodelete is not None else 0
        await ctx.response.send_modal(NewResponderModal(custom_id=f"mcr:{ctx.user.id}:{name}:{autodelete}"))

    @app_commands.command(name="delete", description="Remove an automatic response")
    @app_commands.describe(name="The admin-facing name for the responder")
    @app_commands.autocomplete(name=name_autofill)
    async def delete_responder(self, ctx: discord.Interaction, name: str):
        responder = await self.bot.db.get_autoresponse(name=name)
        if responder is None:
            return await ctx.response.send_message(
                f"Could not find the responder associated with the name `{name}`! No changes were made.",
                ephemeral=True,
            )
        ar = AutoResponse.from_database(responder)
        embed = ar.embed
        embed.title = ":BloxlinkDab: Deleted Auto Responder Content"
        embed.set_footer(text="Bloxlink Helper", icon_url=ctx.user.display_avatar)
        embed.color = RED

        await self.bot.db.delete_autoresponse(name=name)
        await ctx.response.send_message(
            f"Success! The responder associated with the name `{name}` was removed.", embed=embed
        )

    ####
    ####################---------REPLY MESSAGE COMMANDS-----------########################
    ####

    message_group = app_commands.Group(name="message", description="Manage responder messages.")

    @message_group.command(
        name="raw", description="View raw string of what the response is for the given responder."
    )
    @app_commands.autocomplete(name=name_autofill)
    async def message_raw(self, ctx: discord.Interaction, name: str):
        responder = await self.bot.db.get_autoresponse(name=name)
        if responder is None:
            return await ctx.response.send_message(
                f"Could not find the responder associated with the name `{name}`! No changes were made.",
                ephemeral=True,
            )
        ar = AutoResponse.from_database(responder)

        return await ctx.response.send_message(
            f"### Raw Message Content for `{ar.name}`\n```{ar.response_message}```"
        )

    @message_group.command(
        name="edit", description="Change what message is sent as a reply for the given responder."
    )
    @app_commands.autocomplete(name=name_autofill)
    async def message_edit(self, ctx: discord.Interaction, name: str):
        # Defer?
        responder = await self.bot.db.get_autoresponse(name=name)
        if responder is None:
            return await ctx.response.send_message(
                f"No auto response with the name `{name}` exists!", ephemeral=True
            )

        await ctx.response.send_modal(MessageEditModal(custom_id=f"med:{ctx.user.id}:{name}"))

    ####
    ####################---------MESSAGE TRIGGER COMMANDS-----------########################
    ####

    trigger_group = app_commands.Group(name="trigger", description="Manage triggers for auto responders.")

    @trigger_group.command(name="add", description="Add an additional message string to respond to.")
    @app_commands.autocomplete(name=name_autofill)
    async def trigger_add(self, ctx: discord.Interaction, name: str, trigger: str):
        responder = await self.bot.db.get_autoresponse(name=name)
        if responder is None:
            return await ctx.response.send_message(
                f"No auto response with the name `{name}` exists!", ephemeral=True
            )

        try:
            resp_parsing.validate_trigger_string(trigger)
        except InvalidTriggerFormat as err:
            return await ctx.response.send_message(
                f"Invalid trigger string: {str(err)}\n"
                f">>> Provided content: \n__TRIGGER STRING:__ ```{trigger}```",
                ephemeral=True,
            )

        ar = AutoResponse.from_database(responder)
        if trigger in ar.message_triggers:
            return await ctx.response.send_message(
                f"No changes were made, that trigger string is already set!", ephemeral=True
            )

        ar.message_triggers.append(trigger)
        await self.bot.db.update_autoresponse(name=name, message_triggers=ar.message_triggers)

        await ctx.response.send_message(
            content=f"Success! Auto responder `{name}` has been updated.\n"
            f'```The string "{trigger}" will now trigger the response: "{ar.response_message}"```'
        )

    @trigger_group.command(name="delete", description="Remove a message string that is responded to.")
    @app_commands.autocomplete(name=name_autofill)
    async def trigger_del(self, ctx: discord.Interaction, name: str):
        pass

    ####
    ####################---------AUTO DELETION COMMANDS-----------########################
    ####

    autodelete_group = app_commands.Group(
        name="autodelete", description="Manage deletion timeout for auto responders."
    )

    @autodelete_group.command(
        name="edit", description="Set time in seconds for the OG message and reply to vanish. 0 to unset."
    )
    @app_commands.autocomplete(name=name_autofill)
    async def autodelete_edit(self, ctx: discord.Interaction, name: str, duration: int):
        responder = await self.bot.db.get_autoresponse(name=name)
        if responder is None:
            return await ctx.response.send_message(
                f"No auto response with the name `{name}` exists!", ephemeral=True
            )

        ar = AutoResponse.from_database(responder)
        if ar.auto_deletion == duration:
            return await ctx.response.send_message(
                f"No changes were made, that duration matches what is already set!", ephemeral=True
            )

        await self.bot.db.update_autoresponse(name, author=str(ctx.user.id), auto_deletion=duration)

        response = (
            "Message and reply do not auto delete after responding."
            if duration == 0
            else f"Message and reply will now delete after {duration} seconds."
        )
        await ctx.response.send_message(
            content=f"Success! Auto responder `{name}` has been updated.\n```{response}```"
        )


async def setup(bot: HelperBot):
    await bot.add_cog(Autoresponder(bot))
