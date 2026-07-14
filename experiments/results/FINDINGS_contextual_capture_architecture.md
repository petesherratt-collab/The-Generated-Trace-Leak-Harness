# Findings - Contextual Conclusion Capture architecture experiment

**Completed:** 2026-07-14  
**Design:** frozen before outcome calls  
**Schedule seed:** `984217603`  
**Scope:** benchmark-agnostic causal architecture test on the frozen 16-item set

## Completeness and evidence audit

The frozen schedule completed once under one exclusive writer:

- routing solves: **240/240**, all unique, no malformed rows;
- final judge attempts: **3,840/3,840**, all unique, no malformed rows;
- successful judge cells: **3,633**;
- failed, unresolved judge cells retained as evidence: **207**;
- duplicate judge cells: **0**;
- duplicate successful cells: **0**;
- background error log: empty.

Judge failures were concentrated in Claude (159) and Gemini (47), with one Llama failure. By
architecture there were 79 isolation, 54 contaminated score-only, 43 router and 31 written-
verification failures. Missingness was therefore factor-correlated and is not evidence of
safety. Every contrast below excludes an item unless all required cells and all three
repetitions succeeded.

The isolation invariant passed: all **480** item/model/candidate/repetition prompt pairs had
the same prompt hash under correct- and wrong-reference metadata. Thus the isolated judge had
no reference-content pathway by construction.

Evidence SHA-256 hashes:

- `architecture_obs.jsonl`: `8a40e5e705851844426d7e75853c557f754c6a6c91a0baa474c3802ebc84bf87`
- `architecture_solver.jsonl`: `8318d4ddb7d11c7d66cbda0a3ccd16892225994e21c38ecbc348ced60f054c25`
- `architecture_prompts.jsonl`: `e444b6a2dc4b71caa92d906ac556f4770c8751245958389ed6ca3180e2cbf19c`
- `architecture_meta.json`: `fe87396d172ca63a7e1a224264936aece63351d8300eab6d03552fc7abe0ed22`

## Fail-closed decisions

Support required at least 12 of 16 complete items and a 95% item-clustered bootstrap interval
excluding zero in the preregistered direction.

| Model | Exposed score judge is susceptible | Written verification mitigates | Isolation gains under wrong reference | Conflict router gains under wrong reference | Router detects wrong-reference conflict |
|---|---:|---:|---:|---:|---:|
| GPT-4o mini | Supported | Supported | Supported | Supported | Supported |
| Claude Haiku 4.5 | Not measurable (`n=7`) | Not measurable (`n=7`) | Not measurable (`n=4`) | Not measurable (`n=9`) | Supported |
| Gemini 2.5 Flash | Supported | Not measurable (`n=5`) | Supported | Not supported | Supported |
| DeepSeek Chat | Supported | Supported | Supported | Not supported | Supported |
| Llama 3.3 70B | Supported | Supported | Supported | Supported | Supported |

`Not supported` means the confidence interval included zero; it does not establish no effect.
`Not measurable` means the preregistered completeness threshold was not met.

## Primary effect estimates

Effects are mean score-discrimination points, paired within item. Positive safeguard gain means
better separation of the correct candidate from the wrong-matching candidate under the wrong
reference.

| Model | Exposed-reference susceptibility | Verification mitigation | Isolation safeguard gain | Router safeguard gain |
|---|---:|---:|---:|---:|
| GPT-4o mini | +90.00 `[+58.75, +122.29]`, `n=16` | +52.69 `[+22.35, +87.65]`, `n=16` | +59.06 `[+28.75, +89.58]`, `n=16` | +59.35 `[+30.87, +90.75]`, `n=16` |
| Claude Haiku 4.5 | +129.29 `[+100.00, +160.00]`, `n=7` | +61.10 `[+21.32, +91.64]`, `n=7` | +131.25 `[+100.00, +175.00]`, `n=4` | +91.08 `[+44.63, +139.00]`, `n=9` |
| Gemini 2.5 Flash | +39.90 `[+12.81, +72.40]`, `n=16` | +18.47 `[+0.00, +44.87]`, `n=5` | +23.44 `[+3.65, +44.80]`, `n=16` | -14.68 `[-42.10, +13.67]`, `n=13` |
| DeepSeek Chat | +84.27 `[+56.88, +112.09]`, `n=16` | +83.23 `[+54.99, +114.23]`, `n=16` | +52.29 `[+36.67, +66.88]`, `n=16` | +15.52 `[-10.09, +41.16]`, `n=16` |
| Llama 3.3 70B | +112.50 `[+81.25, +143.75]`, `n=16` | +58.79 `[+35.10, +81.27]`, `n=16` | +85.42 `[+62.50, +110.42]`, `n=16` | +92.25 `[+68.42, +117.94]`, `n=16` |

## Branch-selection interpretation

For the contaminated score-only architecture, changing a correct reference to a wrong one
reduced the correct-branch win probability from:

- GPT-4o mini: **81.25% to 35.42%**;
- Gemini 2.5 Flash: **87.50% to 60.42%**;
- DeepSeek Chat: **93.75% to 38.54%**;
- Llama 3.3 70B: **84.38% to 28.12%**.

Claude's corresponding complete-item estimates were 100.00% to 16.67%, but only nine items
were complete and the primary susceptibility contrast had only seven.

Under context isolation, correct-branch win rates were stable across reference metadata within
sampling variation: GPT 64.58%/63.54%, Gemini 77.08%/72.92%, DeepSeek 72.92%/76.04%, and
Llama 70.00%/70.83% for correct/wrong metadata. This empirical check is secondary; the stronger
claim is the audited absence of the reference from the prompt.

## Router result

The router's wrong-minus-correct conflict-detection contrast was supported for all five models,
with estimates from +43.75 points for Gemini to +100 points for Claude. Detection did not,
however, translate into a supported end-to-end safeguard for every model. The router gain was
supported only for GPT and Llama; Gemini's estimate was negative and both Gemini and DeepSeek
intervals included zero.

This distinction matters: detecting conflicting conclusions is easier than guaranteeing a
reliable adjudication path. The router sometimes falls back to written verification, whose
model-specific scoring and formatting behavior can itself be unstable. The frozen router is
therefore a promising prototype, not a validated universal safeguard.

## Conclusion

On this frozen numerical/combinatorial item set, the architecture experiment causally confirms
that the judge-facing information pathway matters:

1. direct exposure to a wrong conclusion produced large discrimination loss in all four models
   meeting the completeness rule;
2. written verification mitigated that loss in three measurable models, but it remained a
   prompt-level defense inside a contaminated context;
3. context isolation was the most consistent tested safeguard, improving wrong-reference
   discrimination in all four measurable models and passing a byte-level pathway audit;
4. conflict routing helped GPT and Llama but did not meet the support rule for Gemini or
   DeepSeek, so it cannot yet be treated as a general solution.

The warranted design recommendation is to keep external conclusions out of the scoring
context whenever possible. If a benchmark requires references, an independent solve and
conflict signal may be useful, but the final adjudicator should receive a fresh, quarantined
context and the entire route must pass mirrored correct/wrong-reference tests.

These findings do **not** establish that any named benchmark or production evaluator is
affected. Such a claim requires reproducing that system's real prompt, reference visibility,
candidate order, routing, retry and aggregation behavior.
