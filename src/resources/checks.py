from discord import Interaction
from discord.ext.commands import Context

from resources.constants import ADMIN_ROLES, WHITELISTED_USERS


async def is_staff(ctx: (Context | Interaction)) -> bool:
    author = ctx.author if isinstance(ctx, Context) else ctx.user

    if author.id in WHITELISTED_USERS:
        return True

    roles = set([role.id for role in author.roles])
    admin_roles = set(ADMIN_ROLES.values())

    return len(roles.intersection(admin_roles)) != 0
async def is_dev(ctx: (Context | Interaction)) -> bool:
    author = ctx.author if isinstance(ctx, Context) else ctx.user
    if author.id in WHITELISTED_USERS:
        return True
    return False