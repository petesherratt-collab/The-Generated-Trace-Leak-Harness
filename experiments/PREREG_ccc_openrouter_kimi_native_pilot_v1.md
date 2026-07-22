# Preregistration — Kimi native-reasoning compatibility pilot v1

Date frozen: 2026-07-22, before any native-pilot API call  
Status: compatibility only; no capture estimate or hypothesis verdict

## Rationale and separation

Kimi K2.7 Code is reasoning-mandatory. The earlier Together compatibility block
showed that a requested 2,048-token reasoning ceiling was not enforced: one call
used 8,001 reasoning tokens, two responses exposed long reasoning in the content,
and the run was stopped after 47 of 48 cells. DeepInfra subsequently failed two
fresh trivial preflights before scored cells (strict routing: HTTP 404; relaxed
capability filter: HTTP 429). Local inference is not practical on the available
32 GB, integrated-GPU workstation for a roughly 1T-total-parameter MoE.

This pilot therefore tests Kimi under its native reasoning behavior. It is a
separate protocol and evidence namespace. It must never be pooled with or reported
as directly interchangeable with the terse-score open-weight panel.

## Frozen configuration

- Model: `moonshotai/kimi-k2.7-code`
- Provider: `together`, fixed; fallbacks disabled
- Seed: `824663051`
- Items: the same deterministic two-item subset per domain used in pilot v2
- Domains: arithmetic, code, SQL
- Conditions: no injection, answer only, solver rationale, full rationale
- Candidates: correct and wrong-matching
- Repetitions: one
- Total: 48 cells
- Workers: one
- Transport attempts per judge attempt: three
- Reasoning: provider default; no artificial reasoning ceiling
- Output ceilings: 16,384 primary; 32,768 retry
- Requested response format: strict one-field JSON schema
- Realized acceptance contract: the response must finish with `stop` and its final
  syntactic object must be exactly `{"score": <number 0..100>}`. Earlier prose or
  reasoning in the content is allowed and retained. A `length` response cannot
  pass even if it contains a score-like substring.
- Prefix: `ccc_openrouter_kimi_native_pilot_v1_kimi_together_native_reasoning_v1`

The larger primary ceiling is fixed from the prior diagnostic: most calls stopped
below 4,096 tokens, while one difficult response stopped at 8,009 after retry.
The 16,384/32,768 ceilings provide headroom without claiming control over Kimi's
native reasoning length.

## Graduation rule

The configuration graduates only if all 48 scheduled cells are present, every
cell has a parsed score accepted by the terminal-JSON-plus-stop contract, every
response resolves to the frozen model/provider identity, prompt manifests and
attempt records are complete, and there are no final errors. Exact whole-response
JSON is recorded as a stricter diagnostic but is not required because this is the
native-reasoning protocol. Reasoning usage and cost are recorded without a ceiling.

Failure is an endpoint/protocol result, not evidence of capture, immunity, or
model quality. No effect size is computed from this pilot. A full native-reasoning
Kimi run requires a new preregistration, namespace, and explicit operator approval.

## Cost bound and stop conditions

The previous 47-cell block cost $0.223073 including preflight. A similar native
pilot is expected to remain well below $1, but live billing is authoritative.
Stop before scored cells if preflight fails the terminal-output or identity gate.
Stop and quarantine the namespace if provider/model identity changes, evidence
collides, release gates fail, or the operator withdraws approval.
