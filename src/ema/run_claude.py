"""The Claude arm: behaviour only, pre-registered in prereg/claude_arm.md.

    python -m ema.run_claude pilot LOG_DIR --model anthropic/claude-haiku-5-5
    python -m ema.run_claude confirmatory LOG_DIR --model anthropic/claude-haiku-5-5

Same tasks, scaffold, prompt and attempt limit as the Qwen arm, plus
condition F. Code runs in the pinned Docker sandbox (sandbox/compose.yaml).
Re-running with the same LOG_DIR resumes.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from inspect_ai import eval_set, task_with

from ema.memory_conditions import ALL_CONDITIONS
from ema.tasks.memory_lcb import memory_lcb

COMPOSE = Path(__file__).resolve().parents[2] / "sandbox" / "compose.yaml"
MAX_ATTEMPTS = 10
# Temperature is not settable on current Claude models (the API rejects it).
# Thinking is turned off to match the non-thinking Qwen arm.
GENERATE = {"max_tokens": 2048, "reasoning_effort": "none"}
TOKEN_LIMIT = 300_000  # per-sample safety cap on total tokens
PHASES = {
    "pilot": {"conditions": ("A", "C"), "splits": {"oneoff": 1}, "limit": 20},
    "confirmatory": {"conditions": ALL_CONDITIONS, "splits": {"oneoff": 3, "original": 1}, "limit": None},
}


def build_tasks(phase: str, limit: int | None = None, sandbox=("docker", str(COMPOSE))):
    spec = PHASES[phase]
    n = limit if limit is not None else spec["limit"]
    return [
        task_with(
            memory_lcb(condition=c, split=split, limit=n, max_attempts=MAX_ATTEMPTS, epochs=epochs),
            sandbox=sandbox,
            token_limit=TOKEN_LIMIT,
        )
        for split, epochs in spec["splits"].items()
        for c in spec["conditions"]
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=PHASES)
    parser.add_argument("log_dir")
    parser.add_argument("--model", required=True)
    parser.add_argument("--limit", type=int, default=None, help="smoke tests only")
    parser.add_argument("--max-connections", type=int, default=8)
    args = parser.parse_args()
    tasks = build_tasks(args.phase, args.limit)
    ok, _ = eval_set(
        tasks,
        model=args.model,
        log_dir=args.log_dir,
        max_connections=args.max_connections,
        max_tasks=len(tasks),
        max_sandboxes=8,
        fail_on_error=False,
        log_buffer=5,
        display="plain",
        **GENERATE,
    )
    print("EVAL SET COMPLETE" if ok else "EVAL SET INCOMPLETE")


if __name__ == "__main__":
    main()
