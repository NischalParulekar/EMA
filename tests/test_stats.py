import math

from ema.stats import bootstrap_ci, compare, holm, sign_flip_test


def test_sign_flip_no_effect_is_not_significant():
    diffs = [0.3, -0.3, 0.0, 0.0, 1 / 3, -1 / 3] * 10
    assert sign_flip_test(diffs) > 0.5


def test_sign_flip_consistent_effect_is_significant():
    diffs = [1 / 3] * 15 + [0.0] * 85
    assert sign_flip_test(diffs) < 0.001


def test_sign_flip_matches_exact_small_case():
    # 3 nonzero diffs all positive: exact two-sided p = 2/8 = 0.25.
    p = sign_flip_test([1.0, 1.0, 1.0], n_perm=20_000)
    assert abs(p - 0.25) < 0.02


def test_holm_adjustment():
    adj = holm({"H1": 0.01, "H3": 0.04})
    assert math.isclose(adj["H1"], 0.02) and math.isclose(adj["H3"], 0.04)
    adj = holm({"H1": 0.03, "H3": 0.02})
    assert math.isclose(adj["H3"], 0.04) and math.isclose(adj["H1"], 0.04)  # monotone


def test_bootstrap_ci_contains_mean():
    diffs = [0.0, 1.0] * 50
    lo, hi = bootstrap_ci(diffs)
    assert lo < 0.5 < hi and hi - lo < 0.3


def test_compare_pairs_only_shared_tasks():
    rates = {"C": {"t1": 1.0, "t2": 0.0, "t3": 1.0}, "B": {"t1": 0.0, "t2": 0.0}}
    r = compare(rates, "C", "B")
    assert r["n_tasks"] == 2 and math.isclose(r["diff"], 0.5)


def test_holm_keeps_missing_as_nan():
    adj = holm({"H1": float("nan"), "H3": 0.02})
    assert math.isnan(adj["H1"]) and math.isclose(adj["H3"], 0.02)
