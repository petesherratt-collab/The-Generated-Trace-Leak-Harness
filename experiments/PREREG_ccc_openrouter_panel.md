# Preregistration: CCC OpenRouter open-ecosystem panel

Status: frozen on 2026-07-21 before any preflight or scored call for this panel.

Instrument: `experiments/run_ccc_frontier.py` (`ccc_frontier_prompt_v1`)  
Launcher: `experiments/run_ccc_openweight.ps1`  
Seed: `1496017540`

## Question and prediction

Does a conflicting contextual conclusion reduce correct-versus-wrong discrimination
when the judge comes from the current open-model ecosystem?

The confirmatory prediction for every model-domain pair is positive bare-conclusion harm:

```text
D(no_injection) - D(answer_only) > 0
```

`D` is correct-candidate mean score minus wrong-matching-candidate mean score,
paired within frozen item. The oracle, not the model, establishes correctness.

## Frozen panel and classification

| order | OpenRouter ID | route | classification |
|---:|---|---|---|
| 1 | `minimax/minimax-m3` | `deepinfra` | downloadable weights; MiniMax Community licence |
| 2 | `qwen/qwen3.7-plus` | `alibaba` | hosted comparator; no public weights |
| 3 | `z-ai/glm-5.2` | `deepinfra` | downloadable weights; MIT |
| 4 | `moonshotai/kimi-k2.7-code` | `together` | downloadable weights; Modified MIT |

The study is therefore an **open-ecosystem panel with one hosted comparator**, not a
claim that all four models are open-weight. No model may be replaced after the first
preflight call. The hosted Qwen result must remain labelled as such in every table.

Each request restricts OpenRouter to its listed provider, disables provider fallbacks,
and requires parameter support. Preflight freezes the returned response-model and
provider identity; every scored call must match it. `alibaba` is the OpenRouter route
slug whose response display name is `Alibaba Cloud Int.`.

## Frozen design

- Domains: arithmetic (16 items), Python function implementation (16), SQL (24).
- Conditions: `no_injection`, `answer_only`, `full_rationale`, `solver_rationale`.
- Candidates: `correct`, `wrong_matching`.
- Protocol: `score_only` only.
- Repetitions: 3; temperature: 0.
- Primary/retry output budgets: 1,024/2,048 tokens.
- Schedule: `sha256-domain-cell-v2`, independent of model identity.
- Balance gate: maximum five-percentage-point primary-stratum completion,
  truncation, or content-filter difference.
- Item floor: arithmetic/code 12 of 16; SQL 18 of 24.

Each model is a separate immutable 1,344-cell block (384 arithmetic, 384 code,
576 SQL), with its own metadata, prompt manifests, observations, run ID, and
completion audit. The full frozen panel is 5,376 scored cells.

Blocks run sequentially in the table order. Inspecting cost and missingness between
blocks is allowed, but it cannot change the panel, hypotheses, thresholds, budgets,
or routes. A block may be paused for cost or operational reasons; completed blocks
remain individually reportable, while a four-model panel-wide claim requires all four.

## Estimation and decision rule

An item-condition discrimination exists only when all three repetitions of both
candidate types parse successfully. The 95% interval uses 6,000 seeded,
item-clustered bootstrap draws.

A model-domain result is `SUPPORTED` only when the analyzable-item floor is met,
the primary balance gate passes, and the lower interval bound is above zero. An
interval covering zero is `ns`, not proof of immunity. A failed balance or item-floor
gate is `unmeasurable`, never evidence of safety.

Provenance and rationale increments are descriptive. Cross-model and cross-domain
magnitude comparisons are descriptive, not causal effects of architecture, licence,
provider, nationality, or openness.

## Evidence namespaces

All artifacts live under `experiments/results/ccc_openrouter_v1/` with one prefix:

```text
ccc_openrouter_v1_minimax_m3_b8192
ccc_openrouter_v1_qwen37_plus_hosted_bounded
ccc_openrouter_v1_glm52_bounded
ccc_openrouter_v1_kimi_k27_code_together_bounded
```

`--run` refuses to overwrite existing evidence. `--resume` requires an exact
configuration hash and unchanged endpoint identity. Attempts retain raw output,
finish reason, usage, transport history, requested and resolved endpoint identity,
and prompt SHA-256. The prompt manifests are part of the evidence, not disposable.

## Cost and stopping discipline

Public catalogue prices were inspected on 2026-07-21, but live billing and reasoning
length can change. Offline prompt construction totals approximately 1.18 million
input tokens for the complete four-model panel; output/reasoning is the main unknown.
MiniMax runs first to establish observed usage. Kimi runs last because it always
uses thinking mode and has the highest listed output price in this panel.

Do not begin or resume a block if preflight cannot emit a parseable score, the
provider/model identity differs, a release gate fails, evidence exists under a
different configuration, or the operator withdraws cost approval. A necessary
instrument, panel, route, seed, budget, or namespace change requires a dated
amendment and a fresh run ID before further scored calls.

Phase 2 (`verify_written`) is not authorized here. It requires a separate decision
after the score-only evidence is complete and audited.

## Amendment 1 — Kimi provider capacity (2026-07-21, before scored cells)

The frozen `moonshotai/kimi-k2.7-code` preflight on DeepInfra failed closed after
both judge attempts: every underlying transport attempt returned HTTP 429. MiniMax,
Qwen, and GLM preflights passed; no scored experiment cell for any model had begun.

Kimi alone is moved to its official `moonshotai` OpenRouter provider. The Kimi run
uses the fresh prefix/run ID suffix `kimi_k27_code_moonshot`; the failed DeepInfra
preflight produced no evidence namespace and is not pooled. Model, prompts, domains,
conditions, candidates, seed, repetitions, budgets, balance rule, and analysis are
unchanged. This is an operational endpoint-capacity amendment, not a response to a
CCC result.

## Amendment 2 — Kimi route-slug correction (2026-07-21, before scored cells)

The attempted official-provider route `moonshotai` returned HTTP 404 from the
OpenRouter routing API. It emitted no response and no scored cell. The catalogue
lists Together as an active Kimi K2.7 Code endpoint, so Kimi moves to the fixed
`together` route with fresh suffix `kimi_k27_code_together`. Fallbacks remain
disabled. All scientific settings remain unchanged, and neither failed route is
pooled with the eventual evidence.

## Amendment 3 — MiniMax long-tail reasoning budget (2026-07-21)

The first MiniMax block was stopped after 83 arithmetic rows and is void for
inference. It contains 77 successes and six `truncated_no_score` failures; every
failure used the full 1,024-token attempt and full 2,048-token retry. All six were
in injected conditions (answer-only 3, solver-rationale 2, full-rationale 1) and
none were baseline, already creating treatment-skewed missingness. Recorded API
cost was $0.094844. No code or SQL cell had begun.

Those diagnostic files retain prefix `ccc_openrouter_v1_minimax_m3` and are never
resumed or pooled. MiniMax restarts uniformly from zero with the unchanged
1,024-token primary budget and a 4,096-token retry under fresh prefix
`ccc_openrouter_v1_minimax_m3_b4096`. Output headroom is the only change; model,
route, prompts, domains, conditions, candidates, seed, repetitions, temperature,
balance gate, and analysis remain unchanged. Other panel members retain their
1,024/2,048 budgets unless a separately documented pre-score diagnostic requires
a fresh namespace.

## Amendment 4 — MiniMax second long-tail budget diagnostic (2026-07-21)

The complete arithmetic domain under the 1,024/4,096 budget still failed the
frozen completion-balance gate and is void for inference. Of 384 arithmetic cells,
367 parsed and 17 exhausted both attempts as `truncated_no_score`. Across the four
primary strata, completion was 95.8% (baseline/correct), 100% (baseline/wrong),
89.6% (answer-only/correct), and 91.7% (answer-only/wrong): a 10.4-percentage-point
gap against the five-point limit. Injected primary truncation was 9.4% versus 2.1%
at baseline, a 7.3-point difference. The launcher entered the next domain before
the stop was observed, so 15 successful code cells are also quarantined. Total
recorded cost for the namespace was $0.470733.

The diagnostic files retain prefix `ccc_openrouter_v1_minimax_m3_b4096` and are
never resumed or pooled. MiniMax restarts from zero under fresh prefix
`ccc_openrouter_v1_minimax_m3_b8192`, with the retry ceiling raised to 8,192 tokens.
The primary ceiling remains 1,024. Model, route, prompts, domains, conditions,
candidates, seed, repetitions, temperature, balance gate, and analysis remain
unchanged.

## Amendment 5 — MiniMax 8,192 ceiling stopped; model deferred (2026-07-21)

The 1,024/8,192 MiniMax restart was stopped after 159 arithmetic rows, before any
code or SQL cell. It contains 153 parsed scores and six `truncated_no_score`
failures, all in answer-only: four correct-candidate and two wrong-candidate cells.
Three correct-candidate failures alone imply at least 6.25% missingness in that
48-cell primary stratum even if all remaining cells succeed, and five injected
failures already imply more than a five-point injected-versus-baseline truncation
gap. Two additional in-flight rows settled during termination, leaving the final
diagnostic counts at four and two. Recorded attempt cost was $0.212743.

Prefix `ccc_openrouter_v1_minimax_m3_b8192` is void and never resumed or pooled.
MiniMax is deferred rather than escalated to another unrestricted token ceiling:
the repeated output loops show that a structured-output protocol must first be
validated in a separately documented diagnostic. Qwen, GLM, and Kimi retain their
frozen configurations and may proceed independently; MiniMax's absence does not
alter their within-model estimates.

## Amendment 6 — explicit reasoning and structured-output bounds (2026-07-21)

The original Qwen namespace completed all 384 arithmetic cells without a missing
score, then was stopped at 205/384 code cells. One `rpn_eval` full-rationale/wrong
cell exhausted both visible-output attempts. Crucially, its usage showed 27,751
completion tokens on the nominal 1,024-token attempt and 83,973 on the nominal
2,048-token retry, because Alibaba counted hidden reasoning outside the visible
completion ceilings. Four subsequent calls remained in continuous generation for
more than five minutes; a socket-idle timeout did not impose a total wall-clock or
billing bound. The process was terminated before SQL. Recorded cost was $0.693112
for arithmetic and $0.776602 for partial code, $1.469713 total.

Prefix `ccc_openrouter_v1_qwen37_plus_hosted` is void in full, including its
complete arithmetic domain, and is never resumed or pooled. Retaining arithmetic
while replacing code after observing domain-specific behavior would mix request
policies and invite post-hoc selection.

Before any scored GLM or Kimi cell, the remaining active panel receives two frozen
request controls supported by OpenRouter:

- strict JSON Schema output requiring exactly one numeric `score` in [0,100];
- explicit reasoning control, excluded from the returned body but still audited in
  usage: `reasoning.max_tokens=2048` for Qwen and Kimi, and `reasoning.effort=high`
  for GLM (the lowest effort that model advertises).

Provider routing still requires these parameters and disables fallback. Visible
primary/retry ceilings remain 1,024/2,048. Qwen restarts from zero under fresh
prefix `ccc_openrouter_v1_qwen37_plus_hosted_bounded`; GLM and Kimi use fresh
prefixes `ccc_openrouter_v1_glm52_bounded` and
`ccc_openrouter_v1_kimi_k27_code_together_bounded`. Model, provider, prompts,
domains, conditions, candidates, seed, repetitions, temperature, balance gate,
and analysis remain unchanged. MiniMax remains deferred under Amendment 5; if it
is revisited it must use a fresh structured, reasoning-bounded namespace.

## Amendment 7 — GLM preflight timing attribution corrected (2026-07-21, before scored cells)

The bounded GLM compatibility preflight used the pinned DeepInfra route, strict
score schema, 1,024 visible-token ceiling, and `reasoning.effort=high`, the lowest
effort advertised by GLM 5.2. It returned a parseable, identity-matched score. An
initial operator note incorrectly attributed approximately 55 minutes of tool wall
time to the API call; that interval included the interactive permission wait. Once
permission was granted, the command completed in approximately 18 seconds. No
scored GLM cell or evidence namespace had begun when the attribution was corrected.

The preflight is repeated once with explicit usage/cost reporting added to the
runner. GLM may proceed under `ccc_openrouter_v1_glm52_bounded` only if that live
record shows a normal bounded response. This correction changes no model, route,
prompt, domain, condition, candidate, seed, repetition, budget, balance, or analysis
setting; it prevents an approval-latency measurement from being misreported as
model behavior.

## Amendment 8 — GLM arithmetic missingness gate failed (2026-07-21)

The scored GLM block was stopped during arithmetic as soon as the primary
missingness rule became irrecoverable. Eight in-flight rows settled during process
termination, leaving 225 arithmetic rows: 219 parsed scores and six
`truncated_no_score` failures. Forty-one cells used the 2,048-token retry. Failures
were answer-only/correct 2, answer-only/wrong 3, and full-rationale/wrong 1; no
baseline failure was observed. Three failures in a 48-cell primary stratum imply
6.25% missingness, and five injected primary failures versus zero baseline imply a
5.21-point truncation difference. Both exceed the frozen five-point gate. Recorded
attempt cost was $0.591687. No code or SQL cell began.

Prefix `ccc_openrouter_v1_glm52_bounded` is void, never resumed, and never pooled.
The result is an unmeasurable GLM endpoint under this score protocol, not evidence
of immunity or capture. Kimi remains independently eligible for its bounded
compatibility check.

## Amendment 9 — Kimi arithmetic missingness gate failed (2026-07-22)

The Kimi block was stopped during arithmetic as soon as a primary stratum became
irrecoverably unbalanced. Four in-flight responses settled during termination,
leaving 37 rows: 28 parsed scores, nine `truncated_no_score` failures, and 16 cells
that used the 2,048-token retry. Failures were no-injection/correct 3,
answer-only/correct 2, answer-only/wrong 1, full-rationale/correct 1,
full-rationale/wrong 1, and solver-rationale/correct 1. Three failures in the
48-cell baseline/correct primary stratum imply 6.25% missingness, above the frozen
five-point limit. Recorded attempt cost was $0.221774. No code or SQL cell began.

Prefix `ccc_openrouter_v1_kimi_k27_code_together_bounded` is void, never resumed,
and never pooled. Kimi is unmeasurable under this score protocol and Together
endpoint; the outcome is not evidence of immunity or capture.
