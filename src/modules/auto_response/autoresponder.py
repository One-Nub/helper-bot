import asyncio
import logging
import math
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from textdistance import Sorensen

import resources.responder_parsing as resp_parsing
from resources.checks import is_staff
from resources.constants import RED, UNICODE_LEFT, UNICODE_RIGHT, UNICODE_RIGHT_ALT
from resources.exceptions import InvalidTriggerFormat
from resources.helper_bot import HelperBot
from resources.helper_bot import instance as bot_instance
from resources.models.autoresponse import AutoResponse
from resources.models.interaction_data import MessageComponentData
from resources.utils.base_embeds import ErrorEmbed, StandardEmbed
from resources.utils.timed_user_cooldown import TimedUserCooldown

from .modals import MessageEditModal, NewResponderModal
from .shared_cache import stored_trigger_map

MAX_ITEMS_PER_PAGE = 10


# TODO: consider moving autoresponder to a subfolder, and moving modals into their own files.


@app_commands.guild_only()
class Autoresponder(commands.GroupCog, name="autoresponder"):
    def __init__(self, bot):
        self.bot: HelperBot = bot
        self.cooldown = TimedUserCooldown()
        super().__init__()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:  # type: ignore
        # type ignored because it is freaking out about return types and overrides.
        return await is_staff(interaction)

    @commands.Cog.listener("on_message")
    async def message_handler(self, message: discord.Message):
        if message.author.bot:
            return

        if not stored_trigger_map:
            # Update local map.
            logging.info("Updating the stored trigger map...")
            auto_responses = await self.bot.db.get_all_autoresponses()
            auto_responses = [AutoResponse.from_database(x) for x in auto_responses]

            for ar in auto_responses:
                for tr in ar.message_triggers:
                    stored_trigger_map[tr] = ar
            logging.info(
                f"Stored trigger map updated. There are now {len(stored_trigger_map)} values in the map."
            )

        # Ignore messages that start with the bot prefix (.)
        # Could false positive on a chat command otherwise.
        if message.content.startswith(str(self.bot.command_prefix)):
            return

        for key, val in stored_trigger_map.items():
            check_match = resp_parsing.search_message_match(message=message.content, initial_trigger=key)
            if not check_match:
                continue

            # We only ignore on a match since it applies cooldown after checking and not on cooldown.
            user_on_cooldown = self.cooldown.check_for_user(user_id=message.author.id)
            if user_on_cooldown:
                return

            reply_msg = await message.reply(
                content=(
                    f"{val.response_message}\n"
                    "-# This is an automated reply! If this doesn't make sense, please ask for a volunteer!"
                )
            )

            if val.auto_deletion != 0:
                await message.delete(delay=val.auto_deletion)
                await reply_msg.delete(delay=val.auto_deletion)

            break

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
        embed = StandardEmbed(
            title=":BloxlinkHappy: Auto Responder Guide", footer_icon_url=str(ctx.user.display_avatar)
        )

        description = (
            "> Welcome! This guide is going to teach you some of the things to know about the /autoresponder commands.",
            "Firstly, some key information for the slash commands.",
            '- "Message" - This is the response that the bot will send.',
            '- "Trigger" - This is what we call a string that the bot will look for in a user sent message.',
            "- **All triggers are case-insensitive!**",
            "> Further trigger string usage is shown below. If you have more questions, ask Nub for clarification!",
        )
        embed.description = "\n".join(description)

        embed.add_field(
            name="Trigger String special characters:",
            value=(
                f"- `{resp_parsing.SpecialChar.PARTIAL}` - Start and end of string partial matching.\n"
                f"- `{resp_parsing.SpecialChar.EXPAND}` - Matches anything between two strings.\n"
                f"- `{resp_parsing.SpecialChar.SPLIT}` - Splits the single trigger into individual segments that must ALL be found in the message."
                f"- `{resp_parsing.SpecialChar.EXPLICIT}` - The user's message must EXACTLY MATCH this trigger string (excluding this character) (case-insensitive)."
            ),
        )

        embed.add_field(
            name="Trigger String restrictions:",
            value=(
                "Inside a segment...\n"
                f"- `{resp_parsing.SpecialChar.PARTIAL}` and `{resp_parsing.SpecialChar.EXPAND}` CANNOT be used together.\n"
                f"- `{resp_parsing.SpecialChar.EXPAND}` CANNOT be used multiple times."
                f"- `{resp_parsing.SpecialChar.PARTIAL}` works ONLY at the beginning and end. Anywhere else it is treated as a literal `{resp_parsing.SpecialChar.PARTIAL}` character."
                f"- ALL other special characters are **ignored** when `{resp_parsing.SpecialChar.EXPLICIT}` is at the start of the string."
            ),
        )

        embed.add_field(
            name="Trigger String example usage:",
            value=(
                f"- `*verify` - matches anything suffixed by verify\n - `verify*` - matches anything prefixed by verify\n - `*verify*` - matches anything prefixed or suffixed by verify,\n"
                f"- `help ... banned` - matches anything between the words 'help' and 'banned' in a message. Good for requiring words in a specific order.\n"
                f"- `help, ban*` - matches the words 'help' and any word suffixed with 'ban' in a message. Both must be found to match.\n"
                f"- `=help` or `= help` - Message must exactly equal the word 'help'\n"
                f"- `=How do I verify` - Message must exactly equal the phrase 'how do I verify' (case-insensitive)"
            ),
            inline=False,
        )

        await ctx.response.send_message(embed=embed)

    @app_commands.command(name="all", description="View all set automatic responses")
    async def view_all(self, ctx: discord.Interaction):
        auto_responses = await self.bot.db.get_all_autoresponses()
        auto_responses = [AutoResponse.from_database(x) for x in auto_responses]
        auto_responses.sort(key=(lambda y: y.name))

        # Determine max # of pages
        max_pages = math.ceil(len(auto_responses) / MAX_ITEMS_PER_PAGE)
        # Build generic buttons into a view
        view = discord.ui.View(timeout=None)

        left_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=UNICODE_LEFT,
            disabled=True,
            custom_id=f"ar_all:{ctx.user.id}:0:{max_pages}",
        )

        right_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=UNICODE_RIGHT,
            disabled=True if max_pages == 1 else False,
            custom_id=f"ar_all:{ctx.user.id}:1:{max_pages}",
        )

        view.add_item(left_button)
        view.add_item(right_button)

        # Get the embed & send.
        embed = Autoresponder.build_view_page(str(ctx.user.display_avatar), auto_responses, 0)
        await ctx.response.send_message(embed=embed, view=view)

    @staticmethod
    def build_view_page(avatar_url: str, all_items: list[AutoResponse], page_num: int = 0):
        max_pages = math.ceil(len(all_items) / MAX_ITEMS_PER_PAGE)

        # Grab the 10 elements that we care about
        offset = page_num * MAX_ITEMS_PER_PAGE
        selected_items = all_items[offset : offset + MAX_ITEMS_PER_PAGE]

        # Build the embed.
        embed = StandardEmbed(title="All Auto Responders")

        trigger_strings = []
        for ar in selected_items:
            message_triggers = [f"`{discord.utils.escape_markdown(tr)}`" for tr in ar.message_triggers]
            message_tr_str = ", ".join(message_triggers)

            trigger_strings.append(f"- {ar.name} {UNICODE_RIGHT_ALT} \n\t{message_tr_str}")
        embed.description = f"> ***<Responder Name> {UNICODE_RIGHT_ALT} <Trigger Strings>***\n" + "\n".join(
            trigger_strings
        )

        # footer
        embed.set_footer(text=f"Page {page_num + 1}/{max_pages}", icon_url=avatar_url)

        # return the entire embed
        return embed

    @bot_instance.register_button_handler("ar_all")
    @staticmethod
    async def view_all_button_handler(ctx: discord.Interaction):
        # We already know data is a valid entity by this point, typing system doesn't know that though
        data = MessageComponentData(**ctx.data)  # pyright: ignore[reportCallIssue]

        custom_id_data = data.custom_id.split(":")
        custom_id_data.pop(0)
        original_author_id = custom_id_data[0]
        new_page_index = int(custom_id_data[1])
        max_pages = int(custom_id_data[2])

        if not ctx.message:
            logging.error("Execution failed in view_all_button_handler because there's no message.")
            return

        # Disable after 5 mins.
        if (datetime.now(timezone.utc) - ctx.message.created_at).seconds > 300:
            view = discord.ui.View.from_message(ctx.message)
            view.children
            for x in view.children:
                # Ignored because this is how d.py says to do it.
                x.disabled = True  # pyright: ignore[reportAttributeAccessIssue]

            return await ctx.response.edit_message(
                content="-# This prompt was disabled because 5 minutes have passed since its creation.",
                view=view,
            )

        # Require person who ran the command
        if str(ctx.user.id) != original_author_id:
            return await ctx.response.send_message(
                f"You're not allowed to flip through this embed!", ephemeral=True
            )

        prev_page_index = 0 if new_page_index - 1 < 0 else new_page_index - 1
        next_page_index = max_pages if new_page_index + 1 >= max_pages else new_page_index + 1

        view = discord.ui.View()
        left_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=UNICODE_LEFT,
            disabled=True if prev_page_index <= 0 and new_page_index != 1 else False,
            custom_id=f"ar_all:{ctx.user.id}:{prev_page_index}:{max_pages}",
        )

        right_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=UNICODE_RIGHT,
            disabled=True if next_page_index == max_pages else False,
            custom_id=f"ar_all:{ctx.user.id}:{next_page_index}:{max_pages}",
        )

        view.add_item(left_button)
        view.add_item(right_button)

        auto_responses = await bot_instance.db.get_all_autoresponses()
        auto_responses = [AutoResponse.from_database(x) for x in auto_responses]
        auto_responses.sort(key=(lambda y: y.name))

        embed = Autoresponder.build_view_page(str(ctx.user.display_avatar), auto_responses, new_page_index)
        await ctx.response.edit_message(embed=embed, view=view)

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

        # Intentionally not using an embed so that way it's easier for people to copy.
        return await ctx.response.send_message(
            f"### Raw Message Content for `{ar.name}`\n{discord.utils.escape_markdown(ar.response_message)}"
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
            embed = ErrorEmbed(title=":BloxlinkDead: Invalid Trigger String")
            embed.add_field(name="Error", value=str(err))
            embed.add_field(name="Trigger string", value=trigger)
            return await ctx.response.send_message(embed=embed)

        ar = AutoResponse.from_database(responder)
        if trigger in ar.message_triggers:
            return await ctx.response.send_message(
                f"No changes were made, that trigger string is already set!", ephemeral=True
            )

        ar.message_triggers.append(trigger)
        await self.bot.db.update_autoresponse(name=name, message_triggers=ar.message_triggers)
        stored_trigger_map.clear()

        embed = StandardEmbed(footer_icon_url=str(ctx.user.display_avatar))
        embed.title = f":BloxlinkHappy: Success! Auto responder `{name}` has been updated."
        embed.add_field(name="New Trigger:", value=trigger)
        embed.add_field(name="Response:", value=ar.codeblock_response_msg)
        await ctx.response.send_message(embed=embed)

    @trigger_group.command(name="delete", description="Remove a message string that is responded to.")
    @app_commands.autocomplete(name=name_autofill)
    @app_commands.describe(
        name="The admin-facing name for the responder",
        trigger="Optionally directly say what trigger string to remove. Must exactly match.",
    )
    async def trigger_del(self, ctx: discord.Interaction, name: str, trigger: Optional[str]):
        responder = await self.bot.db.get_autoresponse(name=name)
        if responder is None:
            return await ctx.response.send_message(
                f"No auto response with the name `{name}` exists!", ephemeral=True
            )

        ar = AutoResponse.from_database(responder)
        if len(ar.message_triggers) == 1:
            return await ctx.response.send_message(
                f"Error! There is only one trigger for this auto responder. There must be at least one string to reply to!",
                ephemeral=True,
            )

        if trigger:
            if trigger not in ar.message_triggers:
                return await ctx.response.send_message(
                    f"Error! Could not find the trigger {trigger} for the auto responder {name}.",
                    ephemeral=True,
                )

            ar.message_triggers.remove(trigger)
            await self.bot.db.update_autoresponse(name=name, message_triggers=ar.message_triggers)
            stored_trigger_map.clear()

            embed = StandardEmbed(footer_icon_url=str(ctx.user.display_avatar))
            embed.title = f":BloxlinkHappy: Success! Auto responder `{name}` has been updated."
            embed.add_field(name="Trigger Removed:", value=trigger)
            embed.add_field(name="From Response:", value=ar.codeblock_response_msg)
            return await ctx.response.send_message(embed=embed)

        options = [discord.SelectOption(label=tr[:99], value=tr[:99]) for tr in ar.message_triggers[:25]]
        select_menu = discord.ui.Select(
            custom_id=f"tr-del:{ctx.user.id}:{name}", min_values=0, max_values=len(options), options=options
        )
        view = discord.ui.View(timeout=None)
        view.add_item(select_menu)

        await ctx.response.send_message(content="Select a trigger to remove!", view=view)

    @bot_instance.register_select_menu_handler("tr-del")
    @staticmethod
    async def trigger_del_select_menu(ctx: discord.Interaction):
        # We already know data is a valid entity by this point, typing system doesn't know that though
        data = MessageComponentData(**ctx.data)  # pyright: ignore[reportCallIssue]

        custom_id_data = data.custom_id.split(":")
        custom_id_data.pop(0)
        original_author_id = custom_id_data[0]
        responder_name = custom_id_data[1]

        if not ctx.message:
            # python pls give me a null aware operator.
            logging.error("Execution failed in trigger_del_select_menu because there's no message.")
            return

        # Disable after 5 mins.
        if (datetime.now(timezone.utc) - ctx.message.created_at).seconds > 300:
            return await ctx.response.edit_message(
                content="-# This prompt was disabled because 5 minutes have passed since its creation.",
                view=None,
            )

        # Require person who ran the command
        if str(ctx.user.id) != original_author_id:
            return await ctx.response.send_message(
                f"You're not allowed to edit this select menu.", ephemeral=True
            )

        # I wish we could pass along data here without getting the full object from the db again... but this
        # is acting stateless so we can't (easily)
        responder = await bot_instance.db.get_autoresponse(name=responder_name)
        if not responder:
            return await ctx.response.send_message(
                f"There was an issue getting that responder (`{responder_name}`) from the DB.", ephemeral=True
            )

        # Require >1 trigger string to allow deletions. redundant? maybe.
        ar = AutoResponse.from_database(responder)
        if len(ar.message_triggers) == 1:
            return await ctx.response.send_message(
                f"Error! There is only one trigger for this auto responder. There must be at least one string to reply to!",
                ephemeral=True,
            )

        selections = data.values
        if not selections:
            return await ctx.response.send_message(f"Error! No selections were found.", ephemeral=True)

        if len(selections) == len(ar.message_triggers):
            return await ctx.response.send_message(
                f"Error! You can't remove all of the trigger strings.", ephemeral=True
            )

        # figure out which strings will be kept. values might be truncated (if for some reason we have a trigger
        # over 100 characters long).
        major_output = []
        for sel in selections:
            output = set()
            for items in ar.message_triggers:
                if not items.startswith(sel):
                    output.add(items)
            major_output.append(output)

        major_output = list(set.intersection(*major_output))
        await bot_instance.db.update_autoresponse(name=responder_name, message_triggers=major_output)

        formatted_selections = [f"- `{x}`" for x in selections]
        output_str = "\n".join(formatted_selections)

        embed = StandardEmbed(footer_icon_url=str(ctx.user.display_avatar))
        embed.title = f":BloxlinkHappy: Success! Auto responder `{responder_name}` has been updated."
        embed.add_field(name="Removed Triggers:", value=output_str)
        embed.add_field(name="From Response:", value=ar.codeblock_response_msg)

        return await ctx.response.edit_message(content="", embed=embed, view=None)

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
        stored_trigger_map.clear()

        response = (
            "Message and reply do not auto delete after responding."
            if duration == 0
            else f"Message and reply will now delete after {duration} seconds."
        )
        embed = StandardEmbed(footer_icon_url=str(ctx.user.display_avatar))
        embed.title = f":BloxlinkHappy: Success! Auto responder `{name}` has been updated."
        embed.add_field(name="Changes:", value=response)
        await ctx.response.send_message(embed=embed)


async def setup(bot: HelperBot):
    await bot.add_cog(Autoresponder(bot))
