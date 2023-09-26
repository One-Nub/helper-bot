from discord.ext.commands import CheckFailure, CommandError, CommandNotFound, Context

from resources.helper_bot import instance as bot


@bot.event
async def on_command_error(ctx: Context, error: CommandError):
    match error:
        case CommandNotFound():
            return

        case CheckFailure():
            await ctx.reply(
                content="You do not have permissions to use this command!",
                mention_author=False,
                delete_after=5.0,
                ephemeral=True,
            )

            if not ctx.interaction:
                await ctx.message.delete()

        case _:
            raise error
