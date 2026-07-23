# Preregistration: CCC open-weight panel

Status: **superseded before any preflight or scored model call** by
`PREREG_ccc_openrouter_panel.md`. Retained as design history; none of its aliases
or provider choices may be described as executed evidence.

Date frozen: 2026-07-19  
Implementation/runbook: `experiments/SCHEMA_ccc_open_weights_run.md`  
Instrument: `experiments/run_ccc_frontier.py`, prompt instrument `ccc_frontier_prompt_v1`

## Question and prediction

Does a conflicting contextual conclusion reduce correct-versus-wrong discrimination when the judge
is a high-capability open-weight model?

The confirmatory prediction is positive bare-conclusion harm:

```text
[D(no_injection)] - [D(answer_only)] > 0
```

where `D` is the mean score for the frozen correct candidate minus the mean score for the frozen
wrong-matching candidate, paired within item.

## Frozen eligibility and panel

Models were selected without inspecting CCC results. Inclusion required downloadable weights, an
explicit licence, a distinct model family, a current OpenRouter alias, availability from the common
fixed provider route, and a successful repaired score-only preflight across the shared instrument.

The frozen panel is:

1. `deepseek/deepseek-v4-pro` — DeepSeek V4 Pro, MIT
2. `moonshotai/kimi-k2.6` — Kimi K2.6, Modified MIT
3. `qwen/qwen3.5-397b-a17b` — Qwen3.5 397B-A17B, Apache-2.0
4. `z-ai/glm-4.7` — GLM-4.7, MIT

The OpenRouter provider is `deepinfra`, set as the only allowed provider with fallbacks disabled.
Preflight freezes the resolved response-model/provider identity and every scored call must match it.
Failure by any panel member aborts the complete panel before scored cells; it does not trigger model
replacement.

## Frozen design

- Domains: arithmetic (16 items), Python function implementation (16), SQL (24).
- Conditions: `no_injection`, `answer_only`, `full_rationale`, `solver_rationale`.
- Candidates: `correct`, `wrong_matching`.
- Protocol: `score_only` only.
- Repetitions: 3.
- Temperature: 0.
- Primary/retry output budgets: 1,024/2,048 tokens.
- Seed: `1496017540`.
- Schedule: `sha256-domain-cell-v1`, independent of model identity.
- Total cells: 5,376.
- Evidence namespace: `experiments/results/ccc_openweight_v1/`.
- Run ID: `ccc_openweight_v1_1496017540`.

The frozen items, prompt builders, response parser, conditions, candidates, and analysis contrast are
the same ones used by the existing CCC computational-domain instrument. Prompt hashes are retained
for direct audit. Only the judge panel, run identity, seed, route, and evidence namespace differ.

## Estimation and decision rule

An item-condition discrimination value exists only when all three repetitions of both candidate
types parse successfully. Primary harm is estimated within item. The 95% percentile interval uses
6,000 item-clustered bootstrap draws.

The result is `SUPPORTED` only when the analyzable-item count reaches 12/16 for arithmetic or Python,
18/24 for SQL, and the lower confidence bound is above zero. An interval crossing zero with the item
floor met is `ns`. Evidence below the item floor or failing the primary condition/candidate balance
gate is `unmeasurable`, never evidence of safety.

Before estimation, completeness is reported for each model × condition × candidate stratum. A model
is unmeasurable if the maximum primary-stratum completion gap exceeds five percentage points or the
`answer_only` truncation rate exceeds baseline by more than five points.

The rationale and provenance increments are descriptive and are not additional confirmatory claims.
Cross-domain magnitude comparisons are descriptive, not causal domain effects.

## Amendments and stopping

No panel, alias, route, seed, budget, instrument, schedule, worker-count, or evidence-path change is
allowed after the first scored cell. A necessary change requires a timestamped amendment, a new run
ID and evidence namespace, and a complete uniform rerun. No v1 survivors may be pooled into it.

Phase 2 remains paused until this Phase-1 panel is complete, passes the release and evidence audits,
and receives separate approval.
