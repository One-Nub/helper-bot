from discord.ext.commands import Context
from helper_bot import instance as bot
import requests
import discord
import json
import config
from datetime import datetime
from constants import RED, BLURPLE

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
            string = f'https://api.blox.link/v4/public/guilds/{guild}/discord-to-roblox/{lookup_id}'
            x = requests.get(string, headers={"Authorization" : config.API_KEY})
            response = x.json()
            if(response.get("resolved") != None):
                del response["resolved"]
            success_embed = discord.Embed()
            success_embed.title = "Success"
            success_embed.description= f"Sent a request to {string}.\n\n**Response**\n```json\n{response}```"
            success_embed.color = BLURPLE
            success_embed.timestamp = datetime.now()
            success_embed.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)
            await ctx.reply(embed=success_embed, mention_author=False)
    except Exception as Error: 
        embed_var = discord.Embed(title="<:BloxlinkDead:823633973967716363> Error", description=Error, color=RED)
        embed_var.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)
        embed_var.timestamp = datetime.now()
        await ctx.reply(embed=embed_var)
  
   # x = requests.GET("https://api.blox.link/v1/user/" + lookup_id)
    # await ctx.reply("Pong! - " + str(latency) + "ms")
    