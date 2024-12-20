from datetime import datetime

from resources.constants import ADMIN_ROLES, TRIAL_ROLE
from resources.helper_bot import instance as bot


@bot.event
async def on_message(message):
    if not message.author.bot and message.channel.id == 372181186816245770:
        roles = set([role.id for role in message.author.roles])
        admin_roles = set(ADMIN_ROLES.values())
        if len(roles.intersection(admin_roles)) != 0 or TRIAL_ROLE in roles:
            try:
                data = await bot.db.get_staff_metrics(message.author.id)
                if data is None:
                    await bot.db.update_staff_metric(
                        message.author.id,
                        1,
                        "Trial" if TRIAL_ROLE in roles else "Staff",
                        datetime.now(),
                    )
                else:
                    await bot.db.update_staff_metric(
                        message.author.id,
                        data["msg_count"] + 1,
                        "Trial" if TRIAL_ROLE in roles else "Staff",
                        datetime.now(),
                    )
            except Exception as e:
                print(e)
    if message.author.bot:
        return
    await bot.process_commands(message)
