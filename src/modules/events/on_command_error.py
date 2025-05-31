import asyncio
import traceback
from datetime import datetime

import discord
from discord.ext.commands import (
    CheckFailure,
    CommandError,
    CommandInvokeError,
    CommandNotFound,
    Context,
    MissingRequiredArgument,
)

from resources.constants import (
    ADMIN_ROLES,
    BLOXLINK_DEAD,
    BLOXLINK_GUILD,
    RED,
    TAG_METRIC_IGNORE_CHANNELS,
    TRIAL_ROLE,
)
from resources.exceptions import HelperError
from resources.helper_bot import instance as bot


@bot.event
async def on_command_error(ctx: Context, error: CommandError):
    # For commands with error handlers, we don't handle it here EXCEPT when the error is a HelperError.
    original_is_custom_error = isinstance(error, CommandInvokeError) and isinstance(
        error.original, HelperError
    )
    valid_error_handler = ctx.command is not None and ctx.command.has_error_handler()
    valid_cog_handler = ctx.cog is not None and ctx.cog.has_error_handler()

    if (valid_error_handler or valid_cog_handler) and not original_is_custom_error:
        return

    error_embed = discord.Embed(
        title=f"{BLOXLINK_DEAD} Error",
        description=error,
        color=RED,
    )
    error_embed.set_footer(text="Bloxlink Helper", icon_url=ctx.author.display_avatar)
    error_embed.timestamp = datetime.now()

    should_delete_original = True

    match error:
        case CommandNotFound():
            # Check if a tag that matches the input can be sent.

            name = ctx.invoked_with
            if not name:
                return

            custom_text = ctx.message.content.split(name, maxsplit=1)[1]

            if not ctx.guild:
                return

            match_command = await bot.db.get_tag(name)

            if match_command:
                await ctx.message.delete()

                await ctx.send(
                    f"{custom_text} {match_command['content']}",
                    reference=ctx.message.reference,  # type: ignore
                )  # type: ignore

                await bot.db.update_tag(
                    name,
                    use_count=match_command["use_count"] + 1,
                )

                # Update staff metrics - only when used in a valid channel in bloxlink guild.
                # TODO: Move this to its own method somewhere to be called instead of this copy pasted code.
                if ctx.guild.id != BLOXLINK_GUILD or ctx.message.channel.id in TAG_METRIC_IGNORE_CHANNELS:
                    return

                author_roles = set([role.id for role in ctx.author.roles])  # type: ignore
                staff_roles = set(ADMIN_ROLES.values())
                if TRIAL_ROLE in author_roles:
                    await bot.db.update_staff_metric(str(ctx.author.id), "trial", incr_tags=True)
                elif author_roles.intersection(staff_roles):
                    await bot.db.update_staff_metric(str(ctx.author.id), "volunteer", incr_tags=True)

            return

        case CheckFailure():
            error_embed.description = "You do not have permissions to use this command!"

        case MissingRequiredArgument():
            param = error.param.name
            message = f"You're missing the required {param} argument!"

            if ctx.command.name.startswith("tag"):  # type: ignore
                param = "the tag content" if param == "tag_content" else "the tag name"
                message = f"You're missing {param}!"

            error_embed.description = message

        case CommandInvokeError() as err:
            # Catch HelperError (its wrapped in CommandInvokeError)
            # Lets us handle the original error if desired.
            match err.original:
                case HelperError() as sub_err:
                    error_embed.description = str(sub_err)

                case _ as sub_err:
                    error_embed.description = (
                        f"{sub_err}\n\nAdditional Info:```{traceback.format_exc(chain=True)}```"
                    )
                    should_delete_original = False

        case _ as err:
            error_embed.description = f"{err}\n\nAdditional Info:```{traceback.format_exc(chain=True)}```"
            should_delete_original = False

    # Send the error embed
    await ctx.reply(
        embed=error_embed,
        mention_author=False,
        delete_after=5.0 if should_delete_original else None,  # type: ignore
        ephemeral=True,
    )  # type: ignore

    if not ctx.interaction and should_delete_original:
        await asyncio.sleep(5)
        await ctx.message.delete()

    if not should_delete_original:
        raise error


async def setup(bot): ...
