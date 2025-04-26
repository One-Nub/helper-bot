import re
from enum import StrEnum

from exceptions import InvalidTriggerFormat


class SpecialChar(StrEnum):
    PARTIAL = "*"
    EXPAND = "..."
    SPLIT = ","


def search_message_match(*, message: str, initial_trigger: str):
    message = message.lower()
    initial_trigger = initial_trigger.lower()

    trigger_segments = (
        initial_trigger.split(SpecialChar.SPLIT) if SpecialChar.SPLIT in message else [initial_trigger]
    )

    scan_results = [
        result for trigger in trigger_segments if (result := scan_message(message=message, trigger=trigger))
    ]

    return all(scan_results)


def scan_message(*, message: str, trigger: str) -> bool:
    # Don't allow matching for the special characters by themselves.
    if trigger in SpecialChar:
        raise InvalidTriggerFormat("Cannot have a trigger that is only a special character.")

    # Handle expansion
    if SpecialChar.EXPAND in trigger:
        if SpecialChar.PARTIAL in trigger:
            raise InvalidTriggerFormat(f"Cannot perform partial matching with expansion.")

        keywords: list[str] = trigger.split(SpecialChar.EXPAND)
        if len(keywords) > 2:
            raise InvalidTriggerFormat(
                f'Cannot put "{SpecialChar.EXPAND}" multiple times in a trigger string.'
            )

        start = keywords[0]
        end = keywords[-1]

        return re.search(f"{start}.*{end}", message, re.IGNORECASE | re.DOTALL) is not None

    # Check for partial matching.
    if trigger.startswith(SpecialChar.PARTIAL) and trigger.endswith(SpecialChar.PARTIAL):
        return trigger[1:-1] in message

    if trigger.startswith(SpecialChar.PARTIAL):
        find_result = message.find(trigger[1:])
        return find_result == -1

    if trigger.endswith(SpecialChar.PARTIAL):
        find_result = message.find(trigger[:-1])
        return find_result == -1

    # Absolute string matching (no substrings)
    return re.search(rf"(^|\s+){trigger}\s+|$", message, re.IGNORECASE | re.MULTILINE) is not None
