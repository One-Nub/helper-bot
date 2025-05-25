import traceback
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands

from resources.constants import BLOXLINK_DETECTIVE, BLURPLE
from resources.helper_bot import instance as bot

INFO_URL = "https://groups.roblox.com/v1/groups/{0}"


class GroupIDConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        """Converts a user's argument input into a valid group ID.

        Acceptable input is a Roblox group URL, or any integer input.
        Input that is not accepted will raise a BadArgument exception.
        """
        int_output = None

        try:
            int_output = int(argument)
        except ValueError:
            pass
        else:
            return int_output

        if "/groups/" in argument:
            # Roblox URL, grab the ID.
            split = argument.split("/groups/")
            split_two = split[1].split("/", maxsplit=1)
            int_output = split_two[0]

        elif "/communities/" in argument:
            # Roblox URL, grab the ID.
            split = argument.split("/communities/")
            split_two = split[1].split("/", maxsplit=1)
            int_output = split_two[0]

        if int_output is None:
            raise commands.BadArgument()
        else:
            return int_output


@bot.hybrid_command(
    "groupapi",
    description="Get info about a Roblox group!",
    aliases=["gapi"],
)
@discord.app_commands.describe(group="The group ID or group URL you are looking up.")
async def groupapi(ctx: commands.Context, group: GroupIDConverter):
    # Query Roblox for group data.
    info_data: dict | None = None
    rank_data: dict | None = None
    thumbnail_data: dict | None = None

    info_url = INFO_URL.format(group)

    async with bot.aiohttp.get(info_url) as info_req:
        info_data = await info_req.json()
    async with bot.aiohttp.get(f"{info_url}/roles") as rank_req:
        rank_data = await rank_req.json()

    # Get group icon.
    async with bot.aiohttp.get(
        "https://thumbnails.roblox.com/v1/groups/icons",
        params={
            "groupIds": [group],
            "size": "420x420",
            "format": "Png",
            "isCircular": "false",
        },  # type: ignore
    ) as req:
        thumbnail_data = await req.json()

    desc_builder = []
    name = "Invalid group."
    members = 0
    owner = "N/A"

    embed = discord.Embed(
        color=BLURPLE,
        timestamp=datetime.now(),
        title=f"{BLOXLINK_DETECTIVE} Roblox Group Lookup",
    )

    # Build basic group info content
    if info_data:
        name = info_data.get("name", name)
        members = info_data.get("memberCount", 0)

        owner_data = info_data.get("owner", {})
        if owner_data:
            owner = owner_data.get("username", owner)

    desc_builder.append(f"> **Name:** {name}")
    desc_builder.append(f"> **Owner:** {owner}")
    desc_builder.append(f"> **Member Count:** {members}")
    desc_builder.append(" ")

    # Build rank data fields
    if rank_data:
        field_one = []
        field_two = []

        desc_builder.append(f"**Group Ranks:**")

        ranks = rank_data.get("roles", [])
        rank_count = len(ranks)
        for i, rank in enumerate(ranks):
            rank_name = rank.get("name", "Invalid Name")
            rank_id = rank.get("rank", -1)

            if i < (rank_count / 2):
                field_one.append(f"`{rank_id:<3d}`: {rank_name}")
            else:
                field_two.append(f"`{rank_id:<3d}`: {rank_name}")

        embed.add_field(name="", value="\n".join(field_one), inline=True)
        embed.add_field(name="", value="\n".join(field_two), inline=True)

    # Set thumbnail of embed.
    if thumbnail_data is not None:
        thumbnail_data = thumbnail_data.get("data", [])
        # Empty array is given for invalid IDs.
        if thumbnail_data:
            embed.set_thumbnail(url=thumbnail_data[0]["imageUrl"])

    embed.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)
    embed.description = "\n".join(desc_builder)

    # Add button linking to the group page.
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="Group Page",
            url=f"https://www.roblox.com/groups/{group}",
        )
    )

    await ctx.reply(embed=embed, view=view, mention_author=False)


@groupapi.error
async def groupapi_error(ctx: commands.Context, error: commands.CommandError):
    """Handle exceptions raised by the /groupapi command."""
    message = None

    match error:
        case commands.MissingRequiredArgument():
            message = "You need to a give a group ID to look up!"

        case commands.BadArgument():
            message = "That wasn't a valid group ID!"

        case _:
            message = (
                f"An unhandled exception was caught! ```{type(error)}: {error}"
                f"\n\n{traceback.format_exc()}```"
            )

    await ctx.reply(content=message[:2000], ephemeral=True, mention_author=False)
