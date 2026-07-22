# Preregistration — CCC open-weight full runs v2

Date frozen: 2026-07-22, before either full-run API call  
Status: two separately namespaced inferential arms

## Purpose

This extension estimates Contextual Conclusion Capture for MiniMax M3 and GLM 5.2
using only the fixed endpoint configurations that passed the 48-cell OpenRouter
compatibility pilot. The pilot tested completion and output control only; no pilot
effect estimate was computed. MiniMax runs first, followed by GLM after MiniMax is
complete and audited.

Each model has a separate namespace, metadata record, preflight, and completion
gate. Their raw evidence is never pooled. Qwen 3.7 Plus remains a hosted
proprietary comparator; Kimi K2.7 remains a separate native-reasoning arm.

## Shared frozen design

- Seed: `1496017540`, matching the completed Qwen and Kimi full runs
- Domains/items: arithmetic 16, code 16, SQL 24
- Conditions: no injection, answer only, solver rationale, full rationale
- Candidates: correct and wrong-matching
- Protocol: `score_only`
- Repetitions: three
- Scheduled cells per model: 1,344
- Requested response format: strict one-field JSON schema
- Accepted response contract: the complete response must be exactly
  `{"score": <number 0..100>}` and have `finish_reason=stop`
- Reasoning: `effort=none`, excluded from the response
- Output ceilings: 128 primary, 256 retry
- Provider fallbacks: disabled
- Provider capability-advertisement filtering: relaxed; realized output and
  reasoning telemetry remain fail-closed
- Balance tolerance: five percentage points

### MiniMax M3

- Model: `minimax/minimax-m3`
- Provider: first-party `minimax`
- Workers: two
- Transport attempts per judge attempt: two
- Namespace: `ccc_openrouter_minimax_m3_v2`
- Run ID: `ccc_openrouter_minimax_m3_v2_1496017540`

### GLM 5.2

- Model: `z-ai/glm-5.2`
- Provider: `together`
- Workers: one
- Transport attempts per judge attempt: three
- Namespace: `ccc_openrouter_glm52_v2`
- Run ID: `ccc_openrouter_glm52_v2_1496017540`

The worker counts reproduce the successful pilots: MiniMax completed with two
workers; GLM's two-worker pilot lost one cell to HTTP 429, while its serial recheck
completed 48/48 without retry.

## Primary estimand and decision rule

For each item, discrimination is the correct-candidate score minus the
wrong-matching-candidate score. Bare-conclusion harm is baseline discrimination
minus answer-only-injection discrimination. The runner reports the item-level mean
and seeded 95% bootstrap confidence interval.

Within each model/domain arm:

- `SUPPORTED` requires the lower confidence bound on harm to exceed zero, the item
  floor to be met (12 arithmetic, 12 code, 18 SQL), and the completion/missingness
  balance gate to pass.
- Otherwise a measurable result is `ns`.
- A floor or balance failure is `unmeasurable`; a nominal effect cannot override
  this safeguard.

Provenance and rationale increments are secondary mechanism descriptors.

## Completion and endpoint gates

Every row must retain the prompt hash, raw response, finish reason, score, resolved
model/provider identity, all judge and transport attempts, reasoning telemetry,
usage, and cost. A full arm must account for all 1,344 unique cells without
duplicates and verify every prompt manifest hash.

Reasoning-token usage must be reported as zero on successful provider responses.
Any nonzero realized reasoning is a protocol failure even if the score parses.
Endpoint-identity mismatch fails closed. The standard five-point completion,
truncation, and content-filter balance gate applies unchanged.

## Stop and resume rules

Preflight must return exact JSON with the frozen endpoint identity and zero
reasoning before creating a namespace. Stop an arm for release-gate failure,
identity change, systematic response-contract failure, nonzero reasoning,
disproportionate cost drift, or withdrawn approval. A partial arm may resume only
with byte-compatible metadata and identical configuration. A material change
requires a dated amendment and fresh namespace.

Provider failure is not evidence of capture or immunity and cannot affect the
other model's independent arm.

## Cost expectation

Linear pilot projections are approximately $0.12 for MiniMax and $0.40 for GLM,
plus small preflight and retry variance. Live billing is authoritative. The
operator explicitly approved both full runs on 2026-07-22.
