from discord.ext.commands import Context

from resources.helper_bot import instance as bot


@bot.hybrid_command("ping", description="Check the bot's latency.")
async def ping(ctx: Context):
    """Find out what the bot latency is!"""
    ## get the bot latency and round it, multiply by 1000
    latency = round((ctx.bot.latency) * 1000)
    await ctx.reply("Pong! - " + str(latency) + "ms")
