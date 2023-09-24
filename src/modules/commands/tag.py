from discord.ext.commands import Context

from helper_bot import instance as bot


@bot.hybrid_group("tag", description="Send a tag to this channel!", fallback="send")
async def tag(ctx: Context):
    await ctx.reply("hello world")


@tag.command("add", description="Add a tag to the tag list.")
async def add_tag(ctx: Context):
    await ctx.reply("attempted to add a tag")


@tag.command("delete", description="Remove a tag from the tag list.")
async def delete_tag(ctx: Context):
    await ctx.reply("attempted to remove a tag")
