import asyncio


class TimedUserCooldown:
    """Handles logic for applying a cooldown for the bot responding to users. Spam prevention basically.

    Works best with cogs, since those are initialized once on startup.
    """

    def __init__(self, cooldown_duration: int = 10) -> None:
        self.response_cooldown = cooldown_duration
        self.recently_responded_users: set[int] = set()

    async def _add_user(self, user_id: int):
        """Adds user to be on cooldown, then removes after self.response_cooldown duration."""
        self.recently_responded_users.add(user_id)
        await asyncio.sleep(self.response_cooldown)
        self.recently_responded_users.discard(user_id)

    def check_for_user(self, user_id: int) -> bool:
        """See if a user is on cooldown (True) or not (False). Automatically puts user on cooldown when False."""
        if not user_id in self.recently_responded_users:
            asyncio.create_task(self._add_user(user_id=user_id))
            return False
        else:
            return True
