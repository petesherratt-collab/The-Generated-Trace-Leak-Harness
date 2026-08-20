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
- `plot_v4.py` — aggregates over replicates and generates the phase-boundary and
  gap figures. Note the `groupby(...).agg(["mean", "std"])`: plotting the raw rows
  draws a sawtooth through the 5 replicates at each x, not a mean curve.
- `analysis_tables.py` — prints every number quoted in `walkthrough.md`, so the
  claims can be audited against the sweep rather than read off the charts.
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

`v4_simulation.py` runs a common-random-numbers identity test on every execution:
at `poison_roots = 10` the treatment must reproduce its matched baseline exactly
(`max |planner_D delta| = 0.0`). If that ever prints non-zero, the CRN pairing has
been broken and no contrast in the sweep is trustworthy.

## Status

This is a mechanism model producing testable predictions, **not** an empirical
finding about real LLM swarms. The model is constructed so that consolidating
provenance reduces the information in N votes, so it cannot fail to produce an
aggregation penalty. Where real workers sit on the roots axis is the open
empirical question.
