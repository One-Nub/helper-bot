from discord.ext.commands import Context
import discord

from helper_bot import instance as bot

import asyncio
from datetime import datetime, timedelta



@bot.hybrid_group("tag", description="Send a tag to this channel!", fallback="send")
async def tag(ctx: Context):
    await ctx.reply("hello world")


@tag.command("add", description="Add a tag to the tag list.")
async def add_tag(ctx: Context):
    await ctx.reply("attempted to add a tag")


@tag.command("delete", description="Remove a tag from the tag list.")
async def delete_tag(ctx: Context):
    await ctx.reply("attempted to remove a tag")



## tags command

@tag.command("all", description="View all the tags in the tag list.")
async def view_tag(ctx: Context):
    await ctx.reply("attempted to view all tags")
    '''try:

        # get the tag data
        cookielist = final_list[1]

        # pages stuff
        count = 10
        pages = 1
        while len(cookielist) > count:
            count += 10
            pages += 1
    
        # each page has a different set of users
        cur_page = 1
        mainlist = []

        for current_page in range(0, pages):
            x = current_page * 10
            y = x + 10
            mainlist.append(cookielist[x:y])


    
        # build the embed ---------------------
        async def build_embed(cur_page):
            embed_tags = discord.Embed(
                title = "Leaderboard",
                description = "desc",
                color = 0x7289da,
                )
    
            # set the server icon
            embed_tags.set_thumbnail(url = ctx.guild.icon)

            currentlist = mainlist[cur_page - 1]

            mystr = ""
            # build the leaderboard
            for key in currentlist:
                # try to get_user, if none then fetch
                if ctx.bot.get_user(key) == None:
                    user = await ctx.bot.fetch_user(key)
                else:
                    user = ctx.bot.get_user(key)
        
                # setting variables for organization
                index = currentlist.index(key) + 1


                # building the lines in an embed
                mystr += "this is a line in the embed"

                if index == 5 or index == 10:
                    embed_tags.add_field(name = "", value = mystr, inline = True)
                    mystr = ""

            # make sure the embeds send even if we didn't hit 5 or 10 users
            if len(currentlist) < 5:
                embed_tags.add_field(name = " ", value = mystr, inline = True)
            if len(currentlist) > 5 and len(currentlist) < 10:
                embed_tags.add_field(name = " ", value = mystr, inline = True)



            # footer
            embed_tags.set_footer(text = f"Page {cur_page}/{pages}", icon_url = ctx.author.display_avatar)
            # return the entire embed
            return embed_tags



        send_embed = await ctx.send(embed = await build_embed(cur_page))
        if pages != 1:
            await send_embed.add_reaction("◀️")
            await send_embed.add_reaction("🗑️")
            await send_embed.add_reaction("▶️")

            # This makes sure nobody except the command sender can interact with the menu
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "🗑️", "▶️"]
    
            while True:
                try:
                    reaction, user = await ctx.bot.wait_for("reaction_add", timeout=120, check=check)
                    # waiting for a reaction to be added - times out after 120 seconds
                    if str(reaction.emoji) == "▶️" and cur_page != pages:
                        cur_page += 1
                        await send_embed.edit(embed = (await build_embed(cur_page)))
                        await send_embed.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "◀️" and cur_page > 1:
                        cur_page -= 1
                        await send_embed.edit(embed = (await build_embed(cur_page)))
                        await send_embed.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "🗑️" :
                        await send_embed.remove_reaction(reaction, user)
                        raise asyncio.TimeoutError
                
                    else:
                        await send_embed.remove_reaction(reaction, user)
                        # removes reactions if the user tries to go forward on the last page or backwards on the first page
                except asyncio.TimeoutError:
                    await send_embed.clear_reactions()
                    break
                    # ending the loop if user doesn't react after x seconds

    # exception handling
    except Exception as Error:
        await ctx.send(Error)'''