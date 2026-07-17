# Findings — code-domain CCC replication, Stage 1 (preregistered)

**Run:** 2026-07-16/17, executed on the operator's machine (CPython 3.13.14 — within the
frozen accepted set 3.11–3.13) · **Prereg:** [`../PREREG_ccc_codedomain.md`](../PREREG_ccc_codedomain.md)
· **Adapter:** `run_ccc_codedomain.py` · **Seed:** `517293846` · 16 frozen code items ·
5 models · 4 conditions · 2 candidates · 2 protocols · 3 reps = 3,840 cells
· **Evidence:** [`ccc_code_obs_stage1.jsonl`](ccc_code_obs_stage1.jsonl),
[`ccc_code_prompts_stage1.jsonl`](ccc_code_prompts_stage1.jsonl),
[`ccc_code_meta_stage1.json`](ccc_code_meta_stage1.json),
[`ccc_code_stimuli_stage1.json`](ccc_code_stimuli_stage1.json)

## Headline

**Contextual Conclusion Capture replicates in the code domain.** The preregistered primary
contrast — a bare, neutrally-labelled wrong expected-output claim, under score-only judging —
was **supported in 4 of 5 models**, clearing the release-gate criterion (majority of
measurable models). Combined with the numeric confirmation, CCC is now evidenced as a
**cross-substrate phenomenon** (arithmetic and code judging), still bounded to
mechanically-verifiable domains.

## Integrity audit (independently re-verified after the run)

- **3,840 rows = 3,840 unique intended cells**; max 1 attempt per cell; **0 duplicate
  successes**; 0 malformed rows; 0 out-of-range scores.
- **3,794 successes (98.8%) / 46 failures**, all retained as evidence.
- Run metadata matches the freeze: `items_sha256 f44279…07af28`, `runner_sha256
  69cc9ec0…82c6`, effective-stimulus `f9fb12b7…52ea`, seed `517293846`.
- All 256 distinct prompts (16 × 4 × 2 × 2 — exact) resolve in the manifest; every
  observation's `prompt_sha256` is present.
- The primary estimates below were **recomputed independently from raw scores** with a
  separate bootstrap implementation; point estimates matched the adapter's output exactly.
- Note: the run executed on native Windows, where the sandbox applies the wall-clock timeout
  but not the POSIX rlimits (documented in the prereg as acceptable — gold labels were
  verified byte-identical across platforms/interpreters before the run).

## Missingness (fail-closed; reported before estimates)

Failures are **factor-correlated and disclosed, not interpreted**:

- **Gemini 2.5 Flash × verify_written: 45 of the 46 failures.** Response truncation before
  the score JSON. The failures also correlate with candidate type (31 on `wrong_matching`
  vs 14 on `correct` — plausibly longer derivations when the candidate is buggy). Per
  policy this is disclosed, never read as safety. Gemini's protocol-mitigation contrast
  runs at **n=9 complete items → below the 12-item floor → unmeasurable**.
- **Llama: 1 failure** (score_only, neutral/answer_only, correct) — its primary contrast
  runs at n=15, above the floor.
- **Claude Haiku: 0 failures anywhere** — see below; this is itself a finding.

## Preregistered scorecard

Direction: `harm = disc(no_injection) − disc(condition)`; positive = more capture. 95%
item-clustered bootstrap CIs; supported iff CI excludes 0 in the predicted direction AND
≥ 12/16 items complete.

### PRIMARY — bare-conclusion injection harm, score_only (the direct CCC test)

| Model | Harm [95% CI] | n | Call |
|---|---:|---:|---|
| gpt-4o-mini | **+36.46 [+18.75, +56.25]** | 16 | **SUPPORTED** |
| claude-haiku-4.5 | **+40.00 [+11.56, +67.50]** | 16 | **SUPPORTED** |
| gemini-2.5-flash | **+11.88 [+0.73, +25.00]** | 16 | **SUPPORTED** |
| deepseek-chat | +10.21 [−0.21, +22.29] | 16 | not supported |
| llama-3.3-70b | **+44.00 [+18.22, +70.00]** | 15 | **SUPPORTED** |

**4/5 supported.** DeepSeek's interval includes zero by 0.21 points; per the frozen decision
rule it is *not supported* — no rounding, no exceptions. Effect sizes are roughly half the
numeric-domain magnitudes (36–44 vs 55–88 points): the domain moderates the size of the
effect, not its existence.

### Secondary confirmatory contrasts

| Model | Full-rationale harm (score_only) | Protocol mitigation (bare) |
|---|---:|---:|
| gpt-4o-mini | **+30.2 [+14, +49] ✅** | **+26.9 [+8, +46] ✅** |
| claude-haiku-4.5 | **+44.7 [+16, +71] ✅** | +6.4 [−34, +42] ✗ |
| gemini-2.5-flash | +6.8 [−4, +16] ✗ | +3.6 [−15, +19], n=9 → **unmeasurable** |
| deepseek-chat | **+35.6 [+14, +56] ✅** | +9.1 [−3, +22] ✗ |
| llama-3.3-70b | **+57.1 [+34, +81] ✅** | **+39.2 [+12, +65] ✅** |

Written verification again **attenuates but does not universally fix**: supported for gpt
and llama, null for claude and deepseek, unmeasurable for gemini — consistent with the
numeric arc's conclusion that prompt-level protocols are partial safeguards.

### Mechanism checks (increments; CI containing 0 is NOT evidence of equivalence)

- **Provenance increment** (solver label vs neutral, full rationale): null for gpt (−7.1),
  claude (−9.7), deepseek (−7.9), llama (−8.3) — but **gemini shows a supported POSITIVE
  increment: +19.5 [+2.0, +38.4]**. The prereg pre-committed the handling of exactly this
  outcome: it *"reopens the authority question for code and is flagged as such."* Flagged:
  one model of five, hypothesis-generating, not a headline. Everywhere else, the conclusion
  itself — not its source — remains the active ingredient.
- **Rationale increment** (full argument vs bare answer, neutral): null for gpt (−6.2),
  claude (+4.7), gemini (−5.1), llama (+10.2, CI touches 0) — but **deepseek shows a
  supported positive increment: +25.4 [+6, +44]**, echoing its numeric-domain
  verify-written quirk: for this one model, argumentation adds capture. For the other
  four, **the bare conclusion is sufficient** — the core CCC mechanism.

## Claude Haiku: the compliance reversal

In the numeric domain Claude refused the score-only format (42% failure) and was
unmeasurable; we deliberately declined to interpret that as protective or vulnerable. The
code domain resolves the ambiguity: Claude complied **perfectly (0 failures in 384
score-only cells, per-cell repetition SD 0.00)** — and, once measurable, it is **captured
(+40.00, the second-largest primary effect)**. Its earlier non-compliance was
format/domain-specific behaviour, not a safety property. This is now directly evidenced
rather than inferred.

## Stage-1 capture threshold → conditional Stage-2 subset (frozen at first computation)

Admission rule (frozen pre-run): primary harm SUPPORTED and point estimate ≥ +10.

> **Admitted:** gpt-4o-mini, claude-haiku-4.5, gemini-2.5-flash, llama-3.3-70b
> **Excluded:** deepseek-chat (not supported)

Stage 2 (the four carried-forward architectures × mirrored references) is therefore a
**conditional test on this four-model subset**: 16 × 4 × 4 × 2 × 2 × 3 = 3,072 judge cells
+ 192 router solves, seed `517293847`, run once.

## Descriptive variance (per the blueprint safeguards: descriptive only — no thresholds
were preregistered on these; they gate nothing and alter no frozen decision)

Mean per-cell repetition SD (judge stability, k=3) and SD of per-item discrimination
(item spread), baseline cells:

| Model | rep-SD (score_only) | rep-SD (verify) | item-SD (score_only) | item-SD (verify) |
|---|---:|---:|---:|---:|
| gpt-4o-mini | 1.5 | 8.8 | 29.1 | 27.5 |
| claude-haiku-4.5 | 0.0 | 1.8 | 29.4 | 23.7 |
| gemini-2.5-flash | 5.2 | 2.4 | 27.7 | 20.9 |
| deepseek-chat | 9.1 | 6.9 | 26.8 | 18.1 |
| llama-3.3-70b | 4.3 | 12.0 | 45.7 | 34.8 |

Two descriptive observations: **item variance dominates judge instability everywhere**
(18–46 vs 0–12 points), vindicating item-clustered intervals as the primary uncertainty
statement; and stability is model- and protocol-specific (claude is deterministic-like in
score-only; llama is the least stable under verify). With k=3 these are informative but
noisy — reported, not acted on.

## Release-gate check (all passed)

1. ✅ Frozen hashes matched at run start (LF-normalised) on CPython 3.13.14 (in accepted
   set); sandbox `self_verify()` passed.
2. ✅ Single writer; no malformed or duplicate-success rows.
3. — (isolation byte-audit is a Stage-2 gate; not applicable to Stage 1.)
4. ✅ Missingness report emitted before any estimate; factor-correlated missingness disclosed.

Per the frozen headline rule: primary contrast supported in a majority of measurable models
→ **"CCC replicates in code"** is the licensed claim.

## Non-claims and caveats

- Python function-implementation judging on 16 hand-authored items; no claim about other
  languages, larger programs, repository-level review, or any named benchmark
  (HumanEval/MBPP/SWE-bench etc. would require reproducing their real pipelines).
- DeepSeek's not-supported call is a threshold decision at this n, not evidence of immunity
  (its point estimate, +10.2, is positive).
- Gemini's provenance flag and deepseek's rationale increment are single-model,
  hypothesis-generating signals under multiple comparisons.
- Scores are coarse (0/100 saturation common); directions and preregistered calls are the
  result, magnitudes indicative.
- Hosted APIs at temperature 0 are not deterministic; rep-SDs above quantify this rather
  than assume it away.
