from pathlib import Path

import numpy as np
import pytest

from ema.h2.directions import auroc, family_directions, neutral_basis, random_directions
from ema.h2.run import layers_for
from ema.h2.stats_h2 import CONFIRMATORY, per_task
from ema.h2.stories import EMOTIONS, TEST_SITUATIONS, requests

PILOT_LOGS = str(Path(__file__).parent.parent / "results" / "logs")


def test_story_requests():
    reqs = requests()
    assert len(reqs) == (12 + 6 + 2) * 20 * 3 + 25 * 3
    assert "desperate" in EMOTIONS and "calm" in EMOTIONS
    for r in reqs:
        text = r["messages"][1]["content"].lower()
        assert "test" not in text.replace("tests", "") and "code" not in text
    assert set(TEST_SITUATIONS) == {15, 16, 17, 18, 19}


def test_layers_for_qwen3_4b():
    assert layers_for(36) == (24, [12, 18, 24, 30])


def test_directions_are_unit_and_orthogonal_to_neutral_pcs():
    rng = np.random.default_rng(1)
    d = 32
    neutral = rng.standard_normal((50, d)) * np.linspace(5, 0.1, d)
    basis = neutral_basis(neutral)
    acts = {k: rng.standard_normal((20, d)) + i for i, k in enumerate("abc")}
    dirs = family_directions(acts, basis)
    for v in dirs.values():
        assert abs(np.linalg.norm(v) - 1) < 1e-9
        assert np.abs(basis @ v).max() < 1e-9
    r1, r2 = random_directions(d), random_directions(d)
    assert all(np.array_equal(r1[k], r2[k]) for k in r1)


def test_auroc():
    assert auroc([2, 3], [0, 1]) == 1.0
    assert auroc([0, 1], [2, 3]) == 0.0
    assert auroc([1], [1]) == 0.5


def test_residuals_match_hidden_states_and_stop_early():
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    from ema.h2.activations import residuals
    cfg = transformers.Qwen3Config(vocab_size=100, hidden_size=32, intermediate_size=64, num_hidden_layers=6,
                                   num_attention_heads=4, num_key_value_heads=2, head_dim=8)
    torch.manual_seed(0)
    model = transformers.Qwen3ForCausalLM(cfg).eval()
    ids = [5, 17, 3, 99, 42, 8, 11]
    with torch.no_grad():
        hs = model(torch.tensor([ids]), output_hidden_states=True).hidden_states
    r = residuals(model, ids, [2, 4], positions=[1, 6])
    assert torch.allclose(r[2], hs[2][0, [1, 6]], atol=1e-5)
    assert torch.allclose(r[4], hs[4][0, [1, 6]], atol=1e-5)
    m = residuals(model, ids, [3], start=2)
    assert torch.allclose(m[3][0], hs[3][0, 2:].mean(0), atol=1e-5)
    calls = []
    h = model.model.layers[5].register_forward_hook(lambda *a: calls.append(1))
    residuals(model, ids, [2])
    h.remove()
    assert calls == []  # blocks after the deepest requested layer never run


def _records(shift):
    rng = np.random.default_rng(0)
    out = []
    names = ["emotion:desperate", "emotion:calm", "task:badly"] + [f"control:{i}" for i in range(6)] + [f"random_{i}" for i in range(6)]
    for cond in "BCD":
        for t in range(30):
            for e in (1, 2, 3):
                proj = {n: list(rng.standard_normal(4)) for n in names}
                if cond == "C":
                    proj["emotion:desperate"] = [x + shift for x in proj["emotion:desperate"]]
                out.append({"condition": cond, "task_id": f"t{t}", "epoch": e, "proj": {"24": proj}})
    return out


def test_h2_statistic_detects_a_desperate_only_shift():
    from ema.stats import compare
    scores = per_task(_records(1.0), "24")
    hi, lo = CONFIRMATORY["H2"]
    r = compare(scores, hi, lo)
    assert r["diff"] > 0.5 and r["p"] < 0.001
    null = compare(per_task(_records(0.0), "24"), hi, lo)
    assert null["p"] > 0.05


def test_turn_count_alone_does_not_make_h2_positive():
    """C fails more (more turns); every turn after the first scores higher; no condition effect."""
    from ema.stats import compare
    rng = np.random.default_rng(0)
    names = ["emotion:desperate"] + [f"control:{i}" for i in range(6)] + [f"random_{i}" for i in range(6)]
    records = []
    for cond, n_turns in (("B", 2), ("C", 6)):
        for t in range(30):
            for e in (1, 2, 3):
                proj = {n: list(rng.standard_normal(n_turns) * 0.3) for n in names}
                proj["emotion:desperate"] = [x + (0.0 if i == 0 else 2.0) for i, x in enumerate(proj["emotion:desperate"])]
                records.append({"condition": cond, "task_id": f"t{t}", "epoch": e, "proj": {"24": proj}})
    from ema.h2.stats_h2 import token_scores
    raw = {c: {} for c in "BC"}
    for r, s in zip(records, token_scores(records, "24")):
        raw[r["condition"]].setdefault(r["task_id"], []).append(s.mean())
    raw = {c: {t: float(np.mean(v)) for t, v in d.items()} for c, d in raw.items()}
    assert compare(raw, "C", "B")["p"] < 0.001  # the confound the adjustment removes
    assert compare(per_task(records, "24"), "C", "B")["p"] > 0.05


@pytest.mark.network
def test_decision_positions_match_generation_prompts():
    transformers = pytest.importorskip("transformers")
    from ema.h2.replay import prepare, render, samples
    tok = transformers.AutoTokenizer.from_pretrained("Qwen/Qwen3-4B-Instruct-2507")
    n = 0
    for _meta, messages in samples(PILOT_LOGS, "oneoff"):
        ids, pos = prepare(tok, messages)
        for p, i in zip(pos, [i for i, m in enumerate(messages) if m["role"] == "assistant"]):
            assert ids[:p + 1] == render(tok, messages[:i], add_generation_prompt=True)
        n += 1
        if n == 5:
            break
    assert n == 5
