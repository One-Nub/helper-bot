import logging

from discord import ComponentType, Interaction, InteractionType

from resources.helper_bot import instance as bot
from resources.models.interaction_data import MessageComponentData


@bot.event
async def on_interaction(interaction: Interaction):
    # Handle interactions with custom handler

    match interaction.type:
        case InteractionType.component:
            if not interaction.data:
                logging.error("Discord failed at it's job - no interaction data on component interaction")
                return

            # Only really doing this cuz discord.py buries the actual type and these are basically dicts to us anyway.
            mcd = MessageComponentData(**interaction.data)  # type:ignore[reportArgumentType]

            match mcd.component_type:
                case ComponentType.button.value:
                    for name, handler in bot.button_handlers.items():
                        if not mcd.custom_id.startswith(name):
                            continue

                        await handler(interaction)

                case (
                    ComponentType.string_select.value
                    | ComponentType.user_select.value
                    | ComponentType.role_select.value
                    | ComponentType.mentionable_select.value
                    | ComponentType.channel_select.value
                ):
                    # TODO: Implement select channel handler method and triggers.
                    print(f"select menu component of some kind {mcd.component_type}")

        case InteractionType.application_command:
            pass

        case InteractionType.autocomplete:
            pass

        case InteractionType.modal_submit:
            pass
