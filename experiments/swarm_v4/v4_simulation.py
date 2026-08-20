"""
Swarm discrimination-collapse simulation (v4).

Change from v3: `coherence` was an abstract shared-noise fraction. Here the
mechanism is explicit. Each task presents N APPARENT sources. Those sources
map onto M HIDDEN PROVENANCE ROOTS. Genuine evidence always has M = N (truly
independent origins). Poisoned evidence has M = `poison_roots`, swept from N
down to 1, so that many apparent sources are clones of one false narrative.

    signal[j] = mu(veracity) + provenance[root(j)] + worker_noise[j]

Verification policies model what a worker actually does when it cross-checks:
    'same'        -- re-read the same apparent source (always same provenance)
    'different'   -- read another apparent source; under low poison_roots this
                     usually lands on the SAME hidden provenance anyway.
                     (the realistic web-search / RAG failure mode)
    'independent' -- force a draw from a genuinely independent root
                     (idealised provenance-aware quarantine)

Baselines are matched: identical poison_quality, verify_rate, verify_policy
and identical random draws (CRN), differing ONLY in poison_roots = N.
"""

from dataclasses import dataclass
from typing import Dict, List
import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
# estimators
# ----------------------------------------------------------------------------

def laplace_rate(k: int, n: int) -> float:
    """p_hat = (k + 0.5) / (n + 1). Handles 0-hit / 0-FA without clipping."""
    return (k + 0.5) / (n + 1.0)


def norm_inv(p: float) -> float:
    """Inverse normal CDF. scipy is a hard requirement: the old Acklam
    fallback was accurate to ~1e-9 in the body but degraded in the tails,
    which is exactly where near-floor d' values live. Fail loudly instead."""
    from scipy.special import erfinv
    return float(np.sqrt(2.0) * erfinv(2.0 * p - 1.0))


def d_prime(hit: float, fa: float) -> float:
    return norm_inv(hit) - norm_inv(fa)


def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUROC. labels: True = genuine (positive class)."""
    pos = scores[labels]
    neg = scores[~labels]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order), dtype=float)
    ranks[order] = np.arange(1, len(order) + 1)
    # average ranks for ties
    allv = np.concatenate([pos, neg])[order]
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    r_pos = ranks[:len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


# ----------------------------------------------------------------------------
# configuration
# ----------------------------------------------------------------------------

@dataclass
class Config:
    # environment
    poison_density: float = 0.5
    poison_quality: float = 0.4      # 0 = crude decoy, 1 = indistinguishable
    poison_roots: int = 10           # M for poisoned tasks; N = independent
    # swarm
    n_workers: int = 10              # also N apparent sources
    verify_rate: float = 0.0
    verify_policy: str = "different"  # same | different | independent
    verify_cost: float = 1.0
    planner_margin: float = 0.6
    # signal structure
    mu_true: float = 1.0
    sigma: float = 1.0
    provenance_share: float = 0.7    # fraction of signal variance owned by the source
    # experiment
    n_tasks: int = 1000

    @property
    def mu_false(self) -> float:
        return -1.0 + 2.0 * self.poison_quality

    @property
    def criterion(self) -> float:
        return 0.5 * (self.mu_true + self.mu_false)

    @property
    def sigma_prov(self) -> float:
        return self.sigma * np.sqrt(self.provenance_share)

    @property
    def sigma_ind(self) -> float:
        return self.sigma * np.sqrt(1.0 - self.provenance_share)


# ----------------------------------------------------------------------------
# common random numbers
# ----------------------------------------------------------------------------

class Draws:
    """Pre-generated randomness shared between baseline and treatment runs."""

    def __init__(self, cfg: Config, seed: int):
        rng = np.random.default_rng(seed)
        T, N = cfg.n_tasks, cfg.n_workers
        self.is_genuine = rng.random(T) > cfg.poison_density
        # one provenance draw per (task, potential root) -- indexed by root id
        self.prov = rng.standard_normal((T, N))
        self.prov_extra = rng.standard_normal((T, N))   # for 'independent' policy
        self.noise1 = rng.standard_normal((T, N))
        self.noise2 = rng.standard_normal((T, N))
        self.do_verify = rng.random((T, N))

        # a strictly different apparent source: offset in [1, N-1] can never
        # return the worker's own source, which would silently dilute the
        # 'different' policy into 'same'.
        offset = rng.integers(1, N, size=(T, N))
        worker_source = np.arange(N)[None, :]
        self.alt_source = (worker_source + offset) % N


# ----------------------------------------------------------------------------
# core
# ----------------------------------------------------------------------------

def run(cfg: Config, draws: Draws) -> Dict:
    T, N = cfg.n_tasks, cfg.n_workers
    gen = draws.is_genuine
    mu = np.where(gen, cfg.mu_true, cfg.mu_false)[:, None]      # (T,1)

    # root(j): genuine tasks always have N independent roots.
    # poisoned tasks fold N apparent sources onto `poison_roots` hidden roots.
    src = np.arange(N)[None, :].repeat(T, axis=0)               # (T,N)
    roots_poison = src % max(cfg.poison_roots, 1)
    root_of = np.where(gen[:, None], src, roots_poison)         # (T,N)

    prov = np.take_along_axis(draws.prov, root_of, axis=1) * cfg.sigma_prov
    signal = mu + prov + draws.noise1 * cfg.sigma_ind

    # --- verification -------------------------------------------------------
    verifying = draws.do_verify < cfg.verify_rate               # (T,N)
    if cfg.verify_rate > 0.0:
        if cfg.verify_policy == "same":
            prov2 = prov
        elif cfg.verify_policy == "different":
            alt_root = np.take_along_axis(root_of, draws.alt_source, axis=1)
            prov2 = np.take_along_axis(draws.prov, alt_root, axis=1) * cfg.sigma_prov
        elif cfg.verify_policy == "independent":
            # a genuinely fresh root, never shared with the poisoned narrative
            prov2 = draws.prov_extra * cfg.sigma_prov
        else:
            raise ValueError(f"unknown verify_policy {cfg.verify_policy!r}")
        second = mu + prov2 + draws.noise2 * cfg.sigma_ind
        signal = np.where(verifying, 0.5 * (signal + second), signal)

    latency = float(verifying.sum()) * cfg.verify_cost / T

    # --- worker decisions ---------------------------------------------------
    accept = signal > cfg.criterion                             # (T,N)
    w_true = np.repeat(gen[:, None], N, axis=1)
    wh = int(accept[w_true].sum()); wn_t = int(w_true.sum())
    wf = int(accept[~w_true].sum()); wn_f = int((~w_true).sum())

    # --- planner ------------------------------------------------------------
    frac = accept.mean(axis=1)                                  # (T,)
    commit_yes = frac >= cfg.planner_margin
    commit_no = (1.0 - frac) >= cfg.planner_margin
    abstain = ~(commit_yes | commit_no)
    planner_accept = commit_yes

    ph = int(planner_accept[gen].sum()); pn_t = int(gen.sum())
    pf = int(planner_accept[~gen].sum()); pn_f = int((~gen).sum())

    wh_r, wf_r = laplace_rate(wh, wn_t), laplace_rate(wf, wn_f)
    ph_r, pf_r = laplace_rate(ph, pn_t), laplace_rate(pf, pn_f)

    return {
        "poison_quality": cfg.poison_quality,
        "poison_roots": cfg.poison_roots,
        "verify_rate": cfg.verify_rate,
        "verify_policy": cfg.verify_policy,
        "worker_p_accept_true": wh_r,
        "worker_p_accept_false": wf_r,
        "worker_D": wh_r - wf_r,
        "worker_dprime": d_prime(wh_r, wf_r),
        "worker_auroc": auroc(signal.ravel(), w_true.ravel()),
        "planner_p_accept_true": ph_r,
        "planner_p_accept_false": pf_r,
        "planner_D": ph_r - pf_r,
        "planner_dprime": d_prime(ph_r, pf_r),
        "planner_auroc": auroc(frac, gen),
        "aggregation_gain": (ph_r - pf_r) - (wh_r - wf_r),
        "commit_rate": float((~abstain).mean()),
        "abstain_rate": float(abstain.mean()),
        "mean_latency": latency,
    }


def sweep(reps: int = 5, n_tasks: int = 1000) -> pd.DataFrame:
    rows: List[Dict] = []
    qualities = [0.0, 0.3, 0.6, 0.9]
    roots = [10, 5, 2, 1]
    verify_rates = [0.0, 0.5, 1.0]
    policies = ["same", "different", "independent"]

    for rep in range(reps):
        for q in qualities:
            for vr in verify_rates:
                for pol in policies:
                    base_cfg = Config(poison_quality=q, verify_rate=vr,
                                      verify_policy=pol, poison_roots=10,
                                      n_tasks=n_tasks)
                    draws = Draws(base_cfg, seed=10_000 + rep)   # CRN
                    base = run(base_cfg, draws)

                    for m in roots:
                        cfg = Config(poison_quality=q, verify_rate=vr,
                                     verify_policy=pol, poison_roots=m,
                                     n_tasks=n_tasks)
                        r = run(cfg, draws)                      # same draws
                        r["rep"] = rep
                        r["planner_D_baseline"] = base["planner_D"]
                        r["planner_D_delta"] = r["planner_D"] - base["planner_D"]
                        r["commit_rate_baseline"] = base["commit_rate"]
                        r["commit_rate_delta"] = r["commit_rate"] - base["commit_rate"]
                        rows.append(r)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = sweep(reps=5, n_tasks=1000)
    df.to_csv("v4_sweep.csv", index=False)

    print("=== TEST: poison_roots=10 must equal matched baseline (CRN) ===")
    ident = df[df.poison_roots == 10]
    print("max |planner_D delta| :", ident.planner_D_delta.abs().max())
    print("max |commit delta|    :", ident.commit_rate_delta.abs().max())

    print("\n=== worker vs planner D, by roots (verify_rate=0) ===")
    v0 = df[(df.verify_rate == 0.0)]
    print(v0.groupby(["poison_quality", "poison_roots"]).agg(
        worker_D=("worker_D", "mean"),
        planner_D=("planner_D", "mean"),
        planner_auroc=("planner_auroc", "mean"),
        agg_gain=("aggregation_gain", "mean"),
        commit=("commit_rate", "mean"),
        abstain=("abstain_rate", "mean"),
    ).round(3).to_string())

    print("\n=== does verification rescue? planner_D by policy (quality=0.6) ===")
    q6 = df[df.poison_quality == 0.6]
    print(q6.pivot_table(index=["poison_roots", "verify_rate"],
                         columns="verify_policy", values="planner_D",
                         aggfunc="mean").round(3).to_string())

    print("\n=== d' vs AUROC agreement (planner) ===")
    sub = df[["planner_dprime", "planner_auroc"]].dropna()
    print("spearman:", sub.corr(method="spearman").iloc[0, 1].round(4))
