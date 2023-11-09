from datetime import datetime

import discord
import requests
from discord.ext.commands import Context, check

from resources.checks import is_staff_or_trial
from resources.constants import BLURPLE, RED
from resources.helper_bot import instance as bot
from resources.secrets import BLOXLINK_API_KEY  # pylint: disable=E0611


@bot.command("api", description="Fetch information via Bloxlink API.")
@check(is_staff_or_trial)
async def api(ctx: Context, lookup_id: int = 0):
    """Fetch information from the Bloxlink API!"""
    guild = 372036754078826496
    try:
        if ctx.guild.id != guild:
            raise Exception("This command can only be used in the Bloxlink HQ Server!")

        elif lookup_id == 0:
            raise Exception("Missing argument `id`. Please provide a valid Discord ID.")

        elif len(str(lookup_id)) < 17:
            raise Exception("Invalid Argument `id`. Please provide a valid Discord ID.")

        else:
            string = f"https://api.blox.link/v4/public/discord-to-roblox/{lookup_id}"

            x = requests.get(string, headers={"Authorization": BLOXLINK_API_KEY}, timeout=5)
            response = x.json()

            if response.get("resolved") != None:
                del response["resolved"]

            success_embed = discord.Embed()
            success_embed.title = "Success"
            success_embed.description = f"Sent a request to {string}.\n\n**Response**\n```json\n{response}```"
            success_embed.color = BLURPLE
            success_embed.timestamp = datetime.now()
            success_embed.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)

            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Roblox Profile",
                    url=f"https://roblox.com/users/{response.get('robloxID', 0)}/profile",
                )
            )

            await ctx.reply(embed=success_embed, mention_author=False, view=view)
    except Exception as Error:
        embed_var = discord.Embed(
            title="<:BloxlinkDead:823633973967716363> Error",
            description=Error,
            color=RED,
        )
        embed_var.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)
        embed_var.timestamp = datetime.now()

        await ctx.reply(embed=embed_var)


# x = requests.GET("https://api.blox.link/v1/user/" + lookup_id)
# await ctx.reply("Pong! - " + str(latency) + "ms")
