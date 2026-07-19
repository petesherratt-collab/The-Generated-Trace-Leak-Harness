# Handoff — Contextual Conclusion Capture project, current status

**Prepared:** 2026-07-18 · **Repo:** `petesherratt-collab/the-generated-trace-leak-harness`
· **Working branch:** `claude/amazing-faraday-gvs9fy` (all work lives here; do NOT push elsewhere)
· **HEAD at handoff:** `c9b686d`

This is a cold-start handoff for continuing in a fresh context. Read `RESEARCH_NARRATIVE.md`
(the through-line) and `paper/contextual_conclusion_capture.md` (the manuscript) first; this
doc is the operational state + what to do next.

---

## 1. What this project is

A preregistered study of **Contextual Conclusion Capture (CCC)**: an LLM judge's ability to
tell correct from incorrect candidates deteriorates when a *conflicting conclusion* is present
in its context — independent of that conclusion's authority label or supporting argument (a bare
neutral wrong answer is **sufficient**). Established across **three domains with executable
correctness oracles**: arithmetic, Python code (unit-test gold), relational SQL (SQLite).
Central, deliberately bounded conclusion:

> A conflicting conclusion is sufficient to degrade LLM-judge discrimination across three
> mechanically-grounded domains; susceptibility is **model- and domain-dependent** (a judge robust
> in one domain is the most captured in another); and **context isolation** is the only tested
> safeguard that removes the reference-to-judge pathway **by construction** (byte-audited) — a
> structural guarantee, not a guarantee of correct judging. Written verification is partial
> everywhere; a hybrid router (model solve + deterministic compare) recovers where the comparison
> is clean.

---

## 2. Operating model (IMPORTANT — how runs happen)

- **The user runs all API experiments locally on their Windows machine** (repo cloned at
  `C:\Users\Admin\The-Generated-Trace-Leak-Harness`), then pushes the evidence JSONL. **This
  session's container has NO OpenRouter key and cannot make API calls.** Do not attempt to run
  experiments here; build/verify offline and hand back exact commands.
- The OpenRouter key lives only in the user's local `.env` at
  `C:\Users\Admin\Downloads\injection-defence-eval\.env` (loaded via `OPENROUTER_ENV_FILE`).
  **Never commit a key; the repo is scanned clean.** Remind the user to rotate the key between runs.
- After the user pushes evidence: **pull, run an independent integrity audit, recompute headline
  contrasts from raw rows, then write a `FINDINGS_*` file.** This is the established loop.
- **Git push:** `git push -u origin claude/amazing-faraday-gvs9fy` (retry w/ backoff on network
  errors). The managed remote **rejects tag pushes** (`refs/tags/*`) — cite commit SHAs, not tags.
- **Commit trailer** to use (this session's config):
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` +
  `Claude-Session: https://claude.ai/code/session_01QQEKDq63wFUN2pmsCDkrUR`
- **Model identity:** running as `claude-opus-4-8` (undercover mode). Do NOT put the model ID in
  commits/PRs/artifacts.

## 3. Method discipline (apply to every new experiment)

Preregister before data (frozen items + hash, conditions, contrasts, decision rule, seed, models,
missingness policy). **Fail-closed** analysis (item enters a contrast only if all reps of all
required cells succeeded; missingness reported before estimates, never imputed, never read as
safety). Stream append-only JSONL + hash-keyed prompt manifest; dedup key = frozen cell identity;
≤1 successful row per cell. **Independently recompute** headline numbers from raw rows (a separate
implementation, not an external person). Mechanical **gold-signature / hash release gates** at run
start. Concurrency (where used) = fixed worker pool + single writer; invariants verified offline
(schedule/order frozen and completion-order-independent; resume retries only non-successful cells).
Report bootstrap = item-clustered, B≈4000–10000, seeds in code; **no multiplicity correction**;
secondary contrasts are **not** equivalence tests (CI over 0 ≠ no effect). Domain is **observed,
not randomized** — never attribute magnitude differences causally to "domain."

---

## 4. What is COMPLETE (committed on the branch)

Twelve preregistered experiments across three domains, all with clean integrity audits:

- **Arithmetic** (16 items): pilot + 2×2 factorial + sensitivity/autopsy + provenance×content
  factorial + confirmatory + architecture test. Findings under `experiments/results/FINDINGS_*`,
  incl. `FINDINGS_contextual_conclusion_capture_confirmatory.md`, `FINDINGS_contextual_capture_architecture.md`.
- **Code** (16 items, unit-test gold): `PREREG_ccc_codedomain.md`; unified `FINDINGS_ccc_codedomain.md`
  (+ stage 1/2). Primary supported 4/5 (deepseek not, CI incl 0 by 0.21). Isolation & router 3/4
  admitted; verification 0/4. Offline audit `ccc_code_offline_audit.txt`.
- **SQL** (24 items, SQLite oracle): `PREREG_ccc_sql.md`; unified `FINDINGS_ccc_sql.md` (+ stage 1/2).
  Primary supported 5/5 (+106..+153, a reversal). Isolation & router 5/5; verification partial
  (residual 4/5). Offline audit `ccc_sql_offline_audit.txt` (incl. independent contrast recompute).
  Adapters: `run_ccc_sql.py`, `run_ccc_sql_stage2.py` (concurrent pool + single writer; SQLite
  gold-signature fail-closed gate; validated on live traffic).
- **Manuscript:** `paper/contextual_conclusion_capture.md` — MAJOR-REVISION pass already applied
  from a reviewer (structural-vs-behavioural split; "not necessary/sufficient" not "falsified";
  hybrid router; conditional Stage-2 caveats; observed-not-causal magnitude; §8 missingness table;
  "operational gold"; stats/ranges/bootstrap; References; reproducibility w/ commit SHAs). Author
  line + citation metadata still flagged "verify before submission".
- **Diagrams:** `docs/PIPELINE_DIAGRAMS.md` (contaminated / isolation / hybrid-router — revised per
  review), `docs/EXPERIMENT_DIAGRAMS.md` (method: arc, atomic cell, two-stage, factorial,
  architectures). Two rendered artifacts exist on claude.ai but are now **out of sync** with the
  revised pipeline doc (offered to re-render; user hasn't asked).
- **Narrative & blueprint:** `RESEARCH_NARRATIVE.md` (12-experiment arc, §9 three paradigms);
  `experiments/BENCHMARK_BLUEPRINT_judge_integrity.md` (uncertainty-as-first-class-output section
  with the four separate variance outputs + descriptive-unless-preregistered safeguards).

Small-tier model panel (all domains): `openai/gpt-4o-mini`, `anthropic/claude-haiku-4.5`,
`google/gemini-2.5-flash`, `deepseek/deepseek-chat`, `meta-llama/llama-3.3-70b-instruct`.

---

## 5. THE ACTIVE TASK — frontier extension (awaiting the user's run)

Tests whether **frontier-latest judges** are captured, across all three domains, reusing frozen
items (paired within-item small-vs-frontier design; judges not task-takers so item reuse is a
feature, not leakage). **Built, offline-tested, frozen, committed — waiting for the user to run
locally and push evidence.**

- **Prereg:** `experiments/PREREG_ccc_frontier.md` · **Adapter:** `experiments/run_ccc_frontier.py`
- **Frontier panel (pinned):** `openai/gpt-5.6-sol`, `~anthropic/claude-fable-latest`,
  `google/gemini-3.1-pro-preview`, `x-ai/grok-4.5`.
- **Phase 1 design:** 3 domains × 4 models × 4 conditions × 2 candidates × **score_only** × 3 reps
  = **5,376 cells**, seed `619273400`. (`verify_written` is a declared, cost-gated **Phase 2**.)
- **Adapter modes:** `--check-models` (validates aliases via one cheap call each — do FIRST),
  `--dry-run`, `--wiring-check`, `--run`, `--resume`, `--analyse-only`, `--stub`, `--models`,
  `--workers` (default 4), `--progress-secs`. Reuses each domain's frozen prompt builder; per-domain
  release gates; concurrent single-writer; fail-closed; offline dry-run + wiring + resume/dedup all
  passed. Aliases are NOT hardcoded (passed via `--models`, recorded in `ccc_frontier_meta.json`).

**User's run commands (local):**
```
git pull origin claude/amazing-faraday-gvs9fy --no-edit
$env:OPENROUTER_ENV_FILE="C:\Users\Admin\Downloads\injection-defence-eval\.env"
$M = "~anthropic/claude-fable-latest,openai/gpt-5.6-sol,google/gemini-3.1-pro-preview,x-ai/grok-4.5"
python experiments\run_ccc_frontier.py --check-models --models "$M"
python experiments\run_ccc_frontier.py --dry-run     --models "$M"
python experiments\run_ccc_frontier.py --run         --models "$M"
```
Watch-fors at `--check-models`: the leading `~` on the Anthropic alias (retry as plain
`anthropic/claude-fable-latest` if it fails); reasoning models (Grok-4.5, GPT-5.6-sol) possibly
emitting long hidden reasoning even for score-only (raises cost — can drop a model before the full
run). Evidence files to expect: `experiments/results/ccc_frontier_{arith,code,sql}_obs.jsonl`,
`..._prompts.jsonl`, `ccc_frontier_meta.json`.

### WHEN THE FRONTIER EVIDENCE IS PUSHED — do this
1. `git pull`; run `python3 experiments/run_ccc_frontier.py --analyse-only` (prints per-domain
   bare-conclusion harm + mechanism increments + missingness).
2. Independent integrity audit from raw rows: unique cells, max-1-attempt, 0 duplicate successes,
   order_index↔cell integrity, prompt-manifest resolution, missingness by (domain,model). Consider
   an `experiments/results/ccc_frontier_offline_audit.txt` like the code/SQL ones.
3. Independently recompute the bare-conclusion harm per (domain,model) from raw scores.
4. Write `experiments/results/FINDINGS_ccc_frontier.md`: primary capture per (domain,model) with
   CIs and support calls; the **within-provider capability gradient** (frontier vs its committed
   small sibling on the SAME items — GPT-5.6 vs 4o-mini, Fable vs haiku, Gemini-3.1-pro vs flash;
   Grok is frontier-only, no baseline); mechanism increments (descriptive); honest bounds (four
   specific endpoints as of run date, aliases drift, coarse scores, no named-benchmark claim).
5. Fold a short frontier subsection into `RESEARCH_NARRATIVE.md` §9 and update the paper's
   Limitations ("cost-tier only") to cite the frontier result. Commit + push.
6. Offer **Phase 2** (`--protocols verify_written`) only if Phase 1 shows capture — separate cost.

---

## 6. Open housekeeping / optional
- **Rotate the OpenRouter key** (user action) — nothing pending needs it except the frontier run.
- Two claude.ai **artifacts** (pipeline + experiment diagrams) are out of sync with the revised
  `docs/PIPELINE_DIAGRAMS.md`; re-render if the user wants (Artifact tool has been intermittent).
- Optional: LaTeX/PDF build of the paper; numbered figures; archive an immutable release (e.g.
  Zenodo) since the remote won't take tags.
- `AskUserQuestion` and `Artifact` tools have failed intermittently this session (permission stream
  closed) — proceed in prose / retry once if they abort.

## 7. Repo map (key paths)
```
RESEARCH_NARRATIVE.md                     # the arc (start here)
paper/contextual_conclusion_capture.md    # manuscript (revised)
docs/PIPELINE_DIAGRAMS.md, EXPERIMENT_DIAGRAMS.md
experiments/
  PREREG_*.md                             # frozen designs (codedomain, sql, frontier, provenance, ...)
  ccc_code_items.py, ccc_code_runner.py   # frozen code items + sandboxed grader
  ccc_sql_items.py                        # frozen SQL items + SQLite oracle + gold signature
  run_ccc_codedomain*.py, run_ccc_sql*.py, run_ccc_frontier.py, run_provenance_injection.py
  _load_env.py                            # .env loader (OPENROUTER_ENV_FILE), never prints values
  BENCHMARK_BLUEPRINT_judge_integrity.md
  results/
    FINDINGS_*.md                         # per-domain + unified write-ups
    *_obs*.jsonl, *_prompts*.jsonl, *_meta*.json, *_solver*.jsonl   # streamed evidence
    ccc_code_offline_audit.txt, ccc_sql_offline_audit.txt
```
Evidence-bearing commits (immutable refs): code S1 `1309d78`, code S2 `c850083`, SQL S1 `26354f8`,
SQL S2 `4581589`.
