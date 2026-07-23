# Preregistration — CCC OpenRouter score-output compatibility pilot v2

Date frozen: 2026-07-22, before any v2 pilot-scored call  
Status: compatibility pilot only; no capture estimates or hypothesis verdicts

## Purpose

The first OpenRouter panel established that the prior score-output configuration
was measurable for hosted Qwen 3.7 Plus but not for the three downloadable-weight
judges. This pilot tests whether model-specific reasoning/output controls can
produce complete, condition-balanced score evidence before any further full run.
It does not reuse, resume, or pool any void namespace.

## Frozen design

- Seed: `824663051`.
- Domains: arithmetic, code, and SQL.
- Items: two per domain, selected independently of source ordering by ascending
  SHA-256 of `pilot-items-v1|seed|domain|item_id`.
- Cells per domain: 2 items × 4 conditions × 2 candidates × 1 repetition = 16.
- Cells per model: 48, plus one trivial endpoint preflight.
- Protocol: `score_only`, unchanged prompt instrument, strict numeric JSON Schema.
- Fixed provider route per model; OpenRouter fallback disabled.
- Two workers. Every attempt, usage record, resolved model, and provider is retained.

The pilot is intentionally balanced across all eight condition × candidate strata.
The schedule is a deterministic hash-seeded shuffle; it is not a prefix of a full
run schedule.

## Model-specific configurations

| Model | Provider | Reasoning | Primary / retry output ceiling | Prefix |
|---|---|---|---:|---|
| `minimax/minimax-m3` | `minimax` | `effort=none`, excluded | 128 / 256 | `ccc_openrouter_pilot_v2_minimax_official_permissive_reasoning_off` |
| `z-ai/glm-5.2` | `deepinfra` | `effort=none`, excluded | 128 / 256 | `ccc_openrouter_pilot_v2_glm_reasoning_off` |
| `moonshotai/kimi-k2.7-code` | `together` | `max_tokens=2048`, excluded | 4096 / 8192 | `ccc_openrouter_pilot_v2_kimi_headroom` |

MiniMax and GLM are tested with reasoning disabled because the current OpenRouter
model metadata marks reasoning as non-mandatory. Kimi is marked reasoning-mandatory;
its output ceilings are therefore made strictly larger than its reasoning ceiling
so a final JSON score has reserved headroom.

## Graduation rule

A model graduates only if all 48 scored cells finish with a parseable score, the
resolved model/provider identity matches the frozen route, and no final
`truncated_no_score`, content-filter, request, or parse failure remains. A retry is
allowed because the proposed full protocol also includes that retry, but its use
and cost must be reported.

Any final failure means that model does not receive a full run under this
configuration. Passing the pilot authorizes only the preparation of a separately
frozen full-run namespace; it does not silently authorize or start that run.

No effect size, confidence interval, `SUPPORTED`, immunity, or capture claim may
be computed from this 2-item-per-domain compatibility sample.

## Amendment 1 — MiniMax provider compatibility (2026-07-22, before scored cells)

The pinned DeepInfra MiniMax route returned HTTP 404 on both trivial preflight
attempts when asked for reasoning-off plus strict structured output. No scored
cell was called, no usage or cost was reported, and no run metadata was created.
OpenRouter's current provider table lists the first-party MiniMax endpoint with
the required model-level parameters, while DeepInfra has no reported uptime.

MiniMax therefore moves to the fixed first-party provider slug `minimax`, keeps
the same reasoning/output settings, and receives a fresh prefix
`ccc_openrouter_pilot_v2_minimax_official_reasoning_off`. The preflight failure is
a route-compatibility event, not model evidence, and is never pooled.

## Amendment 2 — MiniMax capability-advertisement filter (2026-07-22, before scored cells)

The fixed first-party MiniMax route also returned HTTP 404 when
`provider.require_parameters=true`; again, both failures were trivial preflight
attempts, with zero scored cells and no reported usage. OpenRouter documents that
this flag excludes endpoints whose capability advertisement does not list every
requested parameter, even when the endpoint can accept or ignore the request.

The MiniMax route remains pinned with fallbacks disabled, but its compatibility
probe sets `provider.require_parameters=false` and uses the fresh prefix
`ccc_openrouter_pilot_v2_minimax_official_permissive_reasoning_off`. Graduation
now additionally requires every response to be strict parseable JSON and all
reported reasoning-token usage to be zero. If reasoning use is nonzero or missing
often enough to prevent verification, MiniMax fails the pilot; ignored parameters
are not silently treated as successful configuration.

## Amendment 3 — GLM rate limit (2026-07-22, before scored cells)

The GLM reasoning-off compatibility preflight received HTTP 429 from the fixed
DeepInfra route on every transport attempt. The runner exhausted its bounded
retries and aborted with zero scored cells, no usage record, and no run metadata.
This is a provider-capacity event, not model evidence. GLM is deferred until the
route cools down; Kimi remains independently eligible for its frozen pilot.

## Amendment 4 — Kimi reasoning control not honoured (2026-07-22)

The Kimi pilot was stopped once its graduation gate became irrecoverably false.
Seven in-flight calls settled during shutdown, leaving 47 of 48 scheduled cells:
all 47 contained a parseable score, but only 45 were strict one-field JSON. Two
responses exposed long deliberation in the answer body. One cell used the retry,
whose reported reasoning usage reached 8,001 tokens despite the requested 2,048
ceiling. Provider and response-model identities remained correct.

Recorded cost was $0.222856 for scored attempts plus $0.000217 for preflight,
$0.223073 total. The remaining scheduled cell was not called after the exact
pilot process was terminated. Prefix `ccc_openrouter_pilot_v2_kimi_headroom` is
ineligible, never resumable, and never pooled. This is a Together endpoint-control
failure, not evidence of Kimi immunity or capture.

## Amendment 5 — GLM fixed-route replacement and retry bound (2026-07-22, before scored cells)

GLM remains unstarted after DeepInfra's HTTP 429 event. OpenRouter's live GLM 5.2
provider table reports Together among the fastest endpoints and with the lowest
observed structured-output error rate. GLM therefore moves to fixed provider
`together`, fallbacks remain disabled, and the fresh prefix is
`ccc_openrouter_pilot_v2_glm_together_permissive_reasoning_off`.

As with the successful MiniMax configuration, capability-advertisement filtering
is relaxed while realized behavior is made stricter: all 48 final responses must
be exact score JSON, and every attempt must report zero reasoning tokens. Internal
HTTP transport retries are reduced from five to two for this and subsequent pilot
calls; the two judge budgets remain unchanged. A failed trivial preflight still
aborts before scored cells.

## Amendment 6 — GLM telemetry denominator and serial recheck (2026-07-22, before recheck cells)

The first Together GLM pilot wrote 47/48 successful scores. The sole failed code
cell received HTTP 429 on both transport attempts. All 47 provider responses were
exact JSON, reported zero reasoning, and used at most seven completion tokens.
The arithmetic and SQL reports nevertheless printed `FAIL` because the pilot gate
incorrectly demanded reasoning telemetry from transport attempts that produced no
provider response. The correct denominator is provider responses, not all judge
attempt records; the gate is fixed accordingly. The 47/48 completeness failure
still stands and the original prefix remains ineligible.

A fresh recheck uses prefix
`ccc_openrouter_pilot_v2_glm_together_serial_reasoning_off`, one worker to avoid
concurrency-triggered 429s, and three bounded transport attempts. All other
settings, items, conditions, score format, and the 48/48 graduation requirement
remain unchanged. This recheck is compatibility evidence only and cannot repair
or pool with the first namespace.

## Amendment 7 — pilot closeout (2026-07-22)

The serial GLM recheck completed 48/48 with exact score JSON, no retry, zero
reported reasoning, and correct endpoint identity. It graduates alongside the
48/48 MiniMax first-party configuration. Kimi does not graduate. No full run is
started by this closeout; each graduate requires a separately frozen full-run
namespace and schedule.

Recorded compatibility spend was $0.255261: MiniMax $0.004133, the ineligible
concurrent GLM block $0.013883, the valid serial GLM block $0.014171, and Kimi
$0.223073. Provider failures that returned no usage record contribute $0.000000
to this total. These are compatibility costs, not capture-effect evidence.

## Amendment 8 — Kimi hosted-provider recovery sequence (2026-07-22, before new calls)

Kimi remains substantively important to the planned open-weight comparison, but
the Together result establishes only that that endpoint did not enforce the
requested reasoning ceiling and exact response schema. It does not establish a
model-level incompatibility. A bounded recovery sequence is therefore authorized:

1. try another fixed hosted endpoint using a trivial score-only preflight;
2. run the unchanged 48-cell compatibility schedule only if preflight returns an
   exact parseable score with the requested endpoint/model identity;
3. consider local inference only if hosted endpoints cannot enforce the controls;
4. if neither route is practical, define a separately labelled native-reasoning
   protocol that is never pooled with the terse-score panel.

DeepInfra is first because the earlier DeepInfra Kimi attempt failed only with
HTTP 429 before scored cells, while the official `moonshotai` route returned 404
and Together has now failed the realized-control gate. The fresh DeepInfra prefix
is `ccc_openrouter_pilot_v2_kimi_deepinfra_headroom`. It retains the frozen seed,
items, conditions, one repetition, strict score schema, 2,048 requested reasoning
ceiling, 4,096/8,192 output ceilings, fallback prohibition, 48/48 completeness,
and observed-reasoning ceiling of 2,048. One worker is used to reduce rate-limit
risk. Failure cannot be repaired or pooled; a later endpoint requires another
dated amendment and fresh prefix.

## Amendment 9 — Kimi DeepInfra capability-advertisement filter (2026-07-22, before retry)

The strict DeepInfra preflight returned HTTP 404 on both judge attempts with no
provider response, usage record, or scored cell. This is consistent with the
router excluding the endpoint when `provider.require_parameters=true`, not with
a Kimi response failure. The strict preflight namespace is closed.

One fresh DeepInfra preflight is authorized with
`provider.require_parameters=false` and prefix
`ccc_openrouter_pilot_v2_kimi_deepinfra_permissive_headroom`. The request still
contains the reasoning ceiling and strict JSON schema; relaxation affects only
OpenRouter's endpoint-advertisement filter. Realized behavior remains fail-closed:
the pilot may start only if the preflight supplies an exact score from DeepInfra
with the requested model identity, and graduation still requires 48/48 exact
scores plus reported reasoning use no greater than 2,048 on every provider
response. Ignored or unenforced controls therefore cannot produce a pass.
