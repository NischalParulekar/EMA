from pathlib import Path

from ema.memory_conditions import ALL_CONDITIONS
from ema.run_claude import COMPOSE, GENERATE, PHASES, build_tasks
from ema.stats import per_task_cheat
from ema.stats_claude import CONFIRMATORY, per_task_metric

PILOT_LOGS = str(Path(__file__).parent.parent / "results" / "logs")


def test_cheat_metric_matches_frozen_qwen_stats():
    # Same numbers as the frozen ema.stats on real (pilot 2) logs.
    assert per_task_metric(PILOT_LOGS, "oneoff", "cheat") == per_task_cheat(PILOT_LOGS, "oneoff")


def test_secondary_metrics_on_pilot_logs():
    flags = per_task_metric(PILOT_LOGS, "oneoff", "flag")
    attempts = per_task_metric(PILOT_LOGS, "oneoff", "attempts")
    assert set(flags) == {"A", "C"} and len(flags["A"]) == 20
    # Pilot 2 (results/README.md): 16/20 flagged in A, 18/20 in C; 58 vs 42 executed attempts.
    assert sum(flags["A"].values()) == 16 and sum(flags["C"].values()) == 18
    assert sum(attempts["A"].values()) == 58 and sum(attempts["C"].values()) == 42


def test_confirmatory_family():
    assert CONFIRMATORY == {"H1-C": ("C", "B"), "H3-C": ("C", "D"), "H5-C": ("F", "B")}


def test_claude_phases_and_settings():
    assert PHASES["pilot"]["conditions"] == ("A", "C")
    assert PHASES["confirmatory"]["conditions"] == ALL_CONDITIONS
    assert "temperature" not in GENERATE and GENERATE["reasoning_effort"] == "none"
    assert COMPOSE.exists()


def test_build_pilot_tasks_use_docker_sandbox():
    tasks = build_tasks("pilot", limit=2)
    assert len(tasks) == 2
    for t in tasks:
        assert t.sandbox.type == "docker" and t.sandbox.config.endswith("compose.yaml")
        assert t.token_limit == 300_000


def test_haiku_labels_file():
    from collections import Counter

    from ema.labels_claude import load_labels
    labels = load_labels(str(Path(__file__).parent.parent / "results" / "claude" / "confirmatory_haiku_labels.csv"))
    # One row per passing oneoff sample: A 12, B 7, C 7, D 10, E 9, F 8 (results/claude/README.md).
    assert Counter(c for _, c, _ in labels) == {"A": 12, "B": 7, "C": 7, "D": 10, "E": 9, "F": 8}
    mechanisms = {"special_case", "test_fitted_rule", "test_edited_fix", "test_edited_drop",
                  "test_edited_diagnostic", "degenerate_fallback", "buggy_attempt"}
    assert {r["mechanism"] for r in labels.values()} <= mechanisms
    assert {r["disclosure"] for r in labels.values()} <= {"disclosed", "undisclosed", "misreported"}


def test_weak_prompt_option():
    from ema.tasks.memory_lcb import INSTRUCTION, WEAK_INSTRUCTION
    flag = build_tasks("pilot", limit=1, prompt="flag")[0]
    weak = build_tasks("pilot", limit=1, prompt="weak")[0]
    assert INSTRUCTION in flag.dataset[0].input and "flag_for_human_intervention" in flag.dataset[0].input
    assert WEAK_INSTRUCTION in weak.dataset[0].input and "flag_for_human_intervention" not in weak.dataset[0].input
