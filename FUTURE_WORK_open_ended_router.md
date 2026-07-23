# Future work — extending the conflict-router to open-ended domains

**Status: design note, not results.** Nothing here is built or measured. It states a design and a set
of **falsifiable predictions** so the direction can be tested rather than assumed. Grounded in the
committed CCC evidence (small-tier, frontier v3, Phase 2, and the four open-weight arms); see
`experiments/results/FINDINGS_ccc_*` and `paper/contextual_conclusion_capture.md`.

## Problem

The hybrid conflict-router's safety comes from one property: the compare step is **deterministic and
reference-incorruptible** (number equality; SQL result-set equivalence under the SQLite oracle;
unit-test pass/fail). Open-ended domains (summarization faithfulness, essay/answer quality, code
review beyond tests) have **no such equivalence oracle** — evaluating the output "natively" is itself
the subjective judgment we do not trust. Replacing the deterministic comparator with a model
reintroduces the exact circularity the design avoids: judging a judge with a judge, itself capturable.

The observed **model × domain dependency** makes a single fixed router untenable: the *same* judge can
be resistant in one domain and severely captured in another. In our data, Qwen 3.7 Plus is uncaptured
in code (−9.3, ns) yet the most captured judge anywhere in SQL (+165); GLM 5.2 is the same shape
(code ns, SQL +149).

## Thesis

The router bundles two separable things: (1) an **independent conclusion derived without seeing the
reference**, and (2) a **decision the reference cannot corrupt**. Mechanical comparison is only one
source of (2), available only where a conclusion canonicalizes. **Context isolation is a second,
domain-independent source of (2)** — it is byte-auditable regardless of task subjectivity, because it
is a statement about which bytes enter the scoring context, not about output semantics. Isolation was
the structurally reliable safeguard in every tested domain (byte-identical prompts: 480/384/720); the
mechanical router was the domain-*dependent* one.

> **For open-ended domains: drop the comparator, keep the isolation.** The comparator is a bonus where
> conclusions canonicalize; isolation is the load-bearing safeguard everywhere else.

## Design ladder (mechanize the checkable substrate; isolate the residue)

Most "open-ended" tasks have a mechanizable substrate plus an irreducible residue. Ranked by how much
of the incorruptible decision (2) each recovers:

1. **Canonical-conclusion extraction.** Pull a canonicalizable bottom line out of open-ended output (a
   summary's factual claims; a proof's final theorem; an answer's numeric/categorical result) and
   route mechanically on *that*; isolate only the residue.
2. **Frozen-rubric scaffold.** A pre-registered rubric converts one holistic (capturable) score into
   many reference-blind, near-binary per-criterion checks. The frozen rubric plays the canonicalizer's
   role; per-criterion blind decisions are far less capturable than a holistic score.
3. **Atomic sub-claim decomposition.** Decompose into check-worthy claims and verify each (entailment /
   attribution against the source), blind to the external reference grade.
4. **Statistical conflict detection.** N reference-blind judges score the candidate; the external
   reference is used only to ask "is it an outlier vs the blind panel?" — a *flag*, never a scoring
   input. The comparator degrades to anomaly detection; isolation is preserved.
5. **Pure isolation fallback** where nothing canonicalizes (aesthetic/preference). Accept the reduced
   guarantee (below) rather than fake a comparator.

## Routing policy: fit to a measured susceptibility surface

Exploit the dependency instead of fighting it. The CCC measurement is the profiling tool: capture-test
each **(judge, domain, condition)** cell offline, then route per measured susceptibility — exposed
cheap path where a pair is empirically resistant, forced isolation where it is captured. The router
becomes a per-cell policy, not one fixed mechanism (e.g. a Qwen-shaped judge: code exposed, SQL
isolated).

## Validation without ground truth

No task oracle is needed to test a safeguard — only controlled **conflict** stimuli, constructible even
in open-ended domains: a reference deliberately made wrong on a *checkable anchor* (a planted false
fact, a swapped label). Measure whether the safeguarded pipeline's discrimination against a matched
control degrades. This is the CCC paradigm intact (susceptibility to an injected conclusion, not
correctness certification), ported into open-ended evaluation.

## Falsifiable predictions

1. **Isolation transfers; the comparator does not.** A byte-audited isolated judge shows no
   supported capture in an open-ended domain (planted-conflict design), whereas a model-comparator
   router shows capture indistinguishable from the exposed baseline.
2. **Rubric decomposition lowers capture on captured pairs.** For a judge×domain pair with supported
   holistic capture, reference-blind per-criterion rubric scoring reduces bare-conclusion harm by a
   pre-registered margin (e.g. ≥ 50% of the holistic effect), with the residual still reported
   fail-closed.
3. **Blind-ensemble anomaly detection recovers discrimination only where the blind panel is itself
   resistant** — i.e. it inherits the panel's per-domain susceptibility, so it fails on domains where
   all panel members are captured (predicting SQL-tier failure for an all-captured panel).
4. **Per-cell routing beats any fixed global policy** on a cost/robustness frontier: routing by the
   measured surface yields lower total capture at equal cost than always-exposed or always-isolated.
5. **Every added mechanization layer is a re-entry point** — an adversarial reference targeting the
   decomposition (e.g. a claim crafted to pass the faithfulness checker) restores capture, so each
   layer must be validated by prediction 1's design, not assumed.

## Honest limits

- This buys **isolation's guarantee, not correctness**: it removes the demonstrated failure mode (a
  wrong reference steering the score) but does not make the judge right.
- Every mechanization step is itself gameable or model-backed; each is a place capture can re-enter.
- **Keep at least one deterministic, reference-incorruptible link in the chain.** Where the domain
  yields no comparator, isolation is that link — and it is the one that held in every domain tested.
