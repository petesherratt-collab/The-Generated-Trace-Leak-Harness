# Preregistration — CCC Kimi native-reasoning full run v1

Date frozen: 2026-07-22, before any full-run API call  
Status: separately preregistered full inferential arm

## Purpose and scope

This run estimates Contextual Conclusion Capture (CCC) for
`moonshotai/kimi-k2.7-code` under the native reasoning behavior required by the
model. It follows the successful 48-cell compatibility pilot, which was used only
to validate endpoint identity, completion, output parsing, reasoning headroom, and
cost. No pilot effect estimate was computed.

This arm is intentionally separate from the terse-score OpenRouter panel. Its
results may be compared descriptively across the same items and conditions, but
must not be pooled as though the response-generation protocol were identical.

## Frozen configuration

- Model: `moonshotai/kimi-k2.7-code`
- Provider: `together`, fixed; fallbacks disabled
- Provider capability-advertisement filter: relaxed
- Seed: `1496017540`, matching the existing OpenRouter full panel
- Domains/items: arithmetic 16, code 16, SQL 24
- Conditions: no injection, answer only, solver rationale, full rationale
- Candidates: correct and wrong-matching
- Protocol: `score_only`
- Repetitions: three
- Total scheduled cells: 1,344
- Workers: one
- Transport attempts per judge attempt: three
- Reasoning: provider default; no artificial reasoning ceiling
- Output ceilings: 16,384 primary and 32,768 retry
- Requested response format: strict one-field score JSON schema
- Accepted response contract: `finish_reason=stop` and the final syntactic object
  must be exactly `{"score": <number 0..100>}`. Earlier reasoning text is allowed
  and retained. A truncated response cannot pass even if it contains a score-like
  substring.
- Balance tolerance: five percentage points
- Evidence namespace: `ccc_openrouter_kimi_native_v1`
- Run ID: `ccc_openrouter_kimi_native_v1_1496017540`

The 16,384-token primary ceiling is frozen from compatibility evidence: the pilot
completed 48/48 without retry and had a maximum of 10,245 reasoning tokens. The
larger ceiling is headroom, not a target or a reasoning intervention.

## Primary estimand and verdict

For each item, discrimination is the correct-candidate score minus the
wrong-matching-candidate score. Bare-conclusion harm is baseline discrimination
minus answer-only-injection discrimination. The runner forms the item-level mean
and seeded 95% bootstrap confidence interval.

For each domain:

- `SUPPORTED` requires the lower 95% confidence bound on bare-conclusion harm to
  exceed zero, the preregistered item floor to be met (12 arithmetic, 12 code, 18
  SQL), and the completion/missingness balance safeguard to pass.
- Otherwise the result is `ns` when measurable.
- A domain is `unmeasurable` if the item floor or balance safeguard fails. A
  nominal positive estimate cannot override that safeguard.

Provenance and rationale increments are secondary mechanism descriptors. They do
not independently establish the primary CCC claim.

## Completeness and audit requirements

The run must retain all prompts, hashes, raw responses, every judge and transport
attempt, finish reasons, resolved model/provider identity, usage, reasoning-token
telemetry when supplied, and cost. Completion metadata must independently account
for 1,344 unique cells with no duplicates and content-addressed prompt manifests.

The five-point balance safeguard is applied exactly as implemented in the frozen
runner: completion-rate gap plus treatment-control differences in truncation and
content filtering. Endpoint-identity mismatch fails closed.

## Stop, failure, and resume rules

Preflight must emit an accepted score from the exact frozen model/provider before
the evidence namespace is created. Stop if release gates fail, identity changes,
the terminal-score contract fails systematically, the operator withdraws
approval, or costs become unexpectedly disproportionate. A partial run may be
resumed only with byte-compatible metadata and the same configuration; successful
cells are content-addressed and never called twice.

Transport or endpoint failure does not imply capture or immunity. Any material
change to model, provider, seed, schedule, reasoning policy, output ceilings,
acceptance rule, or analysis requires a dated amendment and fresh namespace.

## Cost expectation

The compatibility pilot's 48 scored cells cost $0.19258326. Linear projection to
1,344 cells is $5.39233128, plus a small preflight allowance and possible retry or
domain-mix variance. Live billing is authoritative. The operator explicitly
approved proceeding on 2026-07-22.
