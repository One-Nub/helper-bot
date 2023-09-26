from discord.ext.commands import CommandNotFound

from resources.helper_bot import instance as bot


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error
