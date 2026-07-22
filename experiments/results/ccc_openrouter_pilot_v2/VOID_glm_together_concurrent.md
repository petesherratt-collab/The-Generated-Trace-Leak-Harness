# VOID — GLM 5.2 / Together concurrent pilot

Date: 2026-07-22  
Prefix: `ccc_openrouter_pilot_v2_glm_together_permissive_reasoning_off`  
Status: failed compatibility configuration; never resume or pool

The two-worker pilot wrote all 48 scheduled rows, but one code cell ended in
`request_error` after both transport attempts returned HTTP 429.

- 47/48 parseable scores and 47/48 strict one-field JSON responses.
- Five cells entered a second judge attempt; one remained failed.
- All provider responses reported zero reasoning and at most seven completion
  tokens; provider/model identity mismatches were zero.
- Scored cost: $0.013830; preflight: $0.000053; total: $0.013883.

An initial telemetry report also marked complete domains as failed because it
incorrectly required reasoning metadata from transport attempts that never
reached a provider. Amendment 6 corrects that denominator, but it does not repair
the genuine 47/48 completeness failure. A fresh one-worker namespace was used
for the valid serial recheck.
