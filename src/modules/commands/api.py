from discord.ext.commands import Context
from helper_bot import instance as bot
import requests
import discord
import config

## api command

@bot.command("api", description="Fetch information via Bloxlink API.")
async def api(ctx: Context, lookup_id: int = 0):
    """Fetch information via Bloxlink API!"""    
    ## get the bot latency and round it, multiply by 1000
    try:
        if(lookup_id == 0):
            raise Exception("Missing argument `id`. Please provide a valid Discord ID.")
        elif(len(str(lookup_id)) < 17):
            raise Exception("Invalid Argument `id`. Please provide a valid Discord ID.")
        else:
            guild = 372036754078826496
            print(guild)
            string = 'https://api.blox.link/v4/public/guilds/{}/discord-to-roblox/{}'.format(guild, lookup_id)
            x = requests.get(string, headers={"Authorization": config.API_KEY})
            print(x.json())
    except Exception as Error: 
        embed_var = discord.Embed(title="Error", description=Error, color=0x00ff00)
        await ctx.reply(embed=embed_var)
  
   # x = requests.GET("https://api.blox.link/v1/user/" + lookup_id)
    # await ctx.reply("Pong! - " + str(latency) + "ms")
    