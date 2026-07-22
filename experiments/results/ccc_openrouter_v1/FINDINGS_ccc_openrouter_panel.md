# CCC OpenRouter panel — local findings

Date completed: 2026-07-22  
Seed: `1496017540`  
Schedule: `sha256-domain-cell-v2`  
Protocol: `score_only`  
Status: local only; not pushed to GitHub

## Confirmatory result

Only the bounded Qwen block passed every completeness and balance safeguard.

| Model / endpoint | Arithmetic | Code | SQL | Status |
|---|---:|---:|---:|---|
| Qwen 3.7 Plus / Alibaba | **SUPPORTED +94.17** [57.50, 131.25] | ns −9.27 [−31.56, 13.75] | **SUPPORTED +165.28** [147.22, 181.94] | 1,344/1,344, measurable |
| MiniMax M3 / DeepInfra | — | — | — | unmeasurable; treatment-skewed truncation |
| GLM 5.2 / DeepInfra | — | — | — | unmeasurable; treatment-skewed truncation |
| Kimi K2.7 Code / Together | — | — | — | unmeasurable; primary-stratum truncation |

Qwen had 0% completion skew in every domain, 16 arithmetic items, 16 code
items, and 24 SQL items above their preregistered floors. Its arithmetic result is
notably unlike the prior GPT/Gemini/Grok frontier pattern and resembles Fable's
arithmetic susceptibility; its SQL capture is exceptionally large. Code is null.

## Qwen audit

- 384 arithmetic + 384 code + 576 SQL = 1,344 unique cells.
- Zero duplicate cell keys, failed cells, judge retries, or endpoint mismatches.
- All prompt manifests and attempt schemas pass the runner's completion audit.
- Fixed provider identity: `Alibaba` (requested slug `alibaba`); fallback disabled.
- Strict JSON Schema score output.
- `reasoning.max_tokens=2048`; observed maximum reasoning was exactly 2,048.
- Evidence hashes are recorded in the completion metadata.
- Recorded bounded-run attempt cost: $1.895857.

## Fail-closed diagnostics

MiniMax was tried under progressively larger retry ceilings before structured
reasoning control was introduced. Every namespace is explicitly void:

- 1,024/2,048 diagnostic: 83 arithmetic rows, six injected truncations, $0.094844.
- 1,024/4,096 diagnostic: full arithmetic plus 15 quarantined code rows; primary
  completion gap 10.4 points, $0.470733.
- 1,024/8,192 diagnostic: stopped at 159 arithmetic rows; injected primary gate
  failed, $0.212743.

Provider-default Qwen was also voided after its hidden reasoning escaped the
visible output caps. It completed arithmetic and 205 code rows, but one code cell
used 111,724 completion tokens across two nominally 1,024/2,048-token attempts;
recorded cost was $1.469713. This led to the explicit reasoning cap and strict
schema used for the valid restart.

The bounded GLM namespace stopped at 225 arithmetic rows (219 parsed, six failed,
primary gate failed; $0.591687). The bounded Kimi namespace stopped at 37
arithmetic rows (28 parsed, nine failed, baseline/correct gate failed; $0.221774).
Neither reached code or SQL.

Total recorded attempt spend across the diagnostic and valid namespaces was
$4.957351, excluding a handful of unpersisted trivial preflight calls. The panel
therefore cost orders of magnitude less than the earlier frontier exercise while
still producing one complete cross-domain judge and three informative fail-closed
endpoint diagnostics.

## Interpretation boundary

The three unmeasurable models cannot be called immune: their missing scores are
condition- or stratum-skewed. Qwen's results describe the hosted proprietary
Qwen 3.7 Plus comparator, not an open-weight model. The open-weight objective is
only partially answered here because all three downloadable-weight judges failed
the score-protocol missingness safeguard on their pinned hosted endpoints.
