"""H2 pipeline driver.

    python -m ema.h2.run generate STORIES_JSONL MODEL
    python -m ema.h2.run directions STORIES_JSONL MODEL OUT_DIR
    python -m ema.h2.run replay LOG_DIR SPLIT MODEL OUT_DIR [--limit N]

`directions` reads generated stories (one JSON object per line: the request
fields from stories.requests() plus "text") and writes OUT_DIR/directions.npz
and OUT_DIR/validity.json. `replay` writes OUT_DIR/projections_<split>.jsonl
(every direction, every diagnostic layer, every decision token) and
OUT_DIR/residuals_<split>.npy (raw float16 residuals at the frozen layer, so
new directions can be projected later without a GPU).

Layers are fractions of depth, so the same code runs on the small development
model. For Qwen3-4B (36 blocks) the frozen layer is 24.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

FROZEN_FRACTION = 2 / 3
DIAGNOSTIC_FRACTIONS = (1 / 3, 1 / 2, 2 / 3, 5 / 6)
STORY_START = 10  # skip the first tokens of each story when averaging


def layers_for(n_blocks: int) -> tuple[int, list[int]]:
    frozen = round(FROZEN_FRACTION * n_blocks)
    return frozen, sorted({round(f * n_blocks) for f in DIAGNOSTIC_FRACTIONS} | {frozen})


def load_model(name: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    cuda = torch.cuda.is_available()
    model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float16 if cuda else torch.float32,
                                                 device_map="cuda" if cuda else None)
    model.eval()
    return AutoTokenizer.from_pretrained(name), model


def story_activations(tokenizer, model, stories: list[dict], layers: list[int]) -> dict[int, np.ndarray]:
    from ema.h2.activations import residuals
    rows: dict[int, list] = defaultdict(list)
    for st in stories:
        ids = tokenizer(st["text"], add_special_tokens=False)["input_ids"]
        r = residuals(model, ids, layers, start=min(STORY_START, len(ids) - 1))
        for layer in layers:
            rows[layer].append(r[layer][0].numpy())
    return {layer: np.stack(v) for layer, v in rows.items()}


def build_directions(stories: list[dict], acts: dict[int, np.ndarray]) -> tuple[dict, dict]:
    """Directions per layer from training situations, plus held-out validity numbers."""
    from ema.h2.directions import (auroc, family_directions, neutral_basis, random_directions,
                                   task_direction)
    from ema.h2.stories import TEST_SITUATIONS
    test = [st["family"] != "neutral" and st["situation"] in TEST_SITUATIONS for st in stories]
    out, validity = {}, {}
    for layer, a in acts.items():
        def pick(family, label=None, held_out=False):
            return a[[i for i, st in enumerate(stories) if st["family"] == family
                      and (label is None or st["label"] == label) and test[i] == held_out]]
        basis = neutral_basis(pick("neutral"))
        dirs = {}
        for family in ("emotion", "control"):
            labels = sorted({st["label"] for st in stories if st["family"] == family})
            for label, v in family_directions({lb: pick(family, lb) for lb in labels}, basis).items():
                dirs[f"{family}:{label}"] = v
        dirs["task:badly"] = task_direction(pick("task", "going badly"), pick("task", "going well"), basis)
        dirs.update(random_directions(a.shape[1]))
        out[layer] = dirs
        d = dirs["emotion:desperate"]
        others = np.concatenate([pick("emotion", lb, True) for lb in
                                 sorted({st["label"] for st in stories if st["family"] == "emotion"}) if lb != "desperate"])
        validity[layer] = {
            "held_out_auroc_desperate_vs_calm": auroc(pick("emotion", "desperate", True) @ d, pick("emotion", "calm", True) @ d),
            "held_out_auroc_desperate_vs_other_emotions": auroc(pick("emotion", "desperate", True) @ d, others @ d),
            "held_out_auroc_task_badly_vs_well": auroc(pick("task", "going badly", True) @ dirs["task:badly"],
                                                        pick("task", "going well", True) @ dirs["task:badly"]),
            "neutral_pcs_removed": int(basis.shape[0]),
        }
    return out, validity


def cmd_directions(stories_path: str, model_name: str, out_dir: str) -> None:
    stories = [json.loads(line) for line in open(stories_path, encoding="utf-8")]
    tokenizer, model = load_model(model_name)
    frozen, layers = layers_for(len(model.model.layers))
    dirs, validity = build_directions(stories, story_activations(tokenizer, model, stories, layers))
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    np.savez(f"{out_dir}/directions.npz", **{f"L{layer}|{name}": v for layer, d in dirs.items() for name, v in d.items()})
    json.dump({"model": model_name, "frozen_layer": frozen, "layers": layers, "n_stories": len(stories),
               "validity": validity}, open(f"{out_dir}/validity.json", "w"), indent=2)
    print(json.dumps(validity, indent=2))


def load_directions(path: str) -> dict[int, dict[str, np.ndarray]]:
    out: dict[int, dict[str, np.ndarray]] = defaultdict(dict)
    with np.load(path) as z:
        for key in z.files:
            layer, name = key.split("|", 1)
            out[int(layer[1:])][name] = z[key]
    return dict(out)


def cmd_replay(log_dir: str, split: str, model_name: str, out_dir: str, limit: int | None = None) -> None:
    from ema.h2.activations import residuals
    from ema.h2.replay import prepare, samples
    tokenizer, model = load_model(model_name)
    frozen, _ = layers_for(len(model.model.layers))
    dirs = load_directions(f"{out_dir}/directions.npz")
    layers = sorted(dirs)
    raw, row = [], 0
    with open(f"{out_dir}/projections_{split}.jsonl", "w", encoding="utf-8") as f:
        for n, (meta, messages) in enumerate(samples(log_dir, split)):
            if limit is not None and n >= limit:
                break
            ids, pos = prepare(tokenizer, messages)
            r = residuals(model, ids, layers, positions=pos)
            proj = {str(layer): {name: (r[layer].numpy() @ v).tolist() for name, v in dirs[layer].items()}
                    for layer in layers}
            raw.append(r[frozen].numpy().astype(np.float16))
            f.write(json.dumps({**meta, "n_tokens": len(ids), "positions": pos, "row": row, "proj": proj}) + "\n")
            row += len(pos)
    np.save(f"{out_dir}/residuals_{split}.npy", np.concatenate(raw) if raw else np.zeros((0, 0), np.float16))
    print(f"replayed {len(raw)} samples, {row} decision tokens")


def cmd_generate(out_path: str, model_name: str) -> None:
    """Write the stories with vLLM (GPU). Run as its own process so the GPU is freed afterwards."""
    from vllm import LLM, SamplingParams

    from ema.h2.stories import requests
    reqs = requests()
    llm = LLM(model_name, dtype="half", max_model_len=4096, seed=0)
    params = SamplingParams(temperature=0.7, top_p=0.8, max_tokens=300, seed=0)
    outs = llm.chat([r["messages"] for r in reqs], params)
    with open(out_path, "w", encoding="utf-8") as f:
        for r, o in zip(reqs, outs):
            f.write(json.dumps({**{k: v for k, v in r.items() if k != "messages"}, "text": o.outputs[0].text}) + "\n")
    print(f"wrote {len(reqs)} stories")


def main(argv: list[str]) -> None:
    if argv[0] == "generate":
        cmd_generate(*argv[1:3])
    elif argv[0] == "directions":
        cmd_directions(*argv[1:4])
    elif argv[0] == "replay":
        limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
        cmd_replay(*argv[1:5], limit=limit)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
