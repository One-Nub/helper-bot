from discord.ext.commands import Context
from helper_bot import instance as bot


## ping command

@bot.command("ping", description="Check the bot's latency.")
async def ping(ctx: Context):
    """find out what the bot latency is!"""    
    ## get the bot latency and round it, multiply by 1000
    latency = round((ctx.bot.latency) * 1000)
    await ctx.reply("Pong! - " + str(latency) + "ms")
    