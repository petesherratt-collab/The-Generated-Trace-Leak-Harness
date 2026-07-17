# Findings — the code-domain CCC replication (unified: Stages 1 + 2)

**One preregistered study, two frozen stages, run 2026-07-16/17** ·
**Prereg:** [`../PREREG_ccc_codedomain.md`](../PREREG_ccc_codedomain.md) ·
Stage records (full detail, audits, per-contrast tables):
[Stage 1 — injection](FINDINGS_ccc_codedomain_stage1.md) ·
[Stage 2 — architectures](FINDINGS_ccc_codedomain_stage2.md)

## Scope, stated first

This is a **bounded replication**: Contextual Conclusion Capture (CCC), previously
established on 16 numeric items, tested in one materially different but still
mechanically-verifiable domain — judging Python function implementations against a
specification, with **unit-test gold computed by a sandboxed, hash-frozen grader** (no
model ever decides ground truth). Sixteen hand-authored items, five judge models, frozen
seeds, fail-closed analysis. It licenses claims about *this design in this domain*: not
other languages, not larger programs, not open-ended evaluation, and **no named benchmark**
(HumanEval/MBPP/SWE-bench would each require reproducing their real prompt, reference
visibility, ordering, and routing).

## The replication in one paragraph

A bare, neutrally-labelled wrong conclusion placed in a code judge's context degraded its
ability to distinguish correct from buggy implementations in **4 of 5 models** (Stage 1,
+36 to +44 points; the fifth missed the frozen support rule by 0.21 points of CI). On the
four captured models, mirrored correct/wrong references confirmed the effect causally in
3 of 4 (Stage 2), and the safeguard ordering found numerically **replicated**: **context
isolation** (reference provably absent from the judge prompt — byte-audited, 384/384
identical) and **mechanical conflict routing** (detection +94 to +100pp) each recovered
discrimination for 3 of 4 models, while **written verification cleared the support rule
for none**. CCC is a cross-substrate phenomenon, and the structural remedies — not the
prompt-level ones — are what survive contact with a second domain.

## Design (both stages under one freeze)

| | Stage 1 — injection | Stage 2 — architectures (conditional) |
|---|---|---|
| Question | Does a conflicting conclusion capture code judges? | Do the validated safeguards fix it? |
| Cells | 3,840 (16×5×4 conditions×2 candidates×2 protocols×3 reps) | 3,072 + 192 router solves (16×4×4 archs×2 refs×2×3) |
| Seed | 517293846 | 517293847 |
| Models | all 5 | **the frozen Stage-1 capture subset**: gpt-4o-mini, claude-haiku-4.5, gemini-2.5-flash, llama-3.3-70b; deepseek excluded (primary not supported) |
| Success | 3,794 / 3,840 (98.8%) | 3,043 / 3,072 (99.1%); 192/192 solves |

Stage 2's model set was **frozen by rule at the moment Stage-1's primary contrast was
computed** (supported AND estimate ≥ +10) — it is a conditional test on the captured
subset, not an all-model comparison. Integrity audits for both stages: one row per cell,
max 1 attempt, zero duplicate successes, every estimate recomputed independently from raw
scores, all evidence streamed with hash-keyed prompt manifests.

## Factor-correlated missingness (preserved, disclosed, never interpreted as safety)

Missingness was not random noise; it tracked specific model × protocol factors, and the
fail-closed rules turned it into explicit unmeasurability rather than silent bias:

- **Gemini 2.5 Flash × written verification — 74 of the 75 total failures across both
  stages** (Stage 1: 45; Stage 2: 22 in contaminated-verify + 7 in the router, whose
  quarantine path *is* a verify-written judge). Truncation before the score JSON, worse on
  buggy candidates (31 vs 14 in Stage 1 — plausibly longer derivations). Consequences,
  applied per the frozen floor: gemini's protocol-mitigation contrast **unmeasurable in
  both stages** (n=9, then n=7); its Stage-2 router gain ran at n=14. The one remaining
  failure was a single llama cell (its Stage-1 primary ran at n=15).
- **Claude Haiku × score-only — the compliance reversal.** Numerically, Claude refused the
  bare-score format (42% failure) and was unmeasurable; here it complied **perfectly
  (0/384 score-only failures, per-cell repetition SD 0.00)** — and, once measurable, was
  captured (+40.0 in Stage 1, +46.6 susceptibility in Stage 2). Its earlier
  non-compliance was format/domain-specific behaviour, **not** a protective property —
  previously left uninterpreted on principle, now resolved by direct evidence.

## Model-specific results (preserved; no cross-model averaging)

| Model | S1 bare-conclusion harm (score-only) | S2 susceptibility | S2 isolation gain | S2 router gain | S2 verify mitigation |
|---|---:|---:|---:|---:|---:|
| gpt-4o-mini | **+36.5 ✅** | **+35.4 ✅** | **+32.7 ✅** | **+51.4 ✅** | +22.4 ✗ |
| claude-haiku-4.5 | **+40.0 ✅** | **+46.6 ✅** | **+43.8 ✅** | **+48.6 ✅** | −17.5 ✗ |
| gemini-2.5-flash | **+11.9 ✅** | **+29.2 ✅** | **+21.0 ✅** | **+28.2 ✅** (n=14) | unmeasurable (n=7) |
| llama-3.3-70b | **+44.0 ✅** (n=15) | +13.1 ✗ | +11.7 ✗ | −0.8 ✗ | −5.5 ✗ |
| deepseek-chat | +10.2 ✗ (CI incl. 0 by 0.21) | — not admitted — | — | — | — |

(✅ = preregistered support rule met: 95% item-clustered CI excludes 0, ≥ 12/16 items.
Router *detection* was supported for all four admitted models, +94 to +100pp.)

The heterogeneity is a result, not noise:

- **gpt, claude, gemini** — captured, and structurally repairable: isolation and routing
  both supported; for gpt the router *exceeds* isolation (+51 vs +33) because its
  quarantine path (fresh verify-written judge) is a stronger protocol than bare scoring.
- **llama** — the most captured model in Stage 1's injection format (+44) shows nothing
  supported in Stage 2's reference format (+13 ns). Tested explanation: a correct
  reference does **not** damage it (−1.0, clean null) — it is simply mildly captured by
  this wording/position. Capture is **format-sensitive per model**, which is itself a
  reason benchmarks must probe their own exact prompt shape rather than import anyone
  else's numbers.
- **deepseek** — excluded by the frozen threshold; a threshold decision at this n, not
  evidence of immunity (its point estimate was positive).
- **Descriptive** (not preregistered): gemini judges significantly *better* with a
  correct reference (−9.4 harm) — references help when right and damage when wrong,
  which is the design tension mechanical routing resolves.

## What the unified replication establishes — and what it does not

**Established (within scope):**
1. CCC generalises across substrates: arithmetic and code judging, same phenomenon, same
   bare-conclusion sufficiency.
2. The safeguard ordering replicates: **isolation ≥ router ≫ written verification** —
   with the router strengthened in code, where mechanical output comparison is exactly
   what a comparator does best (192/192 parseable solves), and verification failing the
   support rule for every model against reference-shaped contamination.
3. Isolation's guarantee is structural, not statistical: in both stages' architecture
   tests the isolated judge's prompts were **byte-identical across reference variants**.

**Not established:** anything beyond this design's boundary — other languages, program
scale, open-ended domains (where mechanical comparison itself becomes a judgement), named
benchmarks, or immunity for any model whose interval included zero. The deterministic
test-oracle router (running the unit tests as the conflict signal instead of a model
solve) is declared future work and untested.

**Effect sizes are format- and domain-dependent** (Stage-1 code effects ≈ half the numeric
ones; llama's +44 → +13 across formats). Directions and the preregistered support calls
are the result; magnitudes are indicative.
