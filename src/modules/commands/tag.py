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
    try:

        # get the tag data
        taglist = await bot.db.get_all_tags()
        tagnames = []

        # get all the tag names
        for key in range(0, len(taglist)):
            tagnames.append(taglist[key]['_id'])
        
        # sort the tag names
        tagnames.sort(reverse = False)


        # pages stuff
        count = 20
        pages = 1
        while len(taglist) > count:
            count += 20
            pages += 1
    
        # each page has a different set of users
        cur_page = 1
        mainlist = []

        for current_page in range(0, pages):
            x = current_page * 20
            y = x + 20
            mainlist.append(tagnames[x:y])


    
        # build the embed ---------------------
        async def build_embed(cur_page):
            embed_tags = discord.Embed(
                title = "All Tags",
                description = "----------",
                color = 0x7289da,
                )
    
            # set some variables
            currentlist = mainlist[cur_page - 1]
            mystr = ""


            # build the embed
            for key in currentlist:
                index = currentlist.index(key) + 1


                # building the lines in an embed
                mystr += key + "\n"

                if index == 10 or index == 20:
                    embed_tags.add_field(name = "", value = mystr, inline = True)
                    mystr = key + "\n"
                    mystr = ""

            # make sure the embeds send even if we didn't hit 5 or 10 users
            if len(currentlist) < 10:
                embed_tags.add_field(name = " ", value = mystr, inline = True)
            if len(currentlist) > 10 and len(currentlist) < 20:
                embed_tags.add_field(name = " ", value = mystr, inline = True)


            # footer
            embed_tags.set_footer(text = f"Page {cur_page}/{pages}", icon_url = ctx.author.display_avatar)
            # return the entire embed
            return embed_tags



        ## get the user for reactions
        if ctx.bot.get_user(ctx.author.id) == None:
            user = await ctx.bot.fetch_user(ctx.author.id)
        else:
            user = ctx.bot.get_user(ctx.author.id)





        ## send the reactions part, nub pls fix this for buttons ------
        send_embed = await ctx.send(embed = await build_embed(cur_page))
        if pages != 1:
            await send_embed.add_reaction("◀️")
            await send_embed.add_reaction("🗑️")
            await send_embed.add_reaction("▶️")

            ## checks if the author is the only one reacting
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "🗑️", "▶️"]

    

            ## this is the reactions part, nub replace this with buttons ty --------
            while True:
                try:
                    reaction, user = await ctx.bot.wait_for("reaction_add", timeout=120, check = check)
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
        await ctx.send(Error)