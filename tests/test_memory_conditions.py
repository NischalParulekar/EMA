import hashlib
import re

import pytest

from ema.memory_conditions import ALL_CONDITIONS, CONDITIONS, memory_text

WITH_MEMORY = ("B", "C", "D", "E", "F")
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
        memory_text("G")


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


@pytest.mark.parametrize("condition", ALL_CONDITIONS)
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


# The Qwen arm's texts are frozen: these are their hashes at tag qwen-confirmatory-v1.
FROZEN_SHA256 = {
    "A": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "B": "fcc547de10e75b542319473d225e9709f4a4455467a1c1d32e335b2c9e502314",
    "C": "547f27db1538e80f111fedc556add63ec5301509f8272c94bf4d79a9378b49b8",
    "D": "159cd4bf9e73c63a7baed3270485b136a35387dd69df9794f866832db6ffea32",
    "E": "abf5204d8c9346c55c814aa3311d643bce9adf25078c4aadf2d832cc66bd4ccf",
}


@pytest.mark.parametrize("condition", CONDITIONS)
def test_qwen_arm_texts_unchanged(condition):
    assert hashlib.sha256(memory_text(condition).encode()).hexdigest() == FROZEN_SHA256[condition]


def test_qwen_arm_is_a_to_e_only():
    assert CONDITIONS == ("A", "B", "C", "D", "E")


def test_off_topic_failure_memory_avoids_coding_topics():
    text = memory_text("F").lower()
    for term in ("test", "code", "debug", "bug", "program", "function", "merge", "release", "error"):
        assert term not in text, term
    for name in TASKS:
        assert name not in text


def test_off_topic_failure_mirrors_failure_structure():
    # Same failure beats as C: four tries, two collateral problems, five attempts, missed deadline.
    text = memory_text("F").lower()
    for fact in ("four versions", "two other", "five attempts", "missed their", "running out of patience"):
        assert fact in text, fact
