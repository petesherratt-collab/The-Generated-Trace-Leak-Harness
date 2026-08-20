# Swarm Discrimination-Collapse Simulation (V4)

A provenance-explicit Monte Carlo model of the "aggregation penalty" in multi-agent
LLM systems: when many *apparent* sources are clones of a single hidden origin, a
planner that aggregates worker votes treats correlated errors as independent
corroboration, and loses discrimination without any operational symptom.

This sits alongside the CCC work in this repository rather than apart from it. CCC
found that models accept conclusions embedded in rich context; this asks what
happens when a swarm of such models cross-checks each other against evidence whose
apparent diversity overstates its evidential independence.

## Dependencies

- `numpy`
- `pandas`
- `matplotlib`
- `scipy` — a **hard** requirement, not optional. `norm_inv` uses
  `scipy.special.erfinv`; the previous Acklam rational approximation was accurate
  in the body of the distribution but degraded in the tails, which is exactly where
  the near-floor d′ values in this sweep live. Failing loudly beats a quietly bad
  tail approximation.

```
pip install numpy pandas scipy matplotlib
```

## Files

- `v4_simulation.py` — the core Monte Carlo simulation and the parameter sweep.
- `plot_v4.py` — aggregates over replicates and generates the provenance-response
  and gap curves. (Not "phase boundary": with four root values and no defined
  transition threshold, nothing here identifies a phase.) Note the
  `groupby(...).agg(["mean", "std"])`: plotting the raw rows draws a sawtooth
  through the 5 replicates at each x, not a mean curve. Lines are means over the
  5 replicates and bands are ±1 SD across them — dispersion, not confidence
  intervals.
- `analysis_tables.py` — prints every number quoted in `walkthrough.md`, so the
  claims can be audited against the sweep rather than read off the charts.
- `test_v4.py` — 17 self-checks, no test framework required. Run it directly.
- `v4_sweep.csv` — the generated sweep dataset (4 qualities × 4 root counts ×
  3 verify rates × 3 policies × 5 replicates, 1000 tasks each).
- `walkthrough.md` — the analysis, claims, and figures.

## What changed from V3

V3's `coherence` was an abstract shared-noise fraction. V4 makes the mechanism
explicit: each task presents N apparent sources mapping onto M hidden provenance
roots, with genuine evidence always at M = N and poisoned evidence swept from
M = N down to M = 1.

V4 also **retracts** V3's "verification backfire" prediction, which does not
survive the explicit model. See §3 of the walkthrough.

## Built-in checks

```
python3 test_v4.py
```

`v4_simulation.py` **asserts** the common-random-numbers identity on every
execution: at `poison_roots = 10` the treatment must reproduce its matched
baseline exactly. If the CRN pairing breaks, every contrast in the sweep is
confounded, so the run must fail rather than write a CSV that looks fine.

`test_v4.py` covers two layers. The estimators: AUROC at perfect separation (1.0),
reversed separation (0.0), all values tied (0.5) and partial ties (0.875); the
log-linear rate correction distinguished from the Laplace add-one it is often
mistaken for; d′ at chance. And the structural properties the walkthrough's claims
rest on — CRN identity, latency invariance to `poison_roots`, worker d′ flat in M
and monotone in quality, and the M = 1 identity between `different` and `same` on
the poisoned class.

These check that the model does what it is documented to do. They do not, and
cannot, check that it says anything true about real swarms.

## A note on "silent"

The headline result is that discrimination falls while commit rate rises and
matched latency is unchanged. Read that as scoped: **none of the three operational
metrics this model measures reports the attack**, and the two that move, move in
the reassuring direction. The latency null in particular is invariant *by
construction* — verification cost depends only on `verify_rate`, never on
provenance structure — and is asserted as such in `test_v4.py` so it is never
quoted as an empirical finding. Detection signals outside the model (output drift,
source-overlap auditing, provenance attestation, cross-run disagreement) are not
evaluated here and may well catch it.

## Status

This is a mechanism model producing testable predictions, **not** an empirical
finding about real LLM swarms. The model is constructed so that consolidating
provenance reduces the information in N votes, so it cannot fail to produce an
aggregation penalty. Where real workers sit on the roots axis is the open
empirical question.
