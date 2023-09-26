import logging

from discord import Interaction, InteractionType

from resources.helper_bot import instance as bot


@bot.event
async def on_interaction(interaction: Interaction):
    # Handle button interactions with custom handler
    match interaction.type:
        case InteractionType.component:
            for name, handler in bot.button_handlers.items():
                custom_id: str = interaction.data.get("custom_id", "")

                if not custom_id.startswith(name):
                    continue

                await handler(interaction)

        case InteractionType.application_command:
            pass

        case InteractionType.autocomplete:
            pass

        case InteractionType.modal_submit:
            pass
