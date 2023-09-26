import math
from datetime import datetime, timedelta

import discord
from discord import ui
from discord.ext.commands import Context

from constants import UNICODE_LEFT, UNICODE_RIGHT
from helper_bot import instance as bot


@bot.hybrid_group("tag", description="Send a tag to this channel!", fallback="send")
async def tag(ctx: Context, name: str = "0", *, message: str = "0"):
    try:
        ## if name is empty, raise error
        if name == "0":
            raise Exception("You forgot the tag name!")

        tag = await bot.db.get_tag(name)
        if tag is None:
            raise Exception("Tag was not found.")

        if ctx.interaction == None:
            await ctx.message.delete()

        allowed_mentions = discord.AllowedMentions(roles=False, users=True, everyone=False)

        if message == "0":
            message = ""

        msg = await ctx.send(
            f"{message} {tag['content']}",
            allowed_mentions=allowed_mentions,
            reference=ctx.message.reference,
        )

    ## send the error message
    except Exception as Error:
        await ctx.send(
            Error,
            delete_after=3.0 if ctx.message else None,
            reference=ctx.message if ctx.message else None,
            silent=True,
        )

        if ctx.interaction == None:
            await ctx.message.delete()


@tag.command("add", description="Add a tag to the tag list.")
async def add_tag(ctx: Context, tag_name: str = "⅋", *, tag_content: str = "⅋"):
    try:
        ## if name or content is empty, raise error
        if tag_name == "⅋" or tag_content == "⅋":
            raise Exception("Please provide both tag name and tag content.")

        if tag_content.__len__() > 2000:
            raise Exception("Tag content exceeds maximum length.")

        else:
            check_tag = await bot.db.get_tag(tag_name)
            if check_tag != None:
                raise Exception("Tag already exists.")

            await bot.db.update_tag(
                tag_name,
                tag_content,
                aliases=None,
                author=ctx.author.id,
                use_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            await ctx.send(f"Tag `{tag_name}` has been added.")
        ## add the tag to db

    ## send the error message
    except Exception as Error:
        await ctx.send(Error)


@tag.command("delete", description="Remove a tag from the tag list.")
async def delete_tag(ctx: Context, name: str = "0"):
    try:
        ## if name is empty, raise error
        if name == "0":
            raise Exception("You forgot the tag name!")

        ## delete the tag
        if await bot.db.get_tag(name) != None:
            await bot.db.delete_tag(name)
            await ctx.send("Tag has been deleted.")
        ## if no tag found, raise error
        else:
            raise Exception("Tag was not found.")

    ## send the error message
    except Exception as Error:
        await ctx.send(Error)


## tags command

MAX_PER_PAGE = 20


@tag.command("all", description="View all the tags in the tag list.")
async def view_tag(ctx: Context):
    # Get tags from the db, get their names, then sort alphabetically
    tag_list = await bot.db.get_all_tags()
    tag_names = [tag["_id"] for tag in tag_list]
    tag_names.sort(reverse=False)

    # Determine max # of pages
    max_pages = math.ceil(len(tag_names) / MAX_PER_PAGE)

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
    embed = await build_page(ctx.author.display_avatar, tag_names, 0)
    await ctx.reply(embed=embed, view=view)


@bot.register_button_handler("tag_all")
async def view_tag_buttons(interaction: discord.Interaction):
    custom_id = interaction.data["custom_id"]
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
    max_pages = math.ceil(len(items) / MAX_PER_PAGE)

    # Grab the 20 elements that we care about
    offset = page_num * MAX_PER_PAGE
    tag_names = items[offset : offset + MAX_PER_PAGE]

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
