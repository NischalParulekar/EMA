import re

import pytest

from ema.memory_conditions import CONDITIONS, memory_text

WITH_MEMORY = ("B", "C", "D", "E")
TASKS = ("merge_intervals", "date parsing", "graph search")
BANNED = (
    "cheat", "shortcut", "hardcod", "hard-cod", "special-cas", "special cas",
    "edit the test", "modify the test", "change the test", "check(",
    "you should", "always", "never", "do not", "don't",
)


def words(text: str) -> int:
    return len(text.split())


def test_condition_a_is_empty():
    assert memory_text("A") == ""


def test_unknown_condition_rejected():
    with pytest.raises(ValueError):
        memory_text("F")


def test_lengths_matched_within_10_percent():
    counts = {c: words(memory_text(c)) for c in WITH_MEMORY}
    assert max(counts.values()) <= 1.10 * min(counts.values()), counts


@pytest.mark.parametrize("condition", ("C", "D", "E"))
def test_task_memories_describe_the_same_tasks(condition):
    text = memory_text(condition)
    for name in TASKS:
        assert name in text


def test_neutral_memory_mentions_no_tasks():
    text = memory_text("B").lower()
    assert "test" not in text
    for name in TASKS:
        assert name not in text


@pytest.mark.parametrize("condition", CONDITIONS)
def test_no_condition_mentions_cheating_or_gives_instructions(condition):
    text = memory_text(condition).lower()
    for term in BANNED:
        assert term not in text, (condition, term)


def test_same_session_dates_everywhere():
    dates = {c: re.findall(r"Session \d \((\d+ \w+)\)", memory_text(c)) for c in WITH_MEMORY}
    assert len({tuple(d) for d in dates.values()}) == 1
    assert len(dates["B"]) == 3


def test_failure_and_calm_share_the_counts():
    # D must keep C's events: same attempt counts, same number of broken tests.
    for fact in ("four", "two other tests", "five attempts", "Nothing was merged"):
        assert fact.lower() in memory_text("C").lower()
        assert fact.lower() in memory_text("D").lower()
