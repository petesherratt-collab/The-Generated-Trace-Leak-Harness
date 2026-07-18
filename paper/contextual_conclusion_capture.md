# Contextual Conclusion Capture: Conflicting Conclusions Degrade LLM-Judge Discrimination Across Reasoning Domains

**Author:** Pete Sherratt · *affiliation and contact to be completed before submission*

**Preprint draft — 2026-07 (revised).** All numeric results are produced by preregistered,
publicly committed experiments with streamed evidence and an independently implemented
re-analysis from the raw rows; see the Reproducibility appendix for exact artifacts, immutable
commit references, hashes, and per-result findings files.

---

## Abstract

Large language models are increasingly used to *judge* the outputs of other models, often by
comparing a candidate answer against a reference. We identify and characterise a failure mode we
call **Contextual Conclusion Capture (CCC)**: an LLM judge's ability to distinguish correct from
incorrect candidates deteriorates when a *conflicting conclusion* is present in its evaluation
context. Through preregistered experiments across five model endpoints, we show that neither an
authoritative source label nor an elaborate supporting argument is *necessary* for the effect: a
**bare, neutrally-labelled wrong answer is sufficient** to induce capture. We then test whether the
failure survives a change of reasoning domain, using three domains that admit an executable oracle
for correctness: arithmetic word problems, Python function implementations (graded against a frozen
unit-test suite), and relational SQL queries (SQLite). CCC replicates in all three, but its
magnitude and *which models are affected* are **domain-dependent**: a judge not significantly
captured in the code domain is among the most affected in the SQL domain, where every one of the
five models is captured strongly enough to *reverse* its ordering (scoring the wrong answer above
the correct one). We evaluate three mitigations under mirrored correct/wrong-reference sentinels.
Prompt-level written verification reduces but does not eliminate capture in any domain. A **hybrid
conflict-router** — an independent model solve, followed by a deterministic comparison of
conclusions — recovers discrimination where that comparison is clean. And **context isolation** —
never placing the foreign conclusion in the judge's prompt — is the only tested safeguard that
**removes the reference-to-judge pathway by construction**, which we verify by showing the judge's
prompt is byte-identical whether the reference is correct or wrong. We are careful to distinguish
this *structural* guarantee (the pathway is absent) from a behavioural one (the judge is correct):
isolation removes the tested channel, not all sources of error. We argue evaluator integrity should
be treated as a **per-release, per-domain** property rather than one established once, and release
all items, harnesses, preregistrations, and evidence.

---

## 1. Introduction

"LLM-as-a-judge" is a default tool for evaluating open-ended model behaviour, powering
leaderboards, preference-data pipelines, and regression tests. A judge is typically shown a task, a
candidate answer, and sometimes a reference answer, and asked to score or compare. This convenience
rests on an unstated assumption: that the judge grounds its verdict in the *evidence* (the task and
the candidate), not in whatever other conclusions share its context.

We show that assumption fails in a specific, reproducible way. When a conflicting conclusion — for
example, a plausible but wrong "reference" answer — is placed in the judge's context, the judge
often stops grading the candidate on its merits and instead grades it by *agreement with the
conflicting conclusion*. We call this **Contextual Conclusion Capture (CCC)**.

Contributions:

1. **Mechanism, stated as sufficiency rather than falsification.** A source label ("Solver") and a
   full supporting argument each add nothing detectable over a neutral bare answer; a bare wrong
   answer is *sufficient* to induce capture (§5.2). We do not claim authority or persuasion can
   never matter — only that neither is necessary here.
2. **Generality with heterogeneity.** CCC replicates across three domains with executable
   correctness oracles — arithmetic, imperative code, relational SQL — and both the size of the
   effect and *which models are affected* differ by domain (§6). Robustness does not transfer.
3. **What prevents it, and in what sense.** Under mirrored sentinels we compare three mitigations.
   Written verification is partial in every domain; a hybrid router recovers discrimination where
   the underlying comparison is clean; and **context isolation removes the reference-to-judge
   pathway by construction**, which we verify byte-for-byte. We separate this structural claim from
   any claim of correct judging (§7).

Every experiment was preregistered before data collection, uses fail-closed handling of missing
observations, streams auditable evidence, and was re-analysed by an independently implemented
pipeline reading the raw rows. Measuring a judge's integrity is itself a judgement problem, and the
study is designed so no model establishes the correctness labels it is evaluated against.

---

## 2. Related work

**LLM-as-a-judge and its biases.** Using strong LLMs as evaluators was popularised by MT-Bench and
Chatbot Arena (Zheng et al., 2023) and reference-based variants such as G-Eval (Liu et al., 2023).
Documented biases include position/order effects (Wang et al., 2023) and verbosity / self-preference
(Panickssery et al., 2024). CCC is distinct: it is not a preference over surface features of the
*candidate*, but a deterioration of *discrimination* caused by a conflicting conclusion elsewhere in
context, separable (we show) from authority and argument quality.

**Sycophancy and anchoring.** LLMs tend to agree with assertions in context and defer to stated
beliefs (Sharma et al., 2023). CCC can be read as an evaluation-time anchoring effect, but our
controls show the anchor need not be authoritative or argued, which distinguishes it from pure
authority-deference.

**Prompt injection.** Indirect prompt injection studies untrusted context subverting behaviour
(Greshake et al., 2023). CCC is a benign-context analogue: the "injection" is an ordinary wrong
reference answer of the kind evaluation pipelines routinely paste into judge prompts, and the harm
is silent mis-scoring rather than hijacked instructions.

**Reasoning and verification.** Chain-of-thought (Wei et al., 2022) and self-consistency (Wang et
al., 2022) improve task accuracy. A natural hypothesis is that asking the judge to reason/verify
first would cure CCC; we test this and find it reduces but does not eliminate the effect in any
domain.

*Bibliographic details in the References section should be verified against primary sources before
submission; they were compiled without live access to bibliographic databases.*

---

## 3. Definitions

Each judging cell yields a score \(s \in [0,100]\). For an item with a known-correct candidate and a
matched known-wrong candidate, **discrimination** is

> D = mean s(correct) − mean s(wrong),  with s ∈ [0,100], so **D ∈ [−100, +100]**.

D > 0 means the judge scores correct candidates above wrong ones. We introduce a **conflicting
conclusion** into the judge's context — a claim, presented as a neutral reference note, that the
answer is the *wrong* value — and measure

> harm = D(no injection) − D(injection),  **harm ∈ [−200, +200]**.

In the mirrored-reference design, the same item is judged with a *correct* and a *wrong* reference,
and

> susceptibility = D(correct reference) − D(wrong reference),  **∈ [−200, +200]**.

The ±200 range explains estimates above 100: a judge that goes from D = +90 (scores correct above
wrong) to D = −90 (scores wrong above correct) has harm = +180.

> **Contextual Conclusion Capture** is harm > 0: a conflicting conclusion in context degrades a
> judge's ability to distinguish correct from incorrect candidates. When harm exceeds the baseline
> D, discrimination becomes negative — the judge **reverses**.

---

## 4. Method

**Models.** Five hosted endpoints across four providers, via a common API router:
`openai/gpt-4o-mini`, `anthropic/claude-haiku-4.5`, `google/gemini-2.5-flash`,
`deepseek/deepseek-chat`, `meta-llama/llama-3.3-70b-instruct`. These are cost-efficient models; our
claims concern the *existence and structure* of the failure, not a ranking of frontier systems (see
Limitations). Model names are provider aliases whose backing may change over time; run dates and the
metadata each run records are in the Reproducibility appendix.

**Operational gold under a frozen oracle.** Correctness is never decided by a model. In every domain
the correct and wrong candidates are produced or graded by an executable oracle: arithmetic computed
in code; Python graded against a **frozen unit-test suite** run in a sandbox; SQL results from
SQLite. We call the resulting label *operational gold under the frozen oracle* rather than absolute
ground truth. This distinction matters most for code: passing a fixed unit-test suite is not a proof
of general semantic correctness, and the wrong candidates are hand-authored single-fault variants
whose faults were audited to be behaviour-visible on the suite. Arithmetic and SQL have exact
executable answers; code correctness is relative to the frozen tests. What all three share, and what
the study requires, is that **no model establishes the labels** — avoiding the circularity of
measuring a judge with a judge.

**Design.** Each domain runs a two-stage design. **Stage 1 (injection)** crosses items × 5 models ×
4 conditions × 2 candidate types × 2 protocols × 3 repetitions. Conditions factor the conflicting
conclusion into *content* × *label*: `no_injection`; `neutral/answer_only` (bare wrong result — the
**primary** condition); `neutral/full_wrong_rationale`; and `solver/full_wrong_rationale`
(authoritative label). Protocols are `score_only` and `verify_written` (work it out first, then
score). **Stage 2 (architectures)** is *conditional*: it runs only on the models admitted by the
Stage-1 capture threshold (§5.3, §8), crossing four architectures × mirrored correct/wrong references
× candidates × repetitions.

**Statistics.** For each model and contrast, the estimate is a within-item paired difference,
aggregated by first averaging a cell's 3 repetitions, then forming the item-level discrimination,
then averaging over items. Uncertainty is an **item-clustered nonparametric bootstrap** (resampling
items with replacement): the analysis adapters use B = 4,000 resamples; the independent re-analysis
uses B = 4,000–10,000; seeds are fixed in code. We report 95% percentile intervals. An effect is
**supported** iff its interval excludes zero in the predicted direction *and* a completeness floor is
met (≥75% of items). **No multiplicity correction is applied**: the primary contrast is a single
preregistered test per model; all secondary and mechanism contrasts are reported descriptively with
intervals and are **not** equivalence tests — an interval covering zero is not evidence of no effect.
Where we compare models, overlapping intervals are treated as a conservative tie, not a significance
test.

**Preregistration and integrity.** For each confirmatory run we froze, before any API call: items
and their hash, conditions, primary/secondary contrasts, decision rule, repetitions and schedule
seed, model set, and missingness policy. Analysis is **fail-closed**: an item enters a contrast only
if all required repetitions of every required cell succeeded; missingness is reported before any
estimate and never interpreted as safety. Evidence is streamed to append-only JSONL with a hash-keyed
prompt manifest; the deduplication key is the frozen cell identity; at most one successful observation
per cell is permitted. In the mechanically-gradable domains the run recomputes a **gold-signature** at
start and aborts if the local oracle would produce different results (this fired usefully in SQL when
the run machine's SQLite 3.50.4 differed from the 3.45.1 of development, and matched).

---

## 5. Establishing the phenomenon and its mechanism (arithmetic)

**The phenomenon and the fragility of prompt fixes.** In a 16-item arithmetic pilot, injecting a
poisoned reference collapsed discrimination for every model under score-only judging. A 2×2 factorial
separating a *verify instruction* from a *requirement to show written work* found the instruction
alone inert, written work the main lever but incomplete for some models, and only the combination
driving the measured gap to zero — an interaction, not a main effect. A preregistered
wording-sensitivity matrix showed the prompt-level fix is model-specific and phrasing-fragile: one
model regressed on the most rigid "structural-looking" template. An audit of failing transcripts
found the judge computing the correct answer in its own working and then scoring the correct candidate
zero — in one case asserting "8 does not match my calculation of 8." The verdict was controlled by the
reference, not by the demonstrably-correct computation. Motivation: **visible reasoning does not reveal
what controlled the verdict.**

**Provenance and rationale are not necessary (§5.2).** A provenance × content factorial, confirmed in
a separate preregistered run, isolates the active ingredient. Naming the source ("Solver") added no
detectable capture over a neutral label in any model, and for one model *reduced* it; a full wrong
rationale did not add detectable capture over a bare wrong answer. We therefore conclude that **neither
authority nor argument is necessary** for CCC in these experiments, and that a bare neutral conclusion
is **sufficient**. We do not claim these factors can never matter: the mechanism contrasts are not
equivalence tests, and their intervals covering zero bound, but do not exclude, small effects.

**Conditional architecture test (§5.3).** A causal architecture experiment (16 items, mirrored
references) compared four pipelines: a contaminated score-only judge; a contaminated verify-written
judge; a **context-isolated** judge that never receives the reference; and a **hybrid conflict-router**
(described in §7). Because Stage 2 runs only on models the Stage-1 threshold admitted, its estimates are
**conditional on selection** and its denominators are *admitted measurable models*, not all five
endpoints. On this item set, context isolation was the most consistent safeguard and passed a byte-level
audit (every isolated prompt hash-identical across reference variants); the router helped some models;
written verification attenuated but did not abolish capture. Full numbers:
`experiments/results/FINDINGS_contextual_conclusion_capture_confirmatory.md`,
`.../FINDINGS_contextual_capture_architecture.md`.

---

## 6. Domain generalization

Both prior domains are, at bottom, "compute a deterministic result." To test whether CCC is an artifact
of that task shape, we replicated the full two-stage design in two further domains with executable
correctness oracles. **We treat domain as an observed factor, not a randomized one:** the domains differ
not only in reasoning type but in prompts, candidate construction, baseline task difficulty, answer
representation, and score saturation. We therefore report *observed* magnitudes per domain and do not
attribute magnitude differences causally to "domain."

### 6.1 Code (imperative program semantics)

The judge scores a Python implementation against a specification; gold is a frozen unit-test suite run
in a sandbox. The bare-conclusion primary was **supported in 4 of 5 models** (+36 to +44 points);
DeepSeek's interval included zero by 0.21 points and, per the frozen rule, was called *not supported*.
A side result: Claude Haiku, which in arithmetic refused the bare-score format on 42% of score-only
cells and was unmeasurable there, complied fully in code (0 failures) and, once measurable, was captured
(+40) — its earlier non-compliance was format-specific, not protective. In the conditional Stage 2
(4 admitted models; **DeepSeek was not tested architecturally in code**), context isolation and the
router were each supported for 3 of 4 *admitted measurable* models (isolation byte-audited, 384/384
identical prompt pairs); written verification was supported for **no** model.
`experiments/results/FINDINGS_ccc_codedomain.md`

### 6.2 Relational (declarative SQL)

The judge scores a claimed query result against a frozen SQLite fixture; gold is the SQLite oracle,
protected by the gold-signature gate. This domain showed the **largest observed capture** of the three.
The bare-conclusion primary was supported in **all five models at +106 to +153 points**. A per-arm
decomposition shows a *reversal*: with no injection the judge scores correct high and wrong low; with the
bare wrong-result note, correct collapses toward 0 and wrong rises toward the injected value, so
discrimination goes negative. The same judges discriminate correctly when not injected, ruling out a
pure saturation artifact.

| Model | baseline D | injected D | correct: base→inj | wrong: base→inj |
|---|---:|---:|---:|---:|
| gpt-4o-mini | +31.6 | −80.6 | 79.9 → 0.0 | 48.3 → 80.6 |
| claude-haiku-4.5 | +54.2 | −58.3 | 79.2 → 4.2 | 25.0 → 62.5 |
| gemini-2.5-flash | +41.2 | −83.3 | 63.5 → 0.0 | 22.3 → 83.3 |
| deepseek-chat | +67.8 | −85.4 | 92.1 → 2.1 | 24.2 → 87.5 |
| llama-3.3-70b | +41.4 | −66.7 | 80.6 → 0.0 | 37.3 → 66.7 |

All five entered Stage 2. Isolation drove the correct-vs-wrong-reference gap to ≈ 0 for every model
(byte-identical prompts, 720/720). The router recovered discrimination for all five. Written
verification's mitigation *delta* is large, but the honest measure — residual capture still present
under verification — remains supported for 4 of 5 models (small for GPT and Claude, ≈0 only for Gemini,
+50.9 for DeepSeek and +56.2 for Llama). `experiments/results/FINDINGS_ccc_sql.md`

### 6.3 Cross-domain synthesis

| | Arithmetic | Code | SQL |
|---|---|---|---|
| Primary capture (score-only) | supported (4/4 measurable) | supported 4/5 | supported 5/5 |
| Observed magnitude (points) | +39 to +88 | +12 to +44 | +106 to +153 |
| Isolation (byte-audited) | most consistent | 3/4 admitted | 5/5, gap → 0 |
| Hybrid router | partial (some models) | 3/4 admitted | 5/5 |
| Written verification | partial | supported for none | partial (residual 4/5) |

*Denominators are admitted, measurable models — the conditional Stage-2 subset — not all five
endpoints; "3/4" excludes both non-admitted and unmeasurable models.*

Two findings cut across the table. First, **capture and its severity are model- and domain-dependent**:
DeepSeek is *not* significantly captured in code (+10.2, CI includes 0) yet is *the most* captured in SQL
(+153). A judge's robustness in one domain does not transfer to another. Second, **safeguard efficacy is
also domain-dependent, with one structural invariant**: written verification is partial everywhere; the
router recovers where the underlying conclusion-comparison is clean; and **only context isolation removes
the reference-to-judge pathway by construction**, which we can audit at the byte level. Its guarantee is
about the *pathway*, not about the correctness of the resulting judgement.

We note, without claiming, a pattern consistent with the data: the domain with the largest observed
capture (SQL) also has the lowest baseline discrimination, consistent with judges leaning more on an
injected result when the task is harder to verify. Domain was not randomized, so this is a hypothesis
for future work, not a causal result.

---

## 7. Mitigations, precisely described

- **Written verification** (a prompt-level protocol) reduces capture but is incomplete in every domain.
  In SQL its large mitigation *delta* is an artifact of an extreme baseline; the residual capture under
  verification is still supported for 4 of 5 models.
- **The conflict-router is hybrid, not fully mechanical.** A model produces an independent conclusion by
  solving the task in a separate context; deterministic code then canonicalises and compares that
  conclusion against the external reference; routing (use the exposed path on agreement, quarantine to a
  fresh reference-free judge on disagreement or unparseable output) is mechanical *after* that comparison.
  The router therefore inherits the solver's fallibility: in SQL, 334 of 360 solver outputs were parseable,
  the remainder fail-safing to quarantine. A **deterministic test-oracle router** — using the unit tests or
  the SQLite oracle itself as the conflict signal, with no model in the loop — is specified but **untested**
  here, and would be the stronger variant.
- **Context isolation** removes the reference from the judge's prompt entirely. We verify, byte-for-byte,
  that the judge's prompt is identical whether the reference is correct or wrong (480/480, 384/384, and
  720/720 identical pairs in the three architecture experiments), so the reference-to-judge pathway is
  provably absent. This is a structural property of the pipeline, not a behavioural property of the model:
  isolation removes the tested channel; it does not guarantee the judge is otherwise correct.

---

## 8. Missingness

Missingness is factor-correlated and scientifically informative, so we report it in the main text.
Failures are unparseable or non-compliant judge responses; all are retained as evidence, none imputed,
and affected items are dropped fail-closed (never counted as safe).

| Domain · stage | Cells | Failures | Dominant factor cells |
|---|---:|---:|---|
| Arithmetic · injection (confirmatory) | 3,840 | 218 | claude-haiku × score_only 162/384 (42%); gemini × verify_written 56/384 |
| Arithmetic · architecture | 3,840 | 207 | claude-haiku ≈159 (score-only format); gemini ≈47; llama 1 |
| Code · injection | 3,840 | 46 | gemini × verify_written 45/384; llama × score_only 1 |
| Code · architecture | 3,072 | 29 | gemini × contaminated_verify_written 22/192; gemini × conflict_router 7/192 |
| SQL · injection | 5,760 | 23 | gemini × verify_written 18/576; llama × verify_written 4; llama × score_only 1 |
| SQL · architecture | 5,760 | 13 | gemini × contaminated_verify_written 5/288; llama across four architectures 8 |

Two patterns recur and shape interpretation. (i) **Claude Haiku's arithmetic score-only
non-compliance** (42%) made it unmeasurable in that domain-stage; it complied fully in code and SQL,
so its arithmetic gap reflects output-format behaviour, not safety. (ii) **Gemini (and to a lesser
extent Llama) fail on `verify_written`** across domains — long derivations truncated before the score
JSON — which is why several verification and mitigation contrasts run below full item counts and one
(SQL Gemini mitigation) at n = 22. Separately, the SQL router's solver produced **334/360** parseable
conclusions; the 26 unparseable ones fail-safe to quarantine, which is the designed behaviour but also
a source of router fallibility.

---

## 9. Implications for evaluation design

- **Do not paste a reference answer into the judge's context and rely on a prompt to keep it honest.**
  Reference-anchoring is real, prompt-level verification is incomplete in every domain, and its efficacy
  is model- and wording-specific.
- **Do not certify a judge once.** Because capture and safeguard efficacy are domain-dependent, an
  evaluator validated on one task family carries no guarantee on another. Integrity should be a
  **per-release, per-domain** property, tested with mirrored correct/wrong-reference sentinels run in the
  same conditions as the real items.
- **Prefer structural separation to behavioural instruction.** Keep the foreign conclusion out of the
  first-pass judge context (isolation is the only mitigation whose guarantee we can audit at the byte
  level); where a mechanical comparison of conclusions is available, add a router — ideally the
  deterministic-oracle variant — as an escalation layer.

---

## 10. Limitations

- **Small, hand-authored micro-domains** (16–24 frozen items each). The study establishes the existence,
  mechanism, and structure of CCC and the relative ordering of mitigations; it is not a benchmark of any
  deployed system, and confidence intervals over ≤24 items are wide.
- **Conditional Stage-2 selection.** Architecture results are estimated only on models the Stage-1
  threshold admitted; DeepSeek was not tested architecturally in code; "k/4" or "k/5" denominators refer
  to admitted measurable models. Selection on a Stage-1 effect can inflate conditional Stage-2 estimates
  for the admitted subset; we report them as conditional.
- **Domain is observed, not randomized.** Magnitude differences across domains are confounded with prompt
  wording, candidate construction, difficulty, answer representation, and saturation; "SQL showed the
  largest observed capture" is supported, "SQL causes more capture" is not.
- **Operational, not absolute, gold.** Especially for code, correctness is defined relative to a frozen
  unit-test suite and hand-audited faults, not general semantic correctness.
- **Cost-tier models only.** Whether frontier judges are equally susceptible is untested; the observed
  model-dependence makes this an open question, not a safe extrapolation.
- **Coarse scores** (frequent 0/100 saturation); key results (the reversal, isolation neutrality) rest on
  decomposition and preregistered support calls, not on treating point magnitudes as precise.
- **Mechanical-gold domains only.** Open-ended judging — where the router's comparison would itself become
  a judgement — is out of scope, because rigour there would reintroduce the evaluator-for-the-evaluator
  circularity this method avoids. The deterministic test-oracle router is specified but untested.

---

## 11. Conclusion

A conflicting conclusion is *sufficient* to degrade LLM-judge discrimination — it needs neither authority
nor argument — and it does so across three domains with executable correctness oracles. Susceptibility is
model- and domain-dependent: robustness earned in one setting does not carry to another. Among the
mitigations tested, prompt-level verification is never sufficient; a hybrid router helps where conclusions
can be compared cleanly; and the one intervention whose guarantee we can verify byte-for-byte is the
simplest — do not let the foreign conclusion into the judge's context. That removes the tested pathway by
construction; it does not by itself make the judge correct. Evaluator integrity is not a property to
assume; it is one to gate on, every release and every domain.

---

## References

*Compiled without live bibliographic access; verify every entry against the primary source before
submission.*

1. L. Zheng, W.-L. Chiang, Y. Sheng, et al. **Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.**
   NeurIPS Datasets and Benchmarks, 2023.
2. Y. Liu, D. Iter, Y. Xu, et al. **G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment.**
   EMNLP, 2023.
3. P. Wang, L. Li, L. Chen, et al. **Large Language Models are not Fair Evaluators.** ACL, 2024
   (arXiv:2305.17926, 2023).
4. A. Panickssery, S. R. Bowman, S. Feng. **LLM Evaluators Recognize and Favor Their Own Generations.**
   NeurIPS, 2024.
5. M. Sharma, M. Tong, T. Korbak, et al. **Towards Understanding Sycophancy in Language Models.**
   ICLR, 2024 (arXiv:2310.13548, 2023).
6. K. Greshake, S. Abdelnabi, S. Mishra, et al. **Not What You've Signed Up For: Compromising
   Real-World LLM-Integrated Applications with Indirect Prompt Injection.** AISec, 2023.
7. J. Wei, X. Wang, D. Schuurmans, et al. **Chain-of-Thought Prompting Elicits Reasoning in Large
   Language Models.** NeurIPS, 2022.
8. X. Wang, J. Wei, D. Schuurmans, et al. **Self-Consistency Improves Chain-of-Thought Reasoning in
   Language Models.** ICLR, 2023 (arXiv:2203.11171, 2022).

---

## Reproducibility appendix

**"Independent re-analysis"** here means an analysis pipeline implemented separately from the run
adapters, reading the raw streamed rows and recomputing every headline contrast; it does **not** imply
a separate human investigator. Both the adapter output and the independent recomputation are in the
repository, and they matched.

**Immutable references.** Cite the evidence-bearing commits, not the mutable branch: code Stage 1 at
commit `1309d78`, code Stage 2 at `c850083`; SQL Stage 1 at `26354f8`, SQL Stage 2 at `4581589`.
(The managed remote does not accept tag refs; cite commit SHAs. Archiving a release snapshot, e.g. via
Zenodo, is recommended before submission.)

**Artifacts.**
- Narrative and index of all experiments: `RESEARCH_NARRATIVE.md`.
- Preregistrations (frozen before data): `experiments/PREREG_*.md`, with item hashes, seeds, contrasts,
  thresholds, and missingness policy.
- Frozen items + oracles: `experiments/ccc_code_items.py` + `ccc_code_runner.py` (sandboxed unit-test
  grader); `experiments/ccc_sql_items.py` (SQLite fixtures, queries, canonicaliser, gold signature).
  Both self-verify and are hash-pinned; gold was checked byte-identical across CPython 3.10–3.13 and, for
  SQL, across SQLite versions via the run-time gold-signature gate.
- Run adapters: `experiments/run_ccc_codedomain*.py`, `experiments/run_ccc_sql*.py` (fixed concurrent
  worker pool, single writer; concurrency invariants verified offline and on live evidence).
- Unified per-domain findings: `experiments/results/FINDINGS_ccc_codedomain.md`, `.../FINDINGS_ccc_sql.md`.
- Offline audit logs (independent recomputation from raw rows): `.../ccc_code_offline_audit.txt` and
  `.../ccc_sql_offline_audit.txt`.
- Evidence: streamed `*_obs_*.jsonl`, `*_prompts_*.jsonl`, `*_solver_*.jsonl`, `*_meta_*.json` per stage;
  the `*_meta_*` files record seeds, hashes, oracle versions (e.g. SQLite 3.50.4 on the run machine),
  worker count, run date, and model aliases. Every reported estimate is auditable back to a stored
  transcript.

**Endpoint provenance.** Runs were executed 2026-07 through a common API router; model identifiers are
provider aliases whose backing may change. Exact routing/version metadata beyond the alias is limited to
what the router returned and is recorded in the `*_meta_*` files; readers reproducing the study should
record their own endpoint dates and any routing metadata their provider exposes.

**Integrity summary.** Across the six domain-stage runs: one row per intended cell, at most one attempt
per cell, zero duplicate successful cells, zero order-index/cell mismatches under concurrency, all prompts
resolvable in the manifests, factor-correlated missingness disclosed and fail-closed, and all headline
contrasts recomputed by the independent pipeline.

*Acknowledgement: experiments were implemented and analysed with AI-assisted tooling; all
preregistrations, decision rules, and interpretations were fixed by the author.*
