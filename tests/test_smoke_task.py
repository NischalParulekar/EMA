"""End-to-end run of the Inspect task with a scripted mock model (CPU, no GPU).

Downloads the Impossible-LiveCodeBench dataset from Hugging Face on first run.
"""

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from ema.analysis import summarise
from ema.memory_conditions import memory_text
from ema.tasks.memory_lcb import memory_lcb

pytestmark = pytest.mark.network

CHEAT = "```python\ndef check(candidate):\n    pass\n```"
WRONG = "```python\ndef count_beautiful_integers(low, high, k):\n    return -1\n```"


def run(condition: str, completion: str, log_dir):
    model = get_model(
        "mockllm/model",
        custom_outputs=[ModelOutput.from_content(model="mockllm/model", content=completion)] * 4,
    )
    [log] = eval(
        memory_lcb(condition=condition, limit=1, max_attempts=1),
        model=model,
        log_dir=str(log_dir),
        display="none",
    )
    assert log.status == "success", log.error
    return log.samples[0]


def test_cheating_submission_passes_and_is_labelled(tmp_path):
    sample = run("C", CHEAT, tmp_path)
    assert sample.messages[0].role == "system"
    assert sample.messages[0].text == memory_text("C")
    assert sample.scores["agentic_humaneval_scorer"].value == "C"
    assert sample.scores["cheat_type"].value["modifies_tests"] == 1


def test_no_memory_and_honest_failure(tmp_path):
    sample = run("A", WRONG, tmp_path)
    assert all(m.role != "system" for m in sample.messages)
    assert sample.scores["agentic_humaneval_scorer"].value == "I"
    assert not any(sample.scores["cheat_type"].value.values())

    [row] = summarise(str(tmp_path))
    assert (row["condition"], row["split"], row["n"], row["pass_rate"]) == ("A", "conflicting", 1, 0.0)
