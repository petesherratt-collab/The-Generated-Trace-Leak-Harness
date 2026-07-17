# Findings — code-domain CCC replication, Stage 2: architectures (preregistered)

> Detailed stage record. For the unified write-up of the whole code-domain replication
> (Stages 1 + 2 as one bounded study), see
> [`FINDINGS_ccc_codedomain.md`](FINDINGS_ccc_codedomain.md).

**Run:** 2026-07-17, operator's machine (CPython 3.13.14, sequential; ~5.5 h) ·
**Prereg:** [`../PREREG_ccc_codedomain.md`](../PREREG_ccc_codedomain.md) §6–8 ·
**Adapter:** `run_ccc_codedomain_stage2.py` · **Seed:** `517293847` ·
**Conditional subset (frozen at Stage 1):** gpt-4o-mini, claude-haiku-4.5, gemini-2.5-flash,
llama-3.3-70b; deepseek excluded (Stage-1 primary not supported) ·
16 items × 4 models × 4 architectures × 2 mirrored references × 2 candidates × 3 reps
= **3,072 judge cells + 192 spec-only router solves** ·
**Evidence:** [`ccc_code_obs_stage2.jsonl`](ccc_code_obs_stage2.jsonl),
[`ccc_code_prompts_stage2.jsonl`](ccc_code_prompts_stage2.jsonl),
[`ccc_code_solver_stage2.jsonl`](ccc_code_solver_stage2.jsonl),
[`ccc_code_meta_stage2.json`](ccc_code_meta_stage2.json)

## Headline

**Structural safeguards beat prompt-level ones in the code domain.** Wrong-reference
susceptibility is causally confirmed for 3 of 4 models; **context isolation and the conflict
router both recover discrimination (supported 3/4)** — with the router's mechanical conflict
detection near-perfect (+94 to +100pp, Claude exactly 100) — while **written verification is
supported for no model**. Combined with Stage 1, the code-domain replication is complete:
CCC exists in code judging, and the same architectural remedies validated numerically
transfer, with the router *stronger* here than in the numeric domain.

## Integrity audit (independently re-verified)

- **3,072 rows = 3,072 unique cells**; max 1 attempt; **0 duplicate successes**; 3,043
  successes (99.1%) / 29 failures, all retained.
- **192/192 router solves parseable** (models solve these items easily — the router premise
  holds).
- **Isolation byte-invariant: 384/384 prompt pairs hash-identical** across reference
  variants (independently recomputed from the manifest); both contaminated architectures
  differ in **384/384** — the reference provably reaches contaminated judges and provably
  never reaches isolated ones.
- Metadata matches the freeze (seed, stimuli `f9fb12b7…`, items/runner hashes); all five
  contrasts recomputed independently from raw scores — point estimates matched the
  adapter's output exactly.
- Synthetic rigged control (defer-to-reference): +200 susceptibility by construction —
  probe sensitivity retained.

## Missingness (fail-closed, before estimates)

**All 29 failures are gemini**: 22 in `contaminated_verify_written`, 7 in `conflict_router`
— the router's quarantine path *is* a verify-written judge, so this is the same truncation
behaviour gemini showed in Stage 1 and the numeric runs. Consequences: gemini's
**verification-mitigation contrast is unmeasurable (n=7 < 12)**; its router gain runs at
n=14. Disclosed, never interpreted as safety.

## Preregistered scorecard

95% item-clustered bootstrap CIs; supported iff CI > 0 and ≥ 12/16 items complete.

| Contrast (predicted > 0) | gpt-4o-mini | claude-haiku | gemini-flash | llama-3.3 |
|---|---:|---:|---:|---:|
| **Susceptibility** (contaminated score-only, correct−wrong ref) | **+35.4 [+19.6, +52.9] ✅** | **+46.6 [+18.4, +71.9] ✅** | **+29.2 [+20.3, +39.4] ✅** | +13.1 [−10.2, +37.5] ✗ |
| **Verification mitigation** (diff-in-diff) | +22.4 [−8.5, +49.7] ✗ | −17.5 [−63.8, +20.0] ✗ | +18.2, n=7 → **unmeasurable** | −5.5 [−26.4, +17.9] ✗ |
| **Isolation gain** (wrong ref) | **+32.7 [+16.3, +51.5] ✅** | **+43.8 [+14.4, +70.3] ✅** | **+21.0 [+10.4, +32.5] ✅** | +11.7 [−10.2, +36.0] ✗ |
| **Router gain** (wrong ref) | **+51.4 [+34.2, +67.4] ✅** | **+48.6 [+16.7, +76.5] ✅** | **+28.2 [+9.2, +45.0] ✅** n=14 | −0.8 [−16.8, +15.0] ✗ |
| **Router detection** (wrong−correct, pp) | **+93.8 ✅** | **+100.0 [100, 100] ✅** | **+93.8 ✅** | **+93.8 ✅** |

## Per-arm discrimination (mean; the raw shape behind the contrasts)

| Model | no-reference baseline (isolated) | correct reference | wrong reference |
|---|---:|---:|---:|
| gpt-4o-mini | +38.1 | +39.6 | **+4.2** |
| claude-haiku | +78.4 | +81.3 | **+34.7** |
| gemini-flash | +55.3 | +64.7 | **+35.5** |
| llama-3.3 | +62.9 | +64.0 | +50.8 |

## Key findings

1. **Mirrored-reference CCC is causal in code** (3/4 supported). Flipping only the
   reference from correct to wrong collapses discrimination — gpt goes from +39.6 to +4.2.
2. **Isolation works and is byte-audited** (3/4 supported). The isolated judge's prompts
   are provably reference-free; its wrong-reference discrimination equals the clean
   baseline by construction.
3. **The router now carries its weight — the headline change from the numeric domain.**
   Numerically the router helped only 2/4; in code it is supported 3/4 with near-perfect
   mechanical detection, and for gpt the router gain (+51.4) *exceeds* the isolation gain
   (+32.7): on disagreement it routes to a fresh verify-written judge, which for gpt is a
   stronger protocol than bare scoring — the routed pipeline ends *above* the no-reference
   baseline (+55.5 vs +38.1). Code favours the router because comparing a solved output
   value is exactly what a mechanical comparator does best (192/192 parseable solves).
4. **Written verification fails everywhere as a mitigation** (0/4 supported; claude points
   negative). Against reference-shaped contamination in code, the prompt-level defence
   does not clear the bar for any model — continuing the pattern that prompt-level
   protections weaken as the tests harden, while structural ones keep passing.
5. **The llama puzzle, resolved against our own hypothesis.** We conjectured llama's flat
   susceptibility might mean a *correct* reference damages it too (conclusion-presence
   sensitivity). Tested directly: correct-reference harm vs the no-reference baseline is
   **−1.0 [−3.1, +1.0] — a clean null**. Llama is simply only mildly captured by this
   reference format (+13.1 ns) despite being the *most* captured by Stage 1's injection
   format (+44.0). Same bare wrong conclusion, different wording and position ("Reference
   note … after the candidate" vs "External reference … before the candidate") — a
   format-sensitivity signal, hypothesis-generating, consistent with llama's known
   wording sensitivity from the numeric arc.
6. **Descriptive bonus:** for gemini a *correct* reference significantly **improves**
   discrimination over the no-reference baseline (correct-ref harm −9.4 [−15.5, −3.7]) —
   a right answer key genuinely helps it. Descriptive only (not preregistered), but it
   sharpens the design tension: references carry real value when correct and real damage
   when wrong, which is precisely why routing on mechanical agreement — rather than
   banishing references entirely — is an attractive production design.

## Release-gate check (all applicable gates passed)

1. ✅ Frozen hashes matched at run start (CPython 3.13.14, in accepted set); sandbox
   self-verify passed; stimuli hash-checked.
2. ✅ Single writer; no malformed/duplicate-success rows.
3. ✅ **Isolation byte-invariant holds (384/384)** — the Stage-2-specific gate.
4. ✅ Missingness reported before estimates; factor-correlated missingness disclosed.

Per the prereg's permitted claim: on this frozen item set, **context isolation and conflict
routing reduced wrong-reference capture relative to a contaminated score-only judge** —
supported for 3 of 4 admitted models. The claim does not extend to llama (all its intervals
include 0), to deepseek (not admitted), or to any named benchmark.

## What the code-domain replication (Stages 1+2 together) establishes

- **CCC generalises across substrates**: bare-conclusion capture in arithmetic and code
  (Stage 1, 4/5), and mirrored-reference capture in code (Stage 2, 3/4).
- **The safeguard ordering replicates**: isolation ≥ router ≫ written verification, with
  the router's relative standing *improved* in code (mechanical output comparison is
  reliable here).
- **Capture magnitude is format- and model-dependent** (llama: +44 in one format, +13 ns
  in another) — a reason benchmarks must probe their own exact prompt shape rather than
  import these numbers.

## Non-claims and caveats

- 16 hand-authored Python items; no claim about other languages, longer programs, or any
  named benchmark; magnitudes indicative (0/100 saturation), preregistered calls primary.
- Llama's not-supported calls are threshold decisions at n=16, not evidence of immunity
  (its point estimates are positive except the router's −0.8).
- The gemini correct-reference benefit and the llama format-sensitivity contrast are
  descriptive/hypothesis-generating (multiple comparisons).
- The router was tested with a *model* solver for parallelism with the numeric experiment;
  a deterministic test-oracle router (running the unit tests) remains declared future work
  and would plausibly dominate here.
