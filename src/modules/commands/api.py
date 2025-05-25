from datetime import datetime

import discord
import requests
from discord.ext.commands import Context, check

from resources.checks import is_hr, is_staff_or_trial
from resources.constants import BLOXLINK_DEAD, BLOXLINK_GUILD, BLURPLE, RED, TEAM_CENTER_GUILD
from resources.exceptions import HelperError
from resources.helper_bot import instance as bot
from resources.secrets import BLOXLINK_API_KEY  # pyright: ignore[reportAttributeAccessIssue]


@bot.command("api", description="Fetch information via Bloxlink API.")
@check(is_staff_or_trial)
async def api(ctx: Context, lookup_id: int = 0):
    """Fetch information from the Bloxlink API!"""
    if not ctx.guild:
        raise HelperError("This command can only be used in a server!")

    if ctx.guild.id != BLOXLINK_GUILD:
        check_hr = await is_hr(ctx)
        if not check_hr:
            raise HelperError("This command can only be used in the Bloxlink HQ Server!")

        if ctx.guild.id != TEAM_CENTER_GUILD:
            raise HelperError("This command can only be used in Bloxlink related guilds!")

    if lookup_id == 0:
        raise HelperError("Missing argument `id`. Please provide a valid Discord ID.")

    if len(str(lookup_id)) < 17:
        raise HelperError("Invalid Argument `id`. Please provide a valid Discord ID.")

    response_embed, response_buttons = await api_request_handler(lookup_id)
    response_embed.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)

    await ctx.reply(embed=response_embed, mention_author=False, view=response_buttons)


@discord.app_commands.context_menu(name="Bloxlink API Lookup")
async def api_menu(interaction: discord.Interaction, user: discord.Member):
    if interaction.guild_id != BLOXLINK_GUILD:
        await interaction.response.send_message(
            content="This context menu only works in Bloxlink HQ!",
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions(users=False),
        )
        return

    allowed_to_run = await is_staff_or_trial(interaction)
    if not allowed_to_run:
        await interaction.response.send_message(
            content="You are not allowed to use this context menu!",
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions(users=False),
        )
        return

    response_embed, response_buttons = await api_request_handler(user.id)
    response_embed.set_footer(text="Bloxlink Helper", icon_url=interaction.user.display_avatar)

    await interaction.response.send_message(
        embed=response_embed,
        view=response_buttons,
        ephemeral=True,
        allowed_mentions=discord.AllowedMentions(users=False),
    )


async def api_request_handler(user_id: int) -> tuple:
    url = f"https://api.blox.link/v4/public/discord-to-roblox/{user_id}"

    embed = discord.Embed()
    embed.timestamp = datetime.now()
    embed.color = BLURPLE

    async with bot.aiohttp.get(url, headers={"Authorization": BLOXLINK_API_KEY}) as api_req:
        response = await api_req.json()

    # TODO: Bring back handling/catching?

    if response.get("resolved") is not None:
        del response["resolved"]

    embed.title = "Success"
    embed.description = f"Sent a request to {url}.\n\n**Response**\n```json\n{response}```"

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="Roblox Profile",
            url=f"https://roblox.com/users/{response.get('robloxID', 0)}/profile",
        )
    )

    return (embed, view)


bot.tree.add_command(api_menu)
