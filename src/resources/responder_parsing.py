import re
from enum import StrEnum

from resources.exceptions import InvalidTriggerFormat


class SpecialChar(StrEnum):
    """Special characters that can be used for a trigger string."""

    PARTIAL = "*"
    """Enables prefix/suffix pattern matching for a given string.

    Only works when at the beginning or ending of a string, placement elsewhere is ignored.

    CANNOT BE USED IN CONJUNCTION WITH SpecialChar.EXPAND
    """

    EXPAND = "..."
    """Equivalent of regex wildcard. Matches anything between two strings.

    Beginning and ending strings are treated as substrings in the context of the larger message.

    CANNOT BE USED IN CONJUNCTION WITH SpecialChar.PARTIAL \n
    CANNOT BE USED MULTIPLE TIMES IN ONE TRIGGER STRING
    """

    SPLIT = ","
    """Splits a single trigger string into unique matchers.

    All sub-matchers must be True for a match to be made.

    Other SpecialChar strings are supported as part of the unique matcher segments.

    Examples:
        "hello, world" - requires that both words "hello" and "world" appear.
        "ban*, game" - requires a word with a prefix of "ban-", and "game" in the message.
        "we ... farmers", dum" - would match "we are farmers bum ba dum ba dum dum dum"
    """


def search_message_match(*, message: str, initial_trigger: str) -> bool:
    """Search a message for a matching substring or trigger formatted string.

    Args:
        message (str): _description_
        initial_trigger (str): Given string to search for. Behavior changes based on presence of SpecialChar(s).

    Returns:
        bool: If the given trigger string found a match.
    """
    message = message.lower()
    initial_trigger = initial_trigger.lower()

    trigger_segments = (
        initial_trigger.split(SpecialChar.SPLIT)
        if SpecialChar.SPLIT in initial_trigger
        else [initial_trigger]
    )

    scan_results = [_scan_message(message=message, trigger=trigger.strip()) for trigger in trigger_segments]

    return all(scan_results)


def _scan_message(*, message: str, trigger: str) -> bool:
    validate_trigger_string(trigger)

    # Handle expansion
    if SpecialChar.EXPAND in trigger:
        # Splits & removes all empty strings found in the result (if any).
        # We have already validated this will be successful (by the power of doing it twice! once above in validate_trigger_string)
        keywords: list[str] = [*filter(None, trigger.split(SpecialChar.EXPAND))]
        start = keywords[0]
        end = keywords[-1]

        return re.search(f"{start}.*{end}", message, re.IGNORECASE | re.DOTALL) is not None

    # Check for partial matching.
    if trigger.startswith(SpecialChar.PARTIAL) and trigger.endswith(SpecialChar.PARTIAL):
        return _clean_trigger(trigger) in message

    # Had to use regex for everything 😔, darn substring matching edge cases that would be horrible to do otherwise
    if trigger.startswith(SpecialChar.PARTIAL):
        trigger = _clean_trigger(trigger, regex_escape=True)

        # enforces white space or end of message at end of match
        return re.search(rf"{trigger}(\s+|$)", message, re.IGNORECASE | re.MULTILINE) is not None

    if trigger.endswith(SpecialChar.PARTIAL):
        trigger = _clean_trigger(trigger, regex_escape=True)

        # enforces white space or start of message at start of match
        return re.search(rf"(\s+|^){trigger}", message, re.IGNORECASE | re.MULTILINE) is not None

    # Absolute string matching (no substrings)
    # Clean in case there are special characters to be literally searched for.
    trigger = _clean_trigger(trigger, regex_escape=True)
    return re.search(rf"(\s+|^){trigger}(\s+|$)", message, re.IGNORECASE | re.MULTILINE) is not None


def _clean_trigger(trigger: str, *, regex_escape=False) -> str:
    """Removes asterisks and leading+trailing white space. Optionally escapes regex special characters."""
    if trigger.startswith(SpecialChar.PARTIAL):
        trigger = trigger[1:]

    if trigger.endswith(SpecialChar.PARTIAL):
        trigger = trigger[:-1]

    trigger = trigger.strip()
    if regex_escape:
        trigger = re.escape(trigger)

    return trigger


def validate_trigger_string(trigger: str) -> bool:
    """Validate if a trigger string is to be accepted. True on approval, InvalidTriggerFormat otherwise."""

    # Preemptively catch SpecialChar strings.
    if trigger in (x.value for x in SpecialChar):
        # In Python 3.12 we can just do "if trigger in SpecialChar".
        raise InvalidTriggerFormat("Cannot have a trigger that is only a special character.")

    trigger_segments = trigger.split(SpecialChar.SPLIT) if SpecialChar.SPLIT in trigger else [trigger]
    for trig in trigger_segments:
        # Checking again since here is after we split on commas.
        if trig in (x.value for x in SpecialChar):
            # In Python 3.12 we can just do "if trigger in SpecialChar".
            raise InvalidTriggerFormat("Cannot have a trigger that is only a special character.")

        # Handle expansion
        if SpecialChar.EXPAND in trig:
            if SpecialChar.PARTIAL in trig:
                raise InvalidTriggerFormat(
                    f"Cannot perform partial matching ({SpecialChar.PARTIAL}) with "
                    f"expansion ({SpecialChar.EXPAND}) in the same segment."
                )

            # Splits & removes all empty strings found in the result (if any).
            keywords: list[str] = [*filter(None, trig.split(SpecialChar.EXPAND))]
            if len(keywords) > 2:
                raise InvalidTriggerFormat(
                    f'Cannot put "{SpecialChar.EXPAND}" multiple times in a trigger string.'
                )

            if len(keywords) <= 1:
                raise InvalidTriggerFormat(
                    f"Not enough strings found after splitting over {SpecialChar.EXPAND}. "
                    f"Consider using {SpecialChar.PARTIAL} instead."
                )

    return True
