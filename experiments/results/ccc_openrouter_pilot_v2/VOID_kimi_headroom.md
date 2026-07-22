# VOID — Kimi K2.7 Code / Together headroom pilot

Date: 2026-07-22  
Prefix: `ccc_openrouter_pilot_v2_kimi_headroom`  
Status: failed compatibility configuration; never resume or pool

The pilot was stopped after its reasoning-control gate became irrecoverably
false. Seven in-flight calls settled during shutdown.

- 47/48 scheduled cells were written; all 47 had a parseable score.
- Only 45/47 final responses were strict one-field JSON.
- Two responses exposed long deliberation in the answer body.
- One cell used the retry; 48 scored attempts were recorded in total.
- Maximum reported reasoning: 8,001 tokens, exceeding the requested 2,048 cap.
- Provider/model identity mismatches: zero (`Together`, Kimi K2.7 Code).
- Scored-attempt cost: $0.222856; preflight: $0.000217; total: $0.223073.
- The exact remaining Python pilot process was identified and stopped; no matching
  process remained afterward.

No capture estimate or immunity claim is permitted from this partial namespace.
The result establishes that Together did not enforce the requested reasoning or
strict-output controls reliably enough for the proposed full protocol.
