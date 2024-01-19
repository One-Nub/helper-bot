from functools import wraps

from discord import Forbidden, HTTPException, Interaction, NotFound
from discord.ext.commands import Context

from resources.constants import (
    ADMIN_ROLES,
    BLOXLINK_GUILD,
    CM,
    HUMAN_RESOURCES_ROLE,
    TRIAL_ROLE,
    WHITELISTED_USERS,
)
from resources.helper_bot import instance as bot


def developer_bypass(func):
    """Check for developers prior to performing the other checks."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        dev_check = await is_dev(*args, **kwargs)
        return dev_check if dev_check else await func(*args, **kwargs)

    return wrapper


@developer_bypass
async def is_staff(ctx: (Context | Interaction)) -> bool:
    """Determine if the current user is Bloxlink staff or not."""
    author = ctx.author if isinstance(ctx, Context) else ctx.user

    if not ctx.guild:
        return False

    # Get roles from the Bloxlink guild (if you can)
    # Updates the author argument accordingly.
    if ctx.guild_id != BLOXLINK_GUILD:
        try:
            bloxlink_guild = bot.get_guild(BLOXLINK_GUILD) or await bot.fetch_guild(BLOXLINK_GUILD)
            author = bloxlink_guild.get_member(author.id) or await bloxlink_guild.fetch_member(author.id)
        except (Forbidden, HTTPException, NotFound):
            # Fallback to roles in the current guild. Author is not updated.
            pass

    roles = {role.id for role in author.roles}

    admin_roles = set(ADMIN_ROLES.values())

    return len(roles.intersection(admin_roles)) != 0


@developer_bypass
async def is_staff_or_trial(ctx: (Context | Interaction)) -> bool:
    """Determine if the current user is a trial, Bloxlink staff, or neither."""
    author = ctx.author if isinstance(ctx, Context) else ctx.user

    if not ctx.guild:
        return False

    # Get roles from the Bloxlink guild (if you can)
    # Updates the author argument accordingly.
    if ctx.guild_id != BLOXLINK_GUILD:
        try:
            bloxlink_guild = bot.get_guild(BLOXLINK_GUILD) or await bot.fetch_guild(BLOXLINK_GUILD)
            author = bloxlink_guild.get_member(author.id) or await bloxlink_guild.fetch_member(author.id)
        except (Forbidden, HTTPException, NotFound):
            # Fallback to roles in the current guild. Author is not updated.
            pass

    roles = {role.id for role in author.roles}

    if TRIAL_ROLE in roles:
        return True

    return await is_staff(ctx)


async def is_dev(ctx: (Context | Interaction)) -> bool:
    """Determine if the current user is a bot developer."""
    author = ctx.author if isinstance(ctx, Context) else ctx.user

    return author.id in WHITELISTED_USERS


@developer_bypass
async def is_cm(ctx: (Context | Interaction)) -> bool:
    """Check if a user is a CM in the HQ or team center"""
    author = ctx.author if isinstance(ctx, Context) else ctx.user
    roles = {role.id for role in author.roles}
    admin_roles = set(CM.values())

    return not roles.isdisjoint(admin_roles)


@developer_bypass
async def is_hr(ctx: (Context | Interaction)) -> bool:
    """Check if a user is a CM in the HQ, or part of the human resources team in the team center"""
    author = ctx.author if isinstance(ctx, Context) else ctx.user
    roles = {role.id for role in author.roles}
    admin_roles = set(CM.values())

    return not roles.isdisjoint(admin_roles) or HUMAN_RESOURCES_ROLE in roles
