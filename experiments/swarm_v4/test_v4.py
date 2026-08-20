"""
Self-checks for the v4 swarm simulation.

Repo convention: no test framework, no dependency beyond what the simulation
already needs. Run it and it either exits 0 or raises.

    python3 test_v4.py

The point of these is narrow. They do not check that the model says anything
true about real swarms -- it cannot, it is a mechanism model. They check that
the properties the walkthrough's claims *rest on* actually hold in the code,
so that a refactor which quietly breaks one of them fails loudly instead of
producing a plausible CSV.
"""

import numpy as np

from v4_simulation import (
    Config, Draws, auroc, d_prime, loglinear_rate, norm_inv, run, sweep,
)

FAILS = []


def check(name, fn):
    try:
        fn()
    except AssertionError as e:
        FAILS.append(f"{name}: {e}")
        print(f"FAIL  {name}\n      {e}")
    else:
        print(f"ok    {name}")


# ---------------------------------------------------------------------------
# estimators
# ---------------------------------------------------------------------------

def test_auroc_perfect_separation():
    scores = np.array([0.0, 1.0, 2.0, 3.0])
    labels = np.array([False, False, True, True])
    assert auroc(scores, labels) == 1.0, auroc(scores, labels)


def test_auroc_reversed_separation():
    scores = np.array([3.0, 2.0, 1.0, 0.0])
    labels = np.array([False, False, True, True])
    assert auroc(scores, labels) == 0.0, auroc(scores, labels)


def test_auroc_all_tied():
    scores = np.ones(8)
    labels = np.array([True] * 3 + [False] * 5)
    # every rank is the mean rank, so the statistic must land exactly on chance
    assert auroc(scores, labels) == 0.5, auroc(scores, labels)


def test_auroc_partial_ties():
    # pos = [1, 2], neg = [0, 1]. Concordant pairs (1,0), (2,0), (2,1) score 1
    # each; the tied pair (1,1) scores 0.5. Total 3.5 / 4 = 0.875.
    scores = np.array([0.0, 1.0, 1.0, 2.0])
    labels = np.array([False, False, True, True])
    assert abs(auroc(scores, labels) - 0.875) < 1e-12, auroc(scores, labels)


def test_auroc_empty_class_is_nan():
    assert np.isnan(auroc(np.array([1.0, 2.0]), np.array([True, True])))


def test_loglinear_rate_is_not_laplace():
    # (k + 0.5) / (n + 1), NOT Laplace add-one (k + 1) / (n + 2)
    assert loglinear_rate(0, 100) == 0.5 / 101.0
    assert loglinear_rate(3, 10) == 3.5 / 11.0
    assert loglinear_rate(0, 100) != 1.0 / 102.0


def test_loglinear_rate_keeps_extremes_off_the_bounds():
    # the whole reason for the correction: 0-hit and all-hit must stay finite
    # under norm_inv, so d' never has to be clipped to an arbitrary floor
    for n in (10, 1000):
        assert 0.0 < loglinear_rate(0, n) < 1.0
        assert 0.0 < loglinear_rate(n, n) < 1.0
        assert np.isfinite(norm_inv(loglinear_rate(0, n)))
        assert np.isfinite(norm_inv(loglinear_rate(n, n)))


def test_d_prime_zero_at_chance_and_monotone():
    assert abs(d_prime(0.5, 0.5)) < 1e-12
    assert d_prime(0.9, 0.1) > d_prime(0.7, 0.3) > 0.0
    assert d_prime(0.1, 0.9) < 0.0


# ---------------------------------------------------------------------------
# properties the walkthrough's claims rest on
# ---------------------------------------------------------------------------

def _matched(poison_roots, **kw):
    cfg = Config(poison_roots=poison_roots, n_tasks=4000, **kw)
    draws = Draws(cfg, seed=99)
    return run(cfg, draws)


def test_crn_identity_at_full_roots():
    """poison_roots = N must reproduce the matched baseline EXACTLY. If this
    drifts, no contrast in the sweep is trustworthy."""
    df = sweep(reps=2, n_tasks=500)
    ident = df[df.poison_roots == 10]
    assert len(ident) > 0, "no poison_roots=10 rows -- sweep grid changed?"
    assert ident.planner_D_delta.abs().max() == 0.0
    assert ident.commit_rate_delta.abs().max() == 0.0


def test_latency_is_invariant_to_roots_by_construction():
    """Guards a claim in the walkthrough. Verification cost depends only on
    verify_rate, never on provenance structure, so the latency null in the
    silent-collapse table is a property of the model and must NOT be reported
    as an empirical finding."""
    for vr in (0.0, 0.5, 1.0):
        a = _matched(10, verify_rate=vr, poison_quality=0.9)["mean_latency"]
        b = _matched(1, verify_rate=vr, poison_quality=0.9)["mean_latency"]
        assert a == b, f"verify_rate={vr}: {a} != {b}"


def test_worker_discrimination_is_flat_in_roots():
    """'Quality degrades workers; roots do not.' Marginal worker d' must be
    invariant in M, because the marginal distribution of a provenance draw does
    not depend on how apparent sources are mapped onto roots."""
    for q in (0.0, 0.3, 0.6, 0.9):
        vals = [_matched(m, poison_quality=q)["worker_dprime"] for m in (10, 5, 2, 1)]
        spread = max(vals) - min(vals)
        assert spread < 0.12, f"quality={q}: worker d' spread {spread:.3f} across roots"


def test_worker_discrimination_falls_in_quality():
    """The other axis: quality must degrade workers, monotonically."""
    vals = [_matched(10, poison_quality=q)["worker_dprime"]
            for q in (0.0, 0.3, 0.6, 0.9)]
    assert all(a > b for a, b in zip(vals, vals[1:])), vals


def test_planner_advantage_falls_as_roots_consolidate():
    """The headline: aggregation gain must shrink as provenance consolidates,
    at fixed worker competence."""
    gains = [_matched(m, poison_quality=0.6)["aggregation_gain"] for m in (10, 5, 2, 1)]
    assert gains[0] > gains[-1], gains


def test_selective_disablement_at_single_root():
    """At M=1 every poisoned apparent source shares the one root, so on
    POISONED tasks 'different' must be bit-identical to 'same'. Any margin
    'different' shows has to come from the genuine class, where M = N always.
    This is the load-bearing decomposition in the walkthrough."""
    kw = dict(poison_quality=0.6, verify_rate=1.0)
    same = _matched(1, verify_policy="same", **kw)
    diff = _matched(1, verify_policy="different", **kw)

    assert diff["planner_p_accept_false"] == same["planner_p_accept_false"], (
        "poisoned-class accept rates must be identical at M=1, got "
        f"{diff['planner_p_accept_false']} vs {same['planner_p_accept_false']}"
    )
    assert diff["worker_p_accept_false"] == same["worker_p_accept_false"]
    assert diff["planner_p_accept_true"] > same["planner_p_accept_true"], (
        "the genuine class is where the whole margin should live"
    )


def test_independent_policy_does_not_leak_the_label():
    """The 'independent' control must supply a fresh provenance root, not an
    oracle. Its poisoned-class accept rate must stay well above zero -- if this
    ever approached zero the positive control would be smuggling in the answer
    and every 'restoration' number would be meaningless."""
    r = _matched(1, poison_quality=0.6, verify_rate=1.0, verify_policy="independent")
    assert r["planner_p_accept_false"] > 0.05, r["planner_p_accept_false"]


def test_unknown_policy_rejected():
    cfg = Config(verify_rate=0.5, verify_policy="nonsense", n_tasks=100)
    try:
        run(cfg, Draws(cfg, seed=1))
    except ValueError:
        return
    raise AssertionError("unknown verify_policy should raise")


def test_alt_source_never_returns_own_source():
    """The 'different' policy silently degrades into 'same' if the alternate
    draw can return the worker's own apparent source."""
    cfg = Config(n_tasks=2000)
    draws = Draws(cfg, seed=7)
    own = np.arange(cfg.n_workers)[None, :]
    assert not (draws.alt_source == own).any()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            check(name, fn)
    print()
    if FAILS:
        raise SystemExit(f"{len(FAILS)} check(s) failed:\n" + "\n".join(FAILS))
    print("all v4 self-checks passed")
