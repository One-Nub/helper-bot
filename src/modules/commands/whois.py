import traceback
from datetime import datetime

import discord
from discord.ext import commands

from resources.constants import BLURPLE
from resources.helper_bot import instance as bot


@bot.hybrid_command(
    "whois",
    description="Get info about a discord user!",
    aliases=["w"],
)
@discord.app_commands.guild_only()
@discord.app_commands.describe(user="The user you are trying to find info for.")
async def whois(ctx: commands.Context, user: discord.User):
    if not ctx.guild:
        return await ctx.reply("This command only works in servers.")

    try:
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)
    except (discord.HTTPException, discord.NotFound):
        member = None

    embed = discord.Embed(
        color=BLURPLE,
        timestamp=datetime.now(),
    )

    name = f"@{user.name}" if user.discriminator == 0 else f"{user.name}#{user.discriminator}"
    embed.set_author(name=f"{user.global_name} ({name})", icon_url=user.avatar)
    embed.set_thumbnail(url=user.avatar)

    embed.description = f"{user.mention}"
    if member:
        embed.description += f"\n**Nickname**: {member.nick}"
    if not member:
        embed.description += "\n*User is not a member of this server!*"

    embed.add_field(
        name="Registered",
        value=f"<t:{int(user.created_at.timestamp())}:R> (<t:{int(user.created_at.timestamp())}>)",
        inline=True,
    )
    if member:
        embed.add_field(
            name="Joined",
            value=f"<t:{int(member.joined_at.timestamp())}:R> (<t:{int(member.joined_at.timestamp())}>)",  # type: ignore
            inline=True,
        )
        embed.add_field(name="Roles", value=", ".join([role.mention for role in member.roles]))

    embed.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)

    await ctx.reply(embed=embed, mention_author=False)


@whois.error
async def whois_error(ctx: commands.Context, error: commands.CommandError):
    """Handle exceptions raised by the /groupapi command."""
    message = None

    match error:
        case commands.MissingRequiredArgument():
            message = "You need to a give a user ID to look up!"

        case commands.BadArgument():
            message = "That wasn't a valid user ID!"

        case _:
            message = (
                f"An unhandled exception was caught! ```{type(error)}: {error}"
                f"\n\n{traceback.format_exc()}```"
            )

    await ctx.reply(content=message[:2000], ephemeral=True, mention_author=False)


async def setup(bot): ...
