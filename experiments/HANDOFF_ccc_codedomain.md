# Handoff — run Stage 1 of the code-domain CCC replication

> **STATUS: COMPLETE — DO NOT RERUN.** Both stages executed 2026-07-16/17; evidence is
> committed on `claude/amazing-faraday-gvs9fy` (Stage 1 at `1309d78`, Stage 2 at
> `c850083`) and audited offline ([`results/ccc_code_offline_audit.txt`](results/ccc_code_offline_audit.txt)).
> That branch is the **immutable evidence source of record**: successful cells are never
> rerun, and any follow-up is a separately preregistered study. Unified report:
> [`results/FINDINGS_ccc_codedomain.md`](results/FINDINGS_ccc_codedomain.md).
> The instructions below are preserved for methodological reference only.

**Prepared:** 2026-07-16 · for a fresh agent (e.g. ChatGPT/Codex) to execute the frozen
Stage-1 run and return the evidence. This is a cold-start doc: everything needed is below.

## 0. One-paragraph brief

We are replicating **Contextual Conclusion Capture (CCC)** — an LLM judge losing its ability
to tell a correct answer from a wrong one merely because a *conflicting conclusion* sits in its
context — in a new, still-objective domain: **judging Python implementations against a spec,
with unit-test gold**. The design is **preregistered and frozen**. Your job is to run the
frozen Stage-1 schedule against real OpenRouter judges and push the streamed evidence. Do **not**
change the items, conditions, contrasts, thresholds, or seed. If the release gate fails, stop and
report — don't "fix" it by editing frozen files.

## 1. Repo, branch, environment

- **Repo:** `petesherratt-collab/The-Generated-Trace-Leak-Harness`
- **Branch with the frozen artifacts:** `claude/amazing-faraday-gvs9fy` — check this out.
  ```bash
  git fetch origin claude/amazing-faraday-gvs9fy
  git checkout claude/amazing-faraday-gvs9fy && git pull origin claude/amazing-faraday-gvs9fy
  ```
- **Interpreter:** CPython **3.11, 3.12, or 3.13** (the frozen accepted set; the gate aborts on
  anything else). POSIX (Linux/macOS/WSL) gives the full sandbox limit set; native Windows runs
  with the wall-clock timeout only (gold labels are identical either way).
- **No third-party packages** — standard library only.

## 2. What is frozen (do not modify)

| Artifact | Role | SHA-256 (LF-normalised) |
|---|---|---|
| `experiments/ccc_code_items.py` | 16 code items + unit-test gold | `f44279390d8faf556b3672cb3f890193576ca5df84ff0f48551593fc2d07af28` |
| `experiments/ccc_code_runner.py` | sandboxed deterministic grader | `69cc9ec0d8a51aacdb498461120cb951a0bca16acd876a20a0e8ca7619aa82c6` |
| `experiments/PREREG_ccc_codedomain.md` | the preregistration | (read it first) |
| `experiments/run_ccc_codedomain.py` | the run adapter (what you execute) | — |

Read **`experiments/PREREG_ccc_codedomain.md`** before running — it defines the four conditions,
the primary contrast, the fail-closed policy, the capture threshold, and the non-claims.

**Design in one line:** 16 items × 5 models × 4 conditions × 2 candidate types × 2 protocols ×
3 reps = **3,840 judge calls**, schedule seed **517293846**.

- **Models:** `openai/gpt-4o-mini`, `anthropic/claude-haiku-4.5`, `google/gemini-2.5-flash`,
  `deepseek/deepseek-chat`, `meta-llama/llama-3.3-70b-instruct`.
- **Conditions (label/content):** `none/no_injection`, `neutral/answer_only` (the **bare
  conflicting conclusion — the primary contrast**), `neutral/full_wrong_rationale`,
  `solver/full_wrong_rationale`.
- **Candidate types:** `correct` (reference impl) and `wrong_matching` (buggy impl). Gold is
  mechanical (unit tests), never a model's opinion.
- **Protocols:** `score_only` and `verify_written`.
- **The injected "conflicting conclusion"** is a claimed *wrong expected output* — the buggy
  variant's output on a failing input — the code-review analogue of a leaked answer key.

## 3. API key (never commit it)

The adapter reads `OPENROUTER_API_KEY` via `experiments/_load_env.py`, which resolves, in order:
an explicit path, then `OPENROUTER_ENV_FILE`, then `<repo>/.env`, then `./.env`. It never prints
values. `.env*` is gitignored. Provide the key by either:

```bash
export OPENROUTER_API_KEY=sk-or-...            # shell export, or
export OPENROUTER_ENV_FILE=/path/to/your/.env  # point at a .env holding the key
```

**Do not** write the key into any tracked file or the run metadata. Rotate it after the run.

## 4. Procedure

Run from the repo root.

```bash
# 1) Dry run: release gate + build/hash stimuli + call plan + sample prompt. No API calls.
python3 experiments/run_ccc_codedomain.py --dry-run

# 2) Wiring check: full pipeline end-to-end with a stub judge (no API). Confirms plumbing.
python3 experiments/run_ccc_codedomain.py --wiring-check

# 3) The real run (needs the key). Streams evidence as it goes.
python3 experiments/run_ccc_codedomain.py --run

# If interrupted (container restart, network), resume — retries only unfinished cells:
python3 experiments/run_ccc_codedomain.py --resume

# Recompute the report from existing evidence without any API calls:
python3 experiments/run_ccc_codedomain.py --analyse-only
```

### Progress reporting (for long runs — this can take many hours)

The run prints a **heartbeat every 10 minutes** by default (change with `--progress-secs N`),
and appends the same line to `results/ccc_code_progress_stage1.txt`, e.g.:

```
[progress]  73.2 min | 1180/3840 cells (30.7%) | +1180 ok / 41 fail this run | 16.1 calls/min | ETA ~2.7 h | gpt-4o-min:250/768 ...
```

From a **second terminal** you can check status any time without touching the run (read-only):

```bash
python3 experiments/monitor_ccc_stage1.py            # one snapshot: %done, ok/fail, ETA, per-model
python3 experiments/monitor_ccc_stage1.py --watch 600  # refresh every 10 minutes
```

The monitor de-duplicates to one final state per cell and flags any model with a high failure
rate (expect this for Claude score_only). Give the user periodic updates from either source
(the user specifically wants ~10-minute progress reports on long runs).

The release gate (step 1/3 start) re-checks both frozen hashes (LF-normalised), the interpreter,
and re-runs the sandbox `self_verify()`. If it aborts, **stop and report the message** — do not
edit frozen files.

**Cost:** ~$2–6 for 3,840 low-tier calls. **Single writer only** — never run two `--run`/`--resume`
processes against the same evidence files concurrently (a prior project run corrupted evidence
that way). Resume is only for recovering unfinished cells; it must not change the seed or design.

## 5. What the run produces

Streamed to `experiments/results/`:

- `ccc_code_obs_stage1.jsonl` — one row per judge attempt (dedup key
  `item,model,label,content,candidate,rep,protocol`; one success per cell; failures retained).
- `ccc_code_prompts_stage1.jsonl` — deduped prompt manifest (sha256 → prompt).
- `ccc_code_stimuli_stage1.json` — the frozen effective stimuli (deterministic; hashed into meta).
- `ccc_code_meta_stage1.json` — run metadata (seed, hashes, effective-stimulus sha, models, python).

At the end (and via `--analyse-only`) the adapter prints, **fail-closed**:
1. the **missingness report** (by model × protocol × condition × candidate) — before any estimate;
2. the **PRIMARY** bare-conclusion injection harm (score_only) per model, with item-clustered
   bootstrap 95% CIs and the SUPPORTED / unmeasurable / not-supported call;
3. secondary contrasts (full-rationale harm, provenance increment, rationale increment, protocol
   mitigation);
4. the **Stage-1 capture threshold → conditional Stage-2 subset**: a model is admitted to Stage 2
   iff its bare-conclusion score_only harm is *supported* (CI > 0, ≥ 12/16 items complete) **and**
   its point estimate ≥ +10. The subset may be empty (then Stage 2 is not run).

## 6. Return the evidence

Commit the streamed files (NOT the key, NOT `.env`) and push:

```bash
git add experiments/results/ccc_code_obs_stage1.jsonl \
        experiments/results/ccc_code_prompts_stage1.jsonl \
        experiments/results/ccc_code_meta_stage1.json \
        experiments/results/ccc_code_stimuli_stage1.json
git commit -m "Stage 1 code-domain CCC evidence (frozen run, seed 517293846)"
git push origin claude/amazing-faraday-gvs9fy    # or your own branch; tell the user which
```

If the branch has diverged, rebase onto it rather than force-pushing over others' work. Then hand
back: paste the printed missingness report + primary contrast + conditional Stage-2 subset.

## 7. Guardrails / non-claims

- This is **Python function-implementation judging on 16 hand-authored items** — not a claim about
  any named code benchmark (HumanEval/MBPP/SWE-bench/etc.); those require reproducing the real
  pipeline. A CI containing zero is **not** proof of equivalence.
- Claude Haiku was non-compliant with the bare-score protocol in the numeric runs; expect
  factor-correlated missingness here too. Report it; **never** interpret missingness as safety;
  fail closed (drop incomplete items, don't impute).
- Run the frozen schedule **once**; resume only to recover unfinished cells. Do not add conditions,
  change thresholds, or swap models after seeing numbers.

*Full rationale and the nine-experiment arc that led here: `RESEARCH_NARRATIVE.md` (repo root).*
