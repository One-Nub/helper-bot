import traceback

from discord.ext.commands import CheckFailure, CommandError, CommandNotFound, Context, MissingRequiredArgument

from resources.helper_bot import instance as bot


@bot.event
async def on_command_error(ctx: Context, error: CommandError):
    if (ctx.command is not None and ctx.command.has_error_handler()) or (
        ctx.cog is not None and ctx.cog.has_error_handler()
    ):
        # Ignore commands that have their own error handlers.
        return

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

                await bot.db.update_tag(
                    name,
                    match_command["content"],
                    use_count=match_command["use_count"] + 1,
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

        case _ as err:
            output = f"{err}\n\nAdditional Info:```{traceback.format_exc(chain=True)}```"
            await ctx.reply(
                content=output,
                mention_author=False,
                ephemeral=True,
            )
            raise err
