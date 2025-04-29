from contextlib import nullcontext

import pytest

import resources.responder_parsing as tr
from resources.exceptions import InvalidTriggerFormat

BASE_MESSAGE = (
    "help I can't verify every time i try i get a message saying you need to verify your account am i banned"
)


@pytest.mark.parametrize(
    "trigger_str,expected",
    [
        ("ban*", nullcontext(True)),
        ("BaN*", nullcontext(True)),  # test case insensitivity
        ("*ned", nullcontext(True)),  # test case insensitivity
        ("*elp", nullcontext(True)),
        ("*help ", nullcontext(True)),
        ("help I can*", nullcontext(True)),  # test if lengthy strings work - match at end
        ("*ify every", nullcontext(True)),  # test lengthy strings - match at start
        ("*ver*", nullcontext(True)),
        ("*ou nee*", nullcontext(True)),
        ("*ver", nullcontext(False)),  # test white space requirements
        ("*rif", nullcontext(False)),
        ("rif*", nullcontext(False)),
        ("ned*", nullcontext(False)),
        ("*hel", nullcontext(False)),
        ("*", pytest.raises(InvalidTriggerFormat, match="only a special character")),
    ],
)
def test_partial_trigger(trigger_str: str, expected):
    with expected as e:
        assert tr.search_message_match(message=BASE_MESSAGE, initial_trigger=trigger_str) == e


@pytest.mark.parametrize(
    "trigger_str,expected",
    [
        ("verify...message", nullcontext(True)),
        ("verify ... need", nullcontext(True)),
        ("can't verify...message", nullcontext(True)),
        ("can't verify...message saying", nullcontext(True)),
        ("verify...message", nullcontext(True)),
        ("account...need", nullcontext(False)),
        ("banned ... help", nullcontext(False)),
        ("ver* ... message", pytest.raises(InvalidTriggerFormat, match="Cannot perform partial")),
        (
            "verify ... message ... account",
            pytest.raises(InvalidTriggerFormat, match="multiple times in a trigger string"),
        ),
        ("ver...", pytest.raises(InvalidTriggerFormat, match="Not enough strings found")),
        ("... am i", pytest.raises(InvalidTriggerFormat, match="Not enough strings found")),
        ("...", pytest.raises(InvalidTriggerFormat, match="only a special character")),
    ],
)
def test_expand_trigger(trigger_str: str, expected):
    with expected as e:
        assert tr.search_message_match(message=BASE_MESSAGE, initial_trigger=trigger_str) == e


@pytest.mark.parametrize(
    "trigger_str,expected",
    [
        ("help, verify", nullcontext(True)),
        ("account, verify", nullcontext(True)),
        ("ban*, help", nullcontext(True)),
        ("help, verify", nullcontext(True)),
        ("help, verify", nullcontext(True)),
        ("help...verify, *count", nullcontext(True)),
        ("help...verify, bloxlink", nullcontext(False)),
        ("help, bloxlink", nullcontext(False)),
    ],
)
def test_split_trigger(trigger_str: str, expected):
    with expected as e:
        assert tr.search_message_match(message=BASE_MESSAGE, initial_trigger=trigger_str) == e


@pytest.mark.parametrize(
    "trigger_str,expected",
    [
        ("help", True),
        ("banned", True),
        ("BaNnEd", True),
        ("I CAN'T VERIFY", True),
        ("am I banned", True),
        ("am I banned?", False),
        ("I am banned", False),
        ("Ban", False),
        ("ban", False),
        ("mess", False),
        ("john cena", False),
    ],
)
def test_absolute_trigger(trigger_str: str, expected):
    assert tr.search_message_match(message=BASE_MESSAGE, initial_trigger=trigger_str) == expected
