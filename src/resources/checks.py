from discord.ext.commands import Context

from resources.constants import ADMIN_ROLES, WHITELISTED_USERS


async def is_staff(ctx: Context) -> bool:
    if ctx.author.id in WHITELISTED_USERS:
        return True

    roles = set([role.id for role in ctx.author.roles])
    admin_roles = set(ADMIN_ROLES.values())

    return len(roles.intersection(admin_roles)) != 0
