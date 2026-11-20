"""Replay logged transcripts and read the residual stream at decision tokens.

A decision token is the last token of the generation prompt before each
assistant turn: the newline after "<|im_start|>assistant". That is the
position from which the model wrote each submission. Transcripts are
re-rendered with the model's chat template and re-tokenised; the logs keep
the text, not vLLM's sampled token ids.

Sample selection matches the frozen ema.stats: per task (condition), the
newest successful log of the split, skipping errored samples.
"""

from __future__ import annotations

from inspect_ai.log import list_eval_logs, read_eval_log

from ema.stats import PASS_SCORER


def latest_logs(log_dir: str, split: str) -> list:
    latest = {}
    for info in list_eval_logs(log_dir):
        log = read_eval_log(info)
        meta = log.eval.metadata or {}
        if log.status != "success" or meta.get("split") != split or not log.samples:
            continue
        if log.eval.task not in latest or log.eval.created > latest[log.eval.task].eval.created:
            latest[log.eval.task] = log
    return sorted(latest.values(), key=lambda lg: lg.eval.metadata["condition"])


def samples(log_dir: str, split: str):
    """Yield (meta dict, chat messages) for every scored, error-free sample."""
    for log in latest_logs(log_dir, split):
        cond = log.eval.metadata["condition"]
        for s in log.samples:
            if s.error or PASS_SCORER not in (s.scores or {}):
                continue
            meta = {"task_id": str(s.id), "condition": cond, "epoch": s.epoch, "split": split,
                    "passed": s.scores[PASS_SCORER].value == "C"}
            yield meta, [{"role": m.role, "content": m.text} for m in s.messages]


def render(tokenizer, messages: list[dict], add_generation_prompt: bool = False) -> list[int]:
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=add_generation_prompt)
    return tokenizer(text, add_special_tokens=False)["input_ids"]


def decision_positions(tokenizer, ids: list[int]) -> list[int]:
    """Index of the token after which each assistant turn begins."""
    prefix = [tokenizer.convert_tokens_to_ids("<|im_start|>")] + tokenizer.encode("assistant\n", add_special_tokens=False)
    n = len(prefix)
    return [i + n - 1 for i in range(len(ids) - n + 1) if ids[i:i + n] == prefix]


def prepare(tokenizer, messages: list[dict]) -> tuple[list[int], list[int]]:
    """Token ids of the whole transcript and its decision positions (one per assistant turn)."""
    ids = render(tokenizer, messages)
    pos = decision_positions(tokenizer, ids)
    n_assistant = sum(m["role"] == "assistant" for m in messages)
    if len(pos) != n_assistant:
        raise ValueError(f"found {len(pos)} decision tokens for {n_assistant} assistant turns")
    return ids, pos
