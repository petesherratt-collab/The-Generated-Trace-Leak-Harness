# Contextual Conclusion Capture — a research narrative

*How a leak-detection harness became a controlled study of why LLM judges lose the
ability to tell right answers from wrong ones when a conflicting conclusion sits in
their context.*

**Status:** working research write-up, 2026-07. Every claim below links to a findings
document with preregistration, streamed evidence, and fail-closed analysis. Read this as
the through-line; read the linked files for the numbers, caveats, and audit trails.

---

## 0. One-paragraph version

We set out to detect leaked information in generated traces. Repurposing the method as a
probe of **LLM-as-judge integrity**, we found that an evaluator can be made to mark a
*correct* answer wrong by placing a plausible wrong answer in its context. Across a sequence of
preregistered experiments of increasing rigor — a confirmation and causal architecture test
in arithmetic, then bounded replications in **two further computational-reasoning
paradigms, Python code and relational SQL** — the mechanism narrowed to a single active
ingredient. It is **not** the wrong answer's source label, and **not** its supporting
argument. It is the mere presence of a **conflicting conclusion**. We name this failure mode
**Contextual Conclusion Capture (CCC)**. The effect and its severity are **model- and
domain-dependent** (a judge robust in one domain is among the most captured in another);
written "verify first" instructions can reduce it but are not dependable; and the one intervention
that removes the pathway by construction — **keeping the foreign conclusion out of the
judge's context** (context isolation) — holds structurally, byte-audited, in every domain
tested. A later four-endpoint frontier confirmation reproduced SQL capture across GPT, Gemini
and Grok, narrowed code capture to GPT, and found Claude Fable captured in arithmetic while
provider filtering made its code/SQL behaviour unmeasurable. A conditional frontier verification
follow-up left supported residual capture for Fable arithmetic and GPT code, bounded the measurable
SQL residuals without proving equivalence, and made Gemini SQL unmeasurable through truncation.

---

## 1. Where it started: the generated-trace leak harness

The project began as [`generated_leak_harness_v151_selfcontained.py`](generated_leak_harness_v151_selfcontained.py):
a self-contained harness that runs a suspected component under **blind, mirrored controls**
(honest / collude / decouple / poison) and uses causal attribution to decide whether a
generated trace leaked information it should not have. Version 1.5.1 closed two real
attacks found in review — a deterministic-replay bypass and a full-file hash-pin bypass —
each demonstrated with a runnable adversary before the fix. (The v1.5 line is preserved
under `previous_versions/`.)

The method's transferable idea is the part that matters here: **to know whether a hidden
channel controls an output, you vary the hidden channel under matched controls and measure
the effect — you do not trust the system's self-report.** That is exactly what a benchmark
needs to know about its judge.

---

## 2. The pivot: is the judge grounded in the work, or in the answer key?

An LLM judge that grades a candidate against a reference answer has a hidden channel: the
reference. A *grounded* judge scores a correct answer highly whether the reference shown to
it is right or wrong, because it can re-derive the answer. A judge that is secretly
**anchored to the key** will mark a correct answer down when the key is a plausible wrong
value. That gap is measurable with the harness's own logic.

### 2.1 Pilot — reference-anchoring is real, and the fix is an interaction

[`FINDINGS.md`](experiments/results/FINDINGS.md) · 16 arithmetic items, 5 models, OpenRouter.

Injecting a **poisoned reference** made every score-only judge mark a mathematically
correct answer down (poison gap 0.50–1.00). A 2×2 factorial separated the two things a
naive "let it reason" fix conflates:

| | verify instruction: No | verify instruction: Yes |
|---|---|---|
| **score only** | A: all suspect | B: all suspect |
| **explanation + score** | C: mixed | **D: all pass (gap 0.00)** |

The verify *instruction alone was inert* (A→B). Requiring a *written worked solution* was
the main lever but incomplete (A→C: gpt-4o-mini and deepseek still anchored). Only the
**combination** drove the measured gap to zero for all five (D). Mitigation was an
**interaction**, not a main effect — and, being prompt-level, suspect on robustness
grounds.

### 2.2 Sensitivity matrix — the prompt fix is model-specific and wording-fragile

[`FINDINGS_sensitivity.md`](experiments/results/FINDINGS_sensitivity.md) · preregistered
([`PREREG_deepseek_sensitivity.md`](experiments/PREREG_deepseek_sensitivity.md)).

Holding the intervention class fixed and varying only *phrasing* (D0–D3), deepseek was
**robust** (0.00 across all four, zero run-to-run variance) while **gpt-4o-mini regressed
to 0.25 on D3** — the rigid "template" variant we'd have bet was the *most* structural. The
preregistration overturned our guess about which model was fragile.

The autopsy is the thesis in miniature. On the failing items, gpt-4o-mini **derived the
correct answer in its own written working and then scored the correct candidate 0.0**,
justifying it by "does not match the reference" — in one case literally asserting "8 does
not match my calculation of 8." Crucially, we do **not** infer from the transcript that the
score was decided first and the reasoning back-filled; this project's own thesis is that
visible reasoning does not reveal causal order. The **causal** evidence is the controlled
poison-vs-gold gap; the transcript is the visible *symptom*. Lesson: **visible, correct
reasoning is not evidence of what controlled the verdict.** That is the whole reason a
controlled probe is necessary.

---

## 3. If a prompt can't be trusted, change the architecture

### 3.1 Two-stage — withhold the reference from the scorer

[`FINDINGS_twostage.md`](experiments/results/FINDINGS_twostage.md).

The principle is stronger than any instruction: **information that must not influence a
decision should not enter the deciding component's context.** So: score blind to the
reference, then compare mechanically and route conflicts.

The honesty note here is load-bearing. "Two-stage gap = 0.00" is **structural, not
empirical** — if the verdict is taken from the blind call and never recomputed after the
reference appears, the gap *must* be zero; that tests the wiring, not the model. And the
blind scorer was reference-blind but **not candidate-blind**: the candidate can still steer
the "independent" derivation. That open channel defined the next experiment.

### 3.2 Three-stage — separate the solver from both channels (underpowered)

[`FINDINGS_threestage.md`](experiments/results/FINDINGS_threestage.md).

A solver blind to *both* candidate and reference, a judge grounded in the solver's sealed
solution, an auditor comparing outside the judge. The design is right, but **the items
weren't hard enough**: blind solver accuracy was ~100%, so the candidate→solver
contamination channel had nothing to exploit. The 0% pulls are **underpowered nulls, not
reassurance.** It did re-confirm that leaking the reference to the judge still anchors it
(gemini +0.20 even here).

---

## 4. What is the reference actually doing? Provenance vs content

The two-stage/three-stage work quarantined the reference but left the scientific question
open: *when a wrong answer does capture a judge, what property of it is responsible?* The
answer key is one instance of a more general object — a **foreign conclusion**. We built a
provenance × content factorial to take it apart.

### 4.1 Exploratory factorial — persuasion dominates (noisy, reps=1)

[`FINDINGS_provinj.md`](experiments/results/FINDINGS_provinj.md).

First read: even an **unlabelled** wrong analysis collapsed discrimination (content, not
provenance, is primary), a skepticism label partly restored it against a bare claim but was
overpowered by a persuasive wrong rationale, and a false "verified" badge worsened
deference. Framed then as "persuasion dominates, provenance modulates." But reps=1 and
n=8 made the per-label CIs wide — a hypothesis, not a result. A confound check (Phase 1)
confirmed the injected wrong analysis and the matching wrong candidate agreed at the
*conclusion* level, not by shared wording (word-4gram Jaccard 0.083).

### 4.2 Stage 2, preregistered — the reframing

[`FINDINGS_provinj_stage2.md`](experiments/results/FINDINGS_provinj_stage2.md) ·
[`PREREG_provenance.md`](experiments/PREREG_provenance.md).

With frozen contrasts, fail-closed missingness, and item-clustered bootstrap CIs, the
picture sharpened and, in one respect, **reversed**:

- **Injection harm** (wrong analysis, neutral label) — **supported**: a wrong conclusion
  collapses discrimination by ~40–68 points in score-only judging.
- **Provenance harm** (solver label vs neutral) — **not supported anywhere**; for llama it
  significantly *reversed*. Naming the source did not add capture.
- **Rationale harm** (full argument vs bare answer) — **not supported; often reversed**. A
  bare wrong number captured score-only judges as much as a full wrong argument.
- **Protocol mitigation** (score-only vs verify-written) — directionally positive for all,
  significant for gemini: written verification attenuates, doesn't abolish.

This retired the earlier "the sealed solver becomes the new answer key" reading. The active
ingredient is neither the badge nor the argument. It is the **competing conclusion itself**.

---

## 5. Contextual Conclusion Capture — the confirmation

We preregistered the confirmatory stage the stage-2 caveats demanded: **16 items, exactly
3 repetitions, a fresh schedule seed, five models, frozen texts and hashes.**

[`FINDINGS_contextual_conclusion_capture_confirmatory.md`](experiments/results/FINDINGS_contextual_conclusion_capture_confirmatory.md)
· [`PREREG_contextual_conclusion_capture_confirmatory.md`](experiments/PREREG_contextual_conclusion_capture_confirmatory.md).

> **Contextual Conclusion Capture:** *a failure mode in which an AI judge's ability to
> distinguish correct from incorrect candidates deteriorates merely because a conflicting
> conclusion is present in its evaluation context, independent of that conclusion's stated
> authority or supporting rationale.*

**The direct test — a bare, neutrally-labelled wrong conclusion under score-only judging —
was supported in all four measurable models:**

| Model | bare-conclusion harm [95% CI] | call |
|---|---|---|
| gpt-4o-mini | +55.10 [+21.77, +90.62] | supported |
| gemini-2.5-flash | +39.06 [+9.90, +74.58] | supported |
| deepseek-chat | +47.83 [+32.67, +66.79] | supported |
| llama-3.3-70b | +87.50 [+62.50, +112.50] | supported |
| claude-haiku-4.5 | (n=4) | unmeasurable |

The mechanism checks replicated: the **provenance increment was null** in every measurable
model (llama again significantly negative), and the **rationale increment was null** — the
bare conclusion did as much harm as the full rationale. **Written verification was a robust
mitigation** (supported in all four), but **llama retained large residual capture**. So the
conflicting conclusion is *sufficient*; verification helps but is not a universal cure.

Claude Haiku was **largely non-compliant with the score-only protocol** (only 4/16 items met
the completeness floor): asked for a bare score, it begins a written verification and
truncates. We report this as non-compliance **without attributing motive** — it makes the
model unbenchmarkable in the vulnerable mode, not demonstrably safe in it.

### Independent verification of this run

Before merging Codex's confirmatory branch, the raw evidence was re-checked from scratch:
row/dedup integrity (3,840 unique cells, **max 1 attempt per cell, 0 duplicate successes**),
and the four headline estimates above were **recomputed from the raw scores** to the
reported values with an independent bootstrap.

---

## 6. Does architecture fix it? The causal safeguard test

Confirming the failure is not the same as validating a remedy. The final experiment stops
asking a contaminated judge to *resist* and instead tests **pipeline designs**, crossing
each architecture with a mirrored correct/wrong external reference.

[`FINDINGS_contextual_capture_architecture.md`](experiments/results/FINDINGS_contextual_capture_architecture.md)
· [`PREREG_contextual_capture_architecture.md`](experiments/PREREG_contextual_capture_architecture.md).

Four architectures: `contaminated_score_only`, `contaminated_verify_written`,
`context_isolated_score_only` (the reference exists in pipeline metadata but never enters
the judge prompt), and `conflict_router` (a fresh question-only solve decides whether to use
the exposed path or quarantine the reference and send a clean written-verification judge).

- **Direct exposure to a wrong conclusion caused large discrimination loss in all four
  measurable models** — reproducing CCC as a causal contrast.
- **Context isolation is the most consistent safeguard**: it improved wrong-reference
  discrimination in all four measurable models, and it passes a **byte-level pathway
  audit** — all 480 isolated-judge prompt pairs are hash-identical across correct-vs-wrong
  reference, so the reference *provably* never reaches the judge. (Independently re-verified
  from the evidence file: 480/480 identical for isolation; 480/480 *differ* for both
  contaminated architectures.)
- **The conflict router is a promising prototype, not a universal fix**: it helped GPT and
  llama but its interval included zero for gemini and deepseek. Detecting a conflicting
  conclusion is easier than guaranteeing a reliable adjudication path.

---

## 7. What is established — and what is not

**Supported.**
1. CCC is real and preregistration-robust: a conflicting conclusion degrades score-only
   judge discrimination across four measurable models on this item set.
2. The conflicting conclusion is *sufficient* — neither a source label nor a long rationale
   is needed.
3. Written verification is a strong but incomplete mitigation (llama retains capture).
4. Context isolation removes the reference→judge pathway by construction (byte-level
   audited) and was the most consistent tested safeguard.

**Deliberately bounded.**
- The domain is **16 numerical/combinatorial items**, and the confirmatory + architecture
  runs **reuse the same item set** (the 8 new items use declared, human-audited decoy
  overrides because generation kept leaking the gold answer — disclosed and hashed). This is
  a larger-n, fresh-seed confirmation on a *shared, partly hand-crafted* domain, **not** an
  independent item-domain replication.
- Null provenance/rationale increments mean *not needed for the confirmed effect*, **not**
  *can never matter*. CIs containing zero are not proof of equivalence.
- The architecture result supports **conflict routing and context separation as stronger
  safeguards than prompt-level warnings or written-verification instructions alone** — it
  does **not** prove any one safeguard is uniquely complete, and it tests no named benchmark
  or production evaluator. A named-benchmark claim requires reproducing that system's actual
  judge prompt, reference visibility, ordering, routing, retry, and aggregation.
- Scores are coarse (0/100 saturation common); treat magnitudes as indicative and the
  preregistered support calls as the result.

---

## 8. Design implications

For anyone building or running an LLM-judged evaluation:

- **Keep foreign conclusions out of the first-pass judge context.** This is the only tested
  intervention that removes the pathway structurally rather than asking the model to resist.
- **Evaluate candidate and reference independently; compare their conclusions mechanically;
  expose conflict instead of allowing silent reconciliation; route disagreement to another
  source of verification** (deterministic checker, second independent solve, or human).
- **Do not ship a single-turn "verify and show working" prompt as a guaranteed defence.** It
  helps, it is model-specific, and it left residual capture for at least one model here.
- **Test the whole route under mirrored correct/wrong-reference sentinels.** A judge that
  passes only when the key is right is not grounded; a blatant leaker should be caught in the
  same condition the real items run in.

The [judge-integrity benchmark blueprint](experiments/BENCHMARK_BLUEPRINT_judge_integrity.md)
sketches an evaluation that makes these properties a **release gate**, not a hidden
assumption. For a visual summary of the two pipelines — the contaminated single-prompt
setup vs. the isolate/compare/route architecture — see
[`docs/PIPELINE_DIAGRAMS.md`](docs/PIPELINE_DIAGRAMS.md); for the experimental method
(investigation arc, atomic measurement, two-stage design, mechanism factorial, the four
architectures) see [`docs/EXPERIMENT_DIAGRAMS.md`](docs/EXPERIMENT_DIAGRAMS.md) (GitHub renders
the diagrams natively).

---

## 9. Domain generalization — three computational paradigms

The open question was whether CCC survives materially different problem types. It was tested
by two bounded, preregistered replications in domains that keep gold **mechanical and
non-circular** — the property that lets the study measure judge integrity without an
evaluator-for-the-evaluator.

### 9a. Code (imperative) — [`PREREG_ccc_codedomain.md`](experiments/PREREG_ccc_codedomain.md), unified [`FINDINGS_ccc_codedomain.md`](experiments/results/FINDINGS_ccc_codedomain.md)

Judges score Python implementations against a specification, with **unit-test gold** (a
sandboxed, hash-frozen grader — no model decides ground truth).

- **Stage 1** ([`FINDINGS_ccc_codedomain_stage1.md`](experiments/results/FINDINGS_ccc_codedomain_stage1.md)):
  the bare-conclusion primary contrast **supported in 4 of 5 models** (+36 to +44 points;
  deepseek's CI included zero by 0.21 points → not supported, per the frozen rule). **CCC is
  cross-substrate.** Notably, Claude Haiku — unmeasurable numerically due to score-only
  non-compliance — complied perfectly in code (0/384 failures) and, once measurable, was
  captured (+40): its earlier non-compliance was format-specific, not protective.
- **Stage 2** ([`FINDINGS_ccc_codedomain_stage2.md`](experiments/results/FINDINGS_ccc_codedomain_stage2.md)),
  conditional on the frozen capture threshold (4 admitted models): mirrored-reference
  susceptibility causal for 3/4; **context isolation and the conflict router both supported
  3/4** (isolation byte-audited again, 384/384 identical prompts); the router's mechanical
  detection near-perfect (+94 to +100pp) and its gain *exceeding* isolation's for gpt;
  **written verification supported for no model**. The safeguard ordering replicates —
  isolation ≥ router ≫ prompt-level verification — with the router strengthened in code,
  where comparing solved output values is exactly what a mechanical comparator does best.

Bounded conclusion for code: **model-dependent CCC replication with strong but non-universal
protection from context isolation.** Primary capture supported 4/5 (deepseek's CI included
zero by 0.21 points → not supported); isolation and router each supported 3/4 (isolation
byte-audited, 384/384); written verification supported for no model. Llama's safeguard
intervals all include zero; isolation is the strongest *tested* safeguard on the models where
capture was measured.

### 9b. Relational (declarative SQL) — [`PREREG_ccc_sql.md`](experiments/PREREG_ccc_sql.md), unified [`FINDINGS_ccc_sql.md`](experiments/results/FINDINGS_ccc_sql.md)

Judges score claimed query results against frozen SQLite fixtures, with the **SQLite oracle as
gold** (a fail-closed gold-signature gate aborts if the local SQLite would produce different
results — which caught nothing, correctly, when the run machine's SQLite 3.50.4 differed from
the 3.45.1 of development). This is the **strongest and most uniform** capture of the three
domains: the bare-conclusion primary is supported in **all five models at +106 to +153**
(≈2× the code magnitude), a genuine *reversal* (the judge scores the wrong result above the
correct one). All five entered Stage 2; **isolation restores reference-neutrality for all five
(byte-audited, correct-vs-wrong gap ≈ 0) and the router fully recovers discrimination for all
five** — its strongest showing, since comparing a canonical query result is exactly what a
mechanical comparator does best. Written verification's mitigation *delta* is large only
because the baseline is extreme; the **residual capture under verification remains supported
for 4/5 models** (deepseek +51, llama +56 large) — partial, as everywhere.

### 9c. What the three domains establish together

- **CCC generalizes across three computational-reasoning paradigms** — arithmetic, imperative
  code, declarative SQL — all with mechanical, non-circular gold.
- **Capture and its severity are model- and domain-dependent, decisively.** DeepSeek is *not
  captured* in code (+10, CI includes 0) yet **the most captured** in SQL (+153). A judge cannot
  be certified once and trusted elsewhere — the empirical backbone for a *per-release* integrity
  gate rather than a one-time certification.
- **Safeguard efficacy is domain-dependent too, with one invariant.** Written verification is
  partial in every domain and never a complete fix; the router recovers where mechanical
  comparison is clean (partial in code, total in SQL); **only context isolation carries a
  structural, byte-level guarantee that holds in every domain** — the reference provably cannot
  reach the judge, so its neutrality is construction, not behaviour.

Not a universally validated product safeguard: these are frozen micro-domains with coarse
0/100 judges and no named-benchmark claim. What remains open is narrower — other languages and
larger programs, and **open-ended domains where mechanical comparison itself becomes a
judgement** (deliberately excluded, because rigor there would require the very
evaluator-for-the-evaluator this method avoids) — plus the declared-but-untested deterministic
oracle router.

---

## 10. Frontier extension — what survived one tier up

[`FINDINGS_ccc_frontier.md`](experiments/results/FINDINGS_ccc_frontier.md) ·
[`PREREG_ccc_frontier.md`](experiments/PREREG_ccc_frontier.md) · independent audit
[`ccc_frontier_v3_audit.txt`](experiments/results/ccc_frontier_v3_audit.txt).

The next question was the obvious one left by a cost-tier panel: does CCC survive in stronger
judges? The confirmatory v3 run tested four frontier endpoints under `score_only` across the same
three mechanically graded domains: 16 arithmetic items, 16 code items, 24 SQL items, and 5,376
intended judge cells. The final instrument froze seed `305774821`, used a reproducible
`sha256(domain)` schedule, recorded both retry outcomes where provider attempts occurred, and
reported missingness by condition × candidate before interpreting an estimate.

| Domain | GPT-5.6-sol | Gemini-3.1-Pro | Grok-4.5 | Claude Fable |
|---|---:|---:|---:|---:|
| Arithmetic | not supported (−7.1) | not supported (+0.2) | not supported (−0.5) | **SUPPORTED +62.9** |
| Code | **SUPPORTED +11.2** | not supported (−2.5) | not supported (+1.4) | unmeasurable — content-filtered |
| SQL | **SUPPORTED +50.6** | **SUPPORTED +40.9** | **SUPPORTED +27.4** | unmeasurable — content-filtered |

Three things changed the story. First, **SQL capture survived the tier change cleanly**: GPT,
Gemini and Grok all show large confirmatory harm (+51, +41 and +27), with large descriptive
provenance increments (+88, +74 and +33). Second, code became narrower: GPT replicated (+11),
but Grok's exploratory v2 result (+5.7 with a barely positive lower bound) fell to +1.4 with an
interval crossing zero. Confirmatory replication earned its keep by rejecting a fragile signal.
Third, Fable showed an inverse domain profile: strong arithmetic capture (+63), but no valid
code or SQL estimate.

The Fable result is a missingness result, not an immunity result. Its endpoint produced
`content_filter` on 148 code cells and 27 SQL cells, concentrated in injected conditions. The
larger-budget retry fired but could not repair a provider filter. Because the surviving observations
are treatment-selected, the preregistered balance safeguard makes both contrasts **unmeasurable** —
including SQL's nominal positive estimate. The filter mechanism itself reproduced across diagnostic
and confirmatory runs.

The independent audit found all 5,376 intended rows, zero duplicate successes, a clean metadata
record (instrument commit `982b97e`, all four aliases validated, no forced models), and estimates
matching the runner. Fourteen cells failed with `worker:KeyError: 'choices'` before a usable provider
choice trace was recorded; they were retained and excluded fail-closed. Their low, non-systematic
rate changed no verdict, but remains an explicit audit exception.

The frontier result sharpens rather than overturns the central thesis: **CCC transfers across model
tiers most clearly in SQL, while susceptibility remains endpoint- and domain-specific.**

### Phase 2 — verify first, then score

[`FINDINGS_ccc_frontier_phase2.md`](experiments/results/FINDINGS_ccc_frontier_phase2.md) ·
[`PREREG_ccc_frontier_phase2.md`](experiments/PREREG_ccc_frontier_phase2.md) · independent audit
[`ccc_frontier_p2_audit.txt`](experiments/results/ccc_frontier_p2_audit.txt).

Phase 2 conditionally admitted only the five measurable pairs with supported Phase-1 capture. Its
headline was the residual harm still present under `verify_written`, not the raw improvement from the
larger score-only baseline.

| Domain / judge | Phase-1 harm | Phase-2 residual [95% CI] | Reading |
|---|---:|---:|---|
| Arithmetic · Fable | +62.9 | **+19.38 [+1.79, +39.13]** | capture persists |
| Code · GPT | +11.2 | **+8.10 [+3.02, +15.48]** | capture persists |
| SQL · GPT | +50.6 | −0.13 [−0.38, 0.00] | positive residual not supported |
| SQL · Gemini | +40.9 | not estimated | unmeasurable — truncation-skewed |
| SQL · Grok | +27.4 | +9.51 [−0.21, +22.01] | positive residual not supported |

The cross-domain contrast is the result. Verification substantially reduced Fable arithmetic but
left a supported residual; it barely moved GPT code; and it sharply reduced the measurable SQL
effects. GPT SQL is bounded very near zero, but the preregistration deliberately does not turn a
zero-touching interval into a proof of elimination. Grok's upper bound still allows a meaningful
residual. Gemini's verification responses were longer on injected cells: four primary responses and
six solver-rationale responses truncated after both budgets, making the primary completion gap 5.56%
and the contrast unmeasurable.

The audit also corrected two tempting mechanism stories. Fable's five arithmetic misses were late
HTTP 402 billing failures, not content filters; Gemini's SQL failures were truncation, not filtering.
All 2,496 intended rows exist with zero duplicate successes. The three invocations did overwrite one
shared metadata file, so arithmetic/SQL configuration is reconstructed from the frozen preregistration,
terminal record, and complete raw rows—an explicit audit exception.

The conclusion is narrower and stronger than “verification failed” or “verification worked”:
**written self-verification is a model- and domain-specific attenuation, not a structural safeguard.**
The frontier phase did not test context isolation or the conflict router; those remain supported only
by the small-tier architecture experiments.

---

## 11. OpenRouter extension — four additional full arms

[`FINDINGS_ccc_openrouter_openweight.md`](experiments/results/FINDINGS_ccc_openrouter_openweight.md) ·
[`PREREG_ccc_openrouter_panel.md`](experiments/PREREG_ccc_openrouter_panel.md) · model-specific
preregistrations, raw evidence, and independent audits under `experiments/results/ccc_openrouter_*`.

The final extension asked whether the frontier pattern survived in a different set of routed model
families and whether a pilot-first workflow could avoid another expensive protocol mismatch. Four
complete 1,344-cell arms resulted: Qwen 3.7 Plus, Kimi K2.7 Code, MiniMax M3, and GLM 5.2. This is an
endpoint comparison, not a model-license audit; Qwen is retained as the hosted comparator.

| Model | Frozen response protocol | Arithmetic | Code | SQL |
|---|---|---:|---:|---:|
| Qwen 3.7 Plus | bounded reasoning, Alibaba | **SUPPORTED +94.17** | not supported (-9.27) | **SUPPORTED +165.28** |
| Kimi K2.7 Code | native reasoning, Together | not supported (-11.88) | not supported (+1.46) | **SUPPORTED +70.69** |
| MiniMax M3 | no reasoning, Minimax | **SUPPORTED +75.17** | **SUPPORTED +19.65** | **SUPPORTED +143.68** |
| GLM 5.2 | no reasoning, Together | **SUPPORTED +52.08** | not supported (+13.33) | **SUPPORTED +148.61** |

The invariant is now difficult to dismiss as one provider family: **every one of the four complete
arms shows supported SQL capture**. Arithmetic capture is common but not universal, and code remains
model-specific. MiniMax is the only arm with a supported primary effect in all three domains. GLM's
primary code interval crosses zero, although its descriptive provenance increment is large (+52.1).

Kimi's first pilot failed for a useful reason: the endpoint spends heavily on native reasoning and
cannot satisfy a terse low-budget response contract. A separately preregistered native-reasoning arm
made it measurable without pretending it was protocol-identical to MiniMax or GLM. Conversely,
MiniMax and GLM used zero observed reasoning tokens yet still showed large arithmetic and SQL effects.
Capture therefore does not require a long chain of thought, and native reasoning does not reliably
protect the SQL judgement.

All four full arms contain 1,344 unique successful cells with complete condition × candidate strata.
The two final no-reasoning arms added 2,688 complete cells for $0.38309156 including launch
preflights, with zero final failures, retries, endpoint drift, or nonzero reasoning records. The
pilot-first workflow converted earlier odd endpoint behaviour into frozen, endpoint-valid protocols
rather than paying full-run prices to rediscover incompatibilities.

The final cross-tier conclusion is consequently both broader and more qualified: **SQL conclusion
capture is robust across the tested endpoint families, while arithmetic and code sensitivity remain
strongly release- and domain-dependent.**

---

## Appendix — methodology and integrity practices

The results are meant to be auditable end-to-end:

- **Preregistration before each confirmatory run** — contrasts, decision rules, fail-closed
  missingness handling, and stop rules frozen in advance (`PREREG_*.md`), with SHA-256 hashes
  on items, effective stimuli, runner, and analysis code.
- **Streamed evidence** — every judge attempt appended to JSONL as it happens, with a
  hash-keyed prompt manifest; failed attempts retained, never averaged with successes.
- **Fail-closed analysis** — an item enters a contrast only when all required cells and
  repetitions succeeded; missingness is reported *before* any estimate and never interpreted
  as safety.
- **One successful row per cell** — dedup key `(item, model, condition, candidate, rep,
  protocol)`; more than one success is a hard error. Row accounting is stated explicitly in
  each findings file.
- **Independent re-verification** — headline numbers and structural invariants recomputed
  from raw evidence, not taken on trust.

### Experiment index

| # | Experiment | Findings |
|---|---|---|
| 1 | Reference-anchoring pilot + 2×2 factorial | [`FINDINGS.md`](experiments/results/FINDINGS.md) |
| 2 | Wording-sensitivity matrix + D3 autopsy | [`FINDINGS_sensitivity.md`](experiments/results/FINDINGS_sensitivity.md) |
| 3 | Two-stage (reference withheld from scorer) | [`FINDINGS_twostage.md`](experiments/results/FINDINGS_twostage.md) |
| 4 | Three-stage (solver blind to both channels) | [`FINDINGS_threestage.md`](experiments/results/FINDINGS_threestage.md) |
| 5 | Provenance × content factorial (exploratory) | [`FINDINGS_provinj.md`](experiments/results/FINDINGS_provinj.md) |
| 6 | Stage-2 preregistered — CCC reframing | [`FINDINGS_provinj_stage2.md`](experiments/results/FINDINGS_provinj_stage2.md) |
| 7 | Confirmatory (16 items, 3 reps, fresh seed) | [`FINDINGS_contextual_conclusion_capture_confirmatory.md`](experiments/results/FINDINGS_contextual_conclusion_capture_confirmatory.md) |
| 8 | Architecture / causal safeguard test | [`FINDINGS_contextual_capture_architecture.md`](experiments/results/FINDINGS_contextual_capture_architecture.md) |
| 9 | Code-domain replication, Stage 1 (injection) | [`FINDINGS_ccc_codedomain_stage1.md`](experiments/results/FINDINGS_ccc_codedomain_stage1.md) |
| 10 | Code-domain replication, Stage 2 (architectures) | [`FINDINGS_ccc_codedomain_stage2.md`](experiments/results/FINDINGS_ccc_codedomain_stage2.md) |
| 11 | Relational (SQL) replication, Stage 1 (injection) | [`FINDINGS_ccc_sql_stage1.md`](experiments/results/FINDINGS_ccc_sql_stage1.md) |
| 12 | Relational (SQL) replication, Stage 2 (architectures) | [`FINDINGS_ccc_sql_stage2.md`](experiments/results/FINDINGS_ccc_sql_stage2.md) |
| 13 | Frontier-tier confirmation, Phase 1 (arithmetic/code/SQL) | [`FINDINGS_ccc_frontier.md`](experiments/results/FINDINGS_ccc_frontier.md) |
| 14 | Frontier-tier conditional Phase 2 (`verify_written`) | [`FINDINGS_ccc_frontier_phase2.md`](experiments/results/FINDINGS_ccc_frontier_phase2.md) |
| 15 | OpenRouter four-arm extension (Qwen/Kimi/MiniMax/GLM) | [`FINDINGS_ccc_openrouter_openweight.md`](experiments/results/FINDINGS_ccc_openrouter_openweight.md) |

*Investigation ordering reflects how understanding developed, including a hypothesis
(authority deference) that the clean experiments falsified. The falsification is part of the
result.*
