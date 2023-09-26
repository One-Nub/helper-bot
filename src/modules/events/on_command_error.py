from discord.ext.commands import (
    CheckFailure,
    CommandError,
    CommandNotFound,
    Context,
    MissingRequiredArgument,
)

from resources.helper_bot import instance as bot


@bot.event
async def on_command_error(ctx: Context, error: CommandError):
    match error:
        case CommandNotFound():
            name = ctx.invoked_with
            if not name:
                return

            custom_text = ctx.message.content.split(name, maxsplit=1)[1]
            match_command = await bot.db.get_tag(name)

            if match_command:
                await ctx.message.delete()

                await ctx.send(
                    f"{custom_text} {match_command['content']}",
                    reference=ctx.message.reference,
                )

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

        case MissingRequiredArgument():
            param = error.param.name
            message = f"You're missing the required {param} argument!"

            if ctx.command.name.startswith("tag"):
                param = "the tag content" if param == "tag_content" else "the tag name"
                message = f"You're missing {param}!"

            await ctx.reply(
                content=message,
                mention_author=False,
                delete_after=5.0,
                ephemeral=True,
            )

            if not ctx.interaction:
                await ctx.message.delete()

        case _:
            raise error
