import asyncio
import math
from datetime import datetime, timedelta

import discord
from discord import app_commands, ui
from discord.ext.commands import (
    CheckFailure,
    CommandError,
    CommandInvokeError,
    Context,
    MissingRequiredArgument,
    check,
)
from textdistance import Sorensen

from resources.checks import is_staff, is_staff_or_trial
from resources.constants import (
    ADMIN_ROLES,
    BLOXLINK_GUILD,
    BLOXLINK_HAPPY,
    BLURPLE,
    TAG_METRIC_IGNORE_CHANNELS,
    TRIAL_ROLE,
    UNICODE_LEFT,
    UNICODE_RIGHT,
)
from resources.exceptions import HelperError
from resources.helper_bot import instance as bot

MAX_TAGS_PER_PAGE = 20

# ------------ TAG AUTOCOMPLETE HANDLERS ------------


async def tag_name_autocomplete(interaction: discord.Interaction, user_input: str):
    tags = await bot.db.get_all_tags()
    valid_names = []
    for tag in tags:
        valid_names.append(tag["_id"])
        valid_names.extend(tag.get("aliases", []))

    if user_input == "":
        return [app_commands.Choice(name=name, value=name) for name in valid_names][:25]

    valid_names = [
        item for item in valid_names if Sorensen().similarity(user_input, item) > 0.65 or user_input in item
    ]
    return [app_commands.Choice(name=name, value=name) for name in valid_names][:25]


async def tag_alias_autocomplete(interaction: discord.Interaction, user_input: str):
    tags = await bot.db.get_all_tags()
    valid_names = []
    for tag in tags:
        valid_names.extend(tag.get("aliases", []))

    if user_input == "":
        return [app_commands.Choice(name=name, value=name) for name in valid_names][:25]

    valid_names = [
        item for item in valid_names if Sorensen().similarity(user_input, item) > 0.65 or user_input in item
    ]
    return [app_commands.Choice(name=name, value=name) for name in valid_names][:25]


# ------------ TAG COMMANDS ------------


@bot.hybrid_group("tag", description="Send a tag to this channel!", fallback="send")
@app_commands.guild_only()
@app_commands.autocomplete(name=tag_name_autocomplete)
async def tag_base(ctx: Context, name: str, *, message: str = "0"):
    if not ctx.guild:
        return

    ## if name is empty, raise error
    if name == "0":
        raise HelperError("You forgot the tag name!")

    tag = await bot.db.get_tag(name)
    if tag is None:
        raise HelperError(f'The tag "{name}" was not found!')

    if ctx.interaction is None:
        await ctx.message.delete()

    allowed_mentions = discord.AllowedMentions(roles=False, users=True, everyone=False)

    if message != "0" and ctx.interaction is None:
        msg = await ctx.send(
            tag["content"],
            allowed_mentions=allowed_mentions,
            reference=ctx.message.reference,  # type: ignore
        )  # type: ignore
        await msg.edit(
            content=f"{message} {tag['content']}",
            allowed_mentions=allowed_mentions,
        )

    elif message != "0" and ctx.interaction is not None:
        await ctx.send(f"{message} {tag['content']}", allowed_mentions=allowed_mentions)

    else:
        await ctx.send(
            tag["content"],
            allowed_mentions=allowed_mentions,
            reference=ctx.message.reference,  # type: ignore
        )  # type: ignore

    await bot.db.update_tag(
        tag["_id"],
        use_count=tag["use_count"] + 1,
    )

    # Update staff metrics - only when used in a valid channel in bloxlink guild.
    # TODO: Move this to its own method somewhere to be called instead of this copy pasted code.
    if ctx.guild.id != BLOXLINK_GUILD or ctx.message.channel.id in TAG_METRIC_IGNORE_CHANNELS:
        return

    author_roles = set([role.id for role in ctx.author.roles])  # type: ignore
    staff_roles = set(ADMIN_ROLES.values())
    if TRIAL_ROLE in author_roles:
        await bot.db.update_staff_metric(str(ctx.author.id), "trial", incr_tags=True)
    elif author_roles.intersection(staff_roles):
        await bot.db.update_staff_metric(str(ctx.author.id), "volunteer", incr_tags=True)


@tag_base.command("add", description="Add a tag to the tag list.", aliases=["create"])
@check(is_staff)
async def add_tag(ctx: Context, tag_name: str = "⅋", *, tag_content: str = "⅋"):
    ## if name or content is empty, raise error
    if tag_name == "⅋" or tag_content == "⅋":
        raise HelperError("Please provide both tag name and tag content.")

    if len(tag_content) > 2000:
        raise HelperError("Tag content exceeds maximum length.")

    check_tag = await bot.db.get_tag(tag_name)
    if check_tag is not None:
        raise HelperError("Tag already exists.")

    tag_content = "\n".join(tag_content.split("\\n"))

    await bot.db.update_tag(
        tag_name,
        tag_content,
        aliases=None,
        author=str(ctx.author.id),
        use_count=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    await ctx.send(f"Tag `{tag_name}` has been added.")
    ## add the tag to db


@tag_base.command("edit", description="Edit a current tag in the list.")
@app_commands.autocomplete(tag_name=tag_name_autocomplete)
@check(is_staff)
async def edit_tag(ctx: Context, tag_name: str = "⅋", *, tag_content: str = "⅋"):
    ## if name or content is empty, raise error
    if tag_name == "⅋" or tag_content == "⅋":
        raise HelperError("Please provide both tag name and tag content.")

    if len(tag_content) > 2000:
        raise HelperError("Tag content exceeds maximum length.")

    check_tag = await bot.db.get_tag(tag_name)
    if check_tag is None:
        raise HelperError("Tag does not exist. Please create the tag with `tag add` instead.")

    tag_content = "\n".join(tag_content.split("\\n"))

    await bot.db.update_tag(
        tag_name,
        content=tag_content,
        author=str(ctx.author.id),
        updated_at=datetime.now(),
    )

    await ctx.send(f"Tag `{tag_name}` has been edited.")
    ## add the tag to db


@tag_base.command("delete", description="Remove a tag from the tag list.")
@app_commands.autocomplete(name=tag_name_autocomplete)
@check(is_staff)
async def delete_tag(ctx: Context, name: str = "0"):
    ## if name is empty, raise error
    if name == "0":
        raise HelperError("You forgot the tag name!")

    ## delete the tag
    if await bot.db.get_tag(name) is not None:
        await bot.db.delete_tag(name)
        await ctx.send("Tag has been deleted.")
    ## if no tag found, raise error
    else:
        raise HelperError("Tag was not found.")


@tag_base.command("info", description="Information about a tag.")
@app_commands.autocomplete(name=tag_name_autocomplete)
@check(is_staff_or_trial)
async def tag_info(ctx: Context, name: str = "0"):
    ## if name is empty, raise error
    if name == "0":
        raise HelperError("You forgot the tag name!")

    ## delete the tag
    tag = await bot.db.get_tag(name)
    if tag is None:
        raise HelperError(f'The tag "{name}" was not found!')

    tag_content = tag["content"]
    tag_author = tag["author"]
    tag_use_count = tag["use_count"]
    tag_created_at = tag["created_at"]
    tag_updated_at = datetime.fromisoformat(tag.get("updated_at", tag_created_at))

    embed = discord.Embed(
        title=f"{BLOXLINK_HAPPY} Tag Info: {tag['_id']}",
        description=f"**Content:** \n```{tag_content}```",
        color=BLURPLE,
    )
    embed.add_field(name="Author", value=f"<@{tag_author}> ({tag_author})", inline=True)
    embed.add_field(name="Use Count", value=tag_use_count, inline=True)
    embed.add_field(name="Created At", value=tag_created_at, inline=True)
    embed.add_field(name="Updated At", value=tag_updated_at.date(), inline=True)

    aliases = tag.get("aliases", [])
    if len(aliases) > 0:
        embed.add_field(name="Aliases", value=", ".join(aliases), inline=False)

    embed.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)
    embed.timestamp = datetime.now()
    await ctx.reply(embed=embed, mention_author=False)


@tag_base.command("all", description="View all the tags in the tag list.")
async def view_tag(ctx: Context):
    # Get tags from the db, get their names, then sort alphabetically
    tag_list = await bot.db.get_all_tags()
    tag_names = [tag["_id"] for tag in tag_list]
    tag_names.sort(reverse=False)

    # Determine max # of pages
    max_pages = math.ceil(len(tag_names) / MAX_TAGS_PER_PAGE)

    # Build generic buttons into a view
    view = ui.View(timeout=None)

    left_button = ui.Button(
        style=discord.ButtonStyle.secondary,
        label=UNICODE_LEFT,
        disabled=True,
        custom_id=f"tag_all:{ctx.author.id}:0:{max_pages}",
    )

    right_button = ui.Button(
        style=discord.ButtonStyle.secondary,
        label=UNICODE_RIGHT,
        disabled=True if max_pages == 1 else False,
        custom_id=f"tag_all:{ctx.author.id}:1:{max_pages}",
    )

    view.add_item(left_button)
    view.add_item(right_button)

    # Get the embed & send.
    embed = await build_page(ctx.author.display_avatar.url, tag_names, 0)
    await ctx.reply(embed=embed, view=view)


# ------------ TAG ALIAS ------------


@tag_base.group("alias", description="Modify aliases for a tag.")
@check(is_staff)
async def alias_base(ctx: Context):
    raise HelperError(
        "You need to run `.tag alias add` or `.tag alias delete`! Or use the slash command instead."
    )


@alias_base.command("add", description="Add an alias to a tag.")
@app_commands.autocomplete(tag=tag_name_autocomplete)
@check(is_staff)
async def alias_add(ctx: Context, tag: str, alias: str):
    # Check to make sure the tag exists.
    matching_tag = await bot.db.get_tag(tag)
    if not matching_tag:
        raise HelperError(f'The tag "{tag}" does not exist, so you can\'t add an alias to it!')

    # Make sure this alias isn't a duplicate with another tag.
    matching_alias = await bot.db.get_tag(alias)
    if matching_alias:
        raise HelperError(f"That alias already exists for the tag {matching_alias['_id']}!")

    # Make sure this alias isn't a duplicate within the same command.
    # Really this is covered by the previous check, so it shouldn't be necessary.
    aliases: list = matching_tag.get("aliases", [])
    if (alias in aliases) or alias.lower() == matching_tag["_id"].lower():
        raise HelperError(f"You can't add the alias \"{alias}\" to the tag {matching_tag['_id']}.")

    if len(alias) > 32:
        raise HelperError("The alias you are adding is too long. Keep it under 32 characters!")

    aliases.append(alias.lower())
    await bot.db.update_tag(
        tag,
        aliases=aliases,
        updated_at=datetime.now(),
    )

    return await ctx.reply(
        f"The alias `{alias}` has been added to the tag `{matching_tag['_id']}`",
        mention_author=False,
    )


@alias_base.command("delete", description="Remove an alias.")
@app_commands.autocomplete(alias=tag_alias_autocomplete)
@check(is_staff)
async def alias_delete(ctx: Context, alias: str):
    # Check to see if the alias actually exists.
    matching_tag = await bot.db.get_tag(alias)
    if not matching_tag:
        raise HelperError(f'The alias "{alias}" does not exist, so you can\'t delete it!')

    # We can't delete tag names from the alias command.
    if matching_tag["_id"].lower() == alias.lower():
        raise HelperError("That was the tag name, not an alias for the tag. You can't delete that from here!")

    aliases: list = matching_tag["aliases"]
    aliases.remove(alias.lower())

    await bot.db.update_tag(
        matching_tag["_id"],
        aliases=aliases,
        updated_at=datetime.now(),
    )

    return await ctx.reply(
        f"The alias \"{alias}\" was removed from the tag {matching_tag['_id']}",
        mention_author=False,
    )


@alias_add.error
@alias_delete.error
async def alias_command_errors(ctx: Context, error: CommandError):
    match error:
        case CheckFailure():
            await ctx.reply(
                content="You do not have permissions to use this command!",
                mention_author=False,
                delete_after=5.0,
                ephemeral=True,
            )

            if not ctx.interaction:
                await asyncio.sleep(5)
                await ctx.message.delete()

        case MissingRequiredArgument():
            param = error.param.name
            message = f"You're missing the required {param} argument!"

            if param == "tag":
                message = "You need to give the command a tag name!"
            elif param == "alias":
                message = "You need to give the command the name of an alias!"

            await ctx.reply(
                content=message,
                mention_author=False,
                delete_after=5.0,
                ephemeral=True,
            )

            if not ctx.interaction:
                await asyncio.sleep(5)
                await ctx.message.delete()

        case CommandInvokeError():
            if isinstance(error.original, HelperError):
                return

            await ctx.reply(
                content=str(error),
                mention_author=False,
                delete_after=5.0,
                ephemeral=True,
            )  # type: ignore

            if not ctx.interaction:
                await asyncio.sleep(5)
                await ctx.message.delete()


# ------------ INTERACTION HANDLERS/UTILITY FUNCTIONS FOR TAG COMMANDS ------------


@bot.register_button_handler("tag_all")
async def view_tag_buttons(interaction: discord.Interaction):
    custom_id = interaction.data["custom_id"]  # type: ignore
    custom_data = custom_id.split(":")

    # Remove tag_all text
    custom_data.pop(0)

    # Get all other useful info from the custom id
    author_id = custom_data[0]
    new_page = int(custom_data[1])
    max_pages = int(custom_data[2])

    # Only listen to the author of the command
    if str(author_id) != str(interaction.user.id):
        await interaction.response.send_message("You can't flip pages on this embed!", ephemeral=True)
        return

    if interaction.message is None:
        # discord giving us a ghost interaction apparently
        return

    # Get the timezone so python doesn't complain
    tz = interaction.message.created_at.tzinfo

    # If it's been over 3 minutes since the prompt was activated.
    if datetime.now(tz) - timedelta(minutes=3) > interaction.message.created_at:
        # Get rid of the buttons
        view = ui.View(timeout=None)
        await interaction.response.edit_message(embeds=interaction.message.embeds, view=view)
        return

    # Build the buttons again
    view = ui.View(timeout=180)

    # Recalculate the next and prev page indexes
    prev_page = 0 if new_page - 1 < 0 else new_page - 1
    next_page = max_pages if new_page + 1 >= max_pages else new_page + 1

    left_button = ui.Button(
        style=discord.ButtonStyle.secondary,
        label=UNICODE_LEFT,
        disabled=True if prev_page <= 0 and new_page != 1 else False,
        custom_id=f"tag_all:{author_id}:{prev_page}:{max_pages}",
    )

    right_button = ui.Button(
        style=discord.ButtonStyle.secondary,
        label=UNICODE_RIGHT,
        disabled=True if next_page == max_pages else False,
        custom_id=f"tag_all:{author_id}:{next_page}:{max_pages}",
    )

    view.add_item(left_button)
    view.add_item(right_button)

    # Get tags from the db, get their names, then sort alphabetically
    tag_list = await bot.db.get_all_tags()
    tag_names = [tag["_id"] for tag in tag_list]
    tag_names.sort(reverse=False)

    new_page = await build_page(interaction.user.display_avatar.url, tag_names, new_page)
    await interaction.response.edit_message(embed=new_page, view=view)


async def build_page(avatar_url: str, items: list[str], page_num: int = 0):
    max_pages = math.ceil(len(items) / MAX_TAGS_PER_PAGE)

    # Grab the 20 elements that we care about
    offset = page_num * MAX_TAGS_PER_PAGE
    tag_names = items[offset : offset + MAX_TAGS_PER_PAGE]

    # Build the embed.
    embed_tags = discord.Embed(
        title="All Tags",
        description="----------",
        color=0x7289DA,
    )

    # Tags will be added to either of these
    field_one = []
    field_two = []

    for index, tag in enumerate(tag_names):
        if index < 10:
            field_one.append(tag)
        else:
            field_two.append(tag)

    # Convert the lists above to strings
    embed_tags.add_field(name="", value="\n".join(field_one), inline=True)
    embed_tags.add_field(name="", value="\n".join(field_two), inline=True)

    # footer
    embed_tags.set_footer(text=f"Page {page_num + 1}/{max_pages}", icon_url=avatar_url)

    # return the entire embed
    return embed_tags


async def setup(bot): ...
