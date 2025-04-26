from contextlib import nullcontext

import pytest

import src.resources.responder_parsing as tr
from src.resources.exceptions import InvalidTriggerFormat

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


@pytest.mark.skip()
@pytest.mark.parametrize(
    "trigger_str,expected",
    [
        ("verify...message", nullcontext(True)),
        ("verify ... need", nullcontext(True)),
        ("need...verify", nullcontext(False)),
        ("banned ... help", nullcontext(False)),
        ("...", pytest.raises(InvalidTriggerFormat)),
    ],
)
def test_expand_trigger(trigger_str: str, expected): ...


@pytest.mark.skip()
@pytest.mark.parametrize(
    "trigger_str,expected",
    [
        (",", pytest.raises(InvalidTriggerFormat)),
    ],
)
def test_split_trigger(trigger_str: str, expected): ...


@pytest.mark.skip()
@pytest.mark.parametrize(
    "trigger_str,expected",
    [],
)
def test_absolute_trigger(trigger_str: str, expected): ...
