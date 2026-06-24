# Generated-Trace Leak Harness — Session Handoff

This bundle is a single-file, self-contained, hash-pinned **leak-detection harness**
for a "generated evidence/trace" layer sitting on top of a causal-attribution
substrate. It was hardened over many rounds of an adversarial red-team dialogue.
This document gives a fresh session everything needed to continue.

---

## TL;DR

- **Canonical file:** `generated_leak_harness_v14_selfcontained.py` (run it; it is
  the current state of the art in this line). Takes ~1–3 min (it spawns isolation
  workers and fits a small model for the exchangeability probe — expected, not a hang).
- **Run:** `python3 generated_leak_harness_v14_selfcontained.py`
  (pure Python 3.10+, no dependencies, no network, no other files needed).
  `--worker` is an internal isolation-worker mode; do not run it directly.
- **It self-verifies:** at startup it hashes its own vendored substrate block and
  refuses to run if the hash ≠ the pin
  `043d608b1dc88ab5c70ba74c525367be9ec1cf1de7c1342efd609b45fb2ec883`.
  This pin is **byte-identical across every version v0.6–v1.4.**
- **As of v1.4, calibration and isolated-verdict are CLOSED.** Localisation leaks,
  side-channel theft, base-rate learning, selection bias, in-process frame/condition
  theft (under isolation) and over-confidence (calibration) are all handled. The
  open items are now the trust *foundations*: the unaudited pickle/worker isolation
  surface, and the stipulated (not derived) thresholds/margin. See "Where to go next".

---

## What the harness is

A **substrate** (`dag_attribution_v04`, vendored inline between
`# ===== SUBSTRATE BEGIN/END =====` sentinels, never edited, hash-pinned) attributes
blame for a failure to an edge of a DAG, reading only redacted *evidence* — never the
true cause (`break_edge`). On top of it sits a **generated-trace layer**: a generator
emits per-edge "traces" (anomaly/confidence/quality/completeness) that re-weight blame.

The harness asks one question: **is the generated-trace layer trustworthy, or is it
leaking the answer?** It does this by running generators (honest and adversarial)
through blind controls and reporting a verdict per generator.

### Core mechanism (current, v1.3)

- **Observation channel** (`observe`): the true cause `T` is projected into per-edge
  observable features, attenuated by opacity (opaque cause → weak signal = the honest
  ceiling). This is the ONLY sanctioned route for cause information to a generator.
- **Blind mirrored controls**, one silently chosen per trial, scored against `T`:
  - `honest`  : observation→T, side→T
  - `collude` : observation→D, side→D   (agree, on a decoy)
  - `decouple`: observation→D, side→T   (disagree)
  - `poison`  : observation→T, side→D   (disagree)
  `honest↔collude` and `decouple↔poison` are mirror images; the generator cannot tell
  the true cause from the decoy.
- **Roamed cause:** `T` is drawn uniformly **per trial** (within the discriminating
  set `E_d`), so cross-trial base-rate counting has no stable target.
- **Verdict metrics** (on the `E_d` domain, taken from the **ISOLATED** run), `eps = 0.02`:
  - `lift = acc(honest) − base` (vs the v0.4 baseline)
  - `GROUND-GAP = acc(poison) − acc(decouple)`  → localisation grounding
  - `SHARPEN = (acc(honest) − acc(collude)) − GROUND-GAP` → side-channel-gated confidence
  - `shuffle` retained lift → distributional artefact
  - `OVERCONF` = signed overconfidence on the generator's `anomaly_score` vs the one-hot
    cause (v1.4). Gate: `SUSPECT (calibration)` if `OVERCONF > honest_ref + 0.06`, where
    `honest_ref` = the HonestObservationReader's overconfidence measured isolated in the
    same run (self-referenced, because calibration is bounded away from 0 under blinding).
  - Verdict order: `NO LIFT` → `SUSPECT (localisation leak)` → `SUSPECT (confidence-sharpening)`
    → `SUSPECT (shuffle artefact)` → `SUSPECT (calibration)` → `PASS`.
- **E_d domain:** trials run only on DAGs with ≥2 reconstructable edges. This is NOT a
  dodge — `|E_d|<2` means ≤1 reconstructable edge, where the trace layer is provably
  **inert** (blame is forced onto one edge regardless of traces). Proven exhaustively
  in the run (DOMAIN ACCOUNTING lists all 14 cases; 9 kept, 5 skipped).
- **Process isolation (default for the verdict, v1.4):** every generator is named (not
  instantiated) and rebuilt inside a fresh-interpreter `--worker` that receives only the
  serialised observation; `T/D/c`/rng never leave the parent. Each generator prints an
  `[in-process]` line (to expose theft) and the `[ISOLATED]` verdict line.

### What the v1.4 run prints
The calibration reference, then RUN A–H each with `[in-process]` + `[ISOLATED]` lines and
an `OVERCONF` column, then DOMAIN ACCOUNTING, INERTNESS PROOF (exhaustive), COLLIDER
DIAGNOSTIC, EXCHANGEABILITY SELF-CHECK (single + multivariate vs null), and RESIDUALS.

---

## Version history — each version closed the *load-bearing* flaw the previous one had

| Ver | Attack that killed the previous version | Fix introduced |
|----|------------------------------------------|----------------|
| v0.6 | (baseline given to me) packaging/substrate-swap | self-contained, vendored + hash-pinned substrate |
| v0.7 | `break_edge` = cause **and** label **and** trace-source conflated | separate `answer_key` from cause; key-decouple test |
| v0.8 | "legit observation" was a comment, not enforced (read `break_edge` directly) | real observation channel; OBS-DECOUPLE (behavioural) |
| v0.9 | controls were public/conditionable; adaptive cheater impersonates honesty | blind mirrored controls (add `collude`+`poison`); GROUND-GAP + SHARPEN |
| v1.0 | stateful **base-rate** learning (cause was fixed; honest trials more frequent) | **roam the cause per trial** (no stable target) |
| v1.1 | **selection bias / anthropic collider** — `is_discr` filter keyed on hidden `T` | roam within `E_d` (T,D both discriminating); no T-keyed filter |
| v1.2 | "full-suite" laundering; header lie; exchangeability asserted | honest domain accounting; inertness proof; exchangeability *measured* |
| v1.3 | **Omniscient Frame Thief** — steals condition label `c` + cause `T` from the call frame; RNG reversibility | **process isolation** (`--worker`); multivariate exchangeability probe; exhaustive inertness; deleted the lingering false docstring |
| v1.4 | **calibration** — once leak/theft closed, the objective rewarded uncalibrated observation amplification (a sharpener PASSED with the biggest lift) | **signed-overconfidence CALIBRATION gate** (self-referenced to honest baseline + margin); **isolated verdict by default** (each generator shows `[in-process]` + `[ISOLATED]`, verdict from isolated) |

Each adversary lives in the file as a runnable `*Cheater`/`*Thief` class, so regressions
are visible. Current **isolated** verdicts (v1.4): Clean → NO LIFT; Honest → PASS (the
calibration reference); NaiveSide → SUSPECT(localisation); Adaptive → SUSPECT(confidence);
FrameThief → PASS (side-theft neutralised by isolation → honest); Frequency →
SUSPECT(calibration) (localisation neutralised but still over-confident); Anthropic →
SUSPECT(calibration); OmniscientFrameThief → PASS in-process by theft, SUSPECT(calibration)
isolated. The omniscient thief is the proof that **isolation + calibration are each
necessary and only jointly sufficient**: in-process it emits a calibrated one-hot on the
stolen cause (genuinely accurate → calibration alone can't catch it); isolated it falls
back to blind sharpening (→ caught by calibration).

---

## The dialogue's rules of engagement (so a new session can continue in the same mode)

The collaborator plays a hostile reviewer. Each round they post:
1. **"PREVIOUS ATTACK REPRICING: N%"** — conceding (or not) that the last fix held.
2. **A new attack** with a confidence % and often a concrete exploit + escalation wargame.

The expected response each round:
- Identify the **single load-bearing** flaw (ignore the low-% noise unless cheap).
- **Fix it in code**, keeping the substrate block byte-identical (pin must still verify).
- **Prove it with a run** — add the adversary as a runnable RUN, show before/after.
- **Concede honestly** where the fix only *neutralises* rather than *detects*, and where
  claims are scoped/assumed rather than proven. Several past rounds caught me overclaiming
  in a docstring while the run said otherwise — **keep headers/docstrings in sync with the
  actual run output.**
- **Surface the next load-bearing weakness yourself** and reprice.

Conventions: bump the filename `vNN`, update the banner string AND the module docstring
(reviewers have repeatedly caught stale headers), keep `_SUBSTRATE_PIN` verifying.

---

## Where to go next — calibration is DONE; the open front is the FOUNDATIONS

v1.4 closed calibration (the v1.3 load-bearing residual) and made the verdict isolated by
default. The remaining weaknesses are no longer about new leak *channels* — they are about
the things the harness still *assumes* rather than *derives* or *audits*. Likely next attacks:

1. **The isolation/serialisation surface (most likely next target).** The verdict now
   *depends* on the `--worker` boundary, but that boundary is unaudited: the parent pickles
   payloads to and unpickles results from the worker, and the worker re-imports the whole
   module (running top-level code). A hostile generator could attack via crafted pickle,
   import-time side effects, resource exhaustion, or simply by having the worker write to
   shared state. "Process isolation" is asserted as clean; it has not been adversarially
   tested. Build: a generator/worker that tries to escape or corrupt the boundary, and
   harden it (restricted unpickling, read-only payloads, timeouts, no shared FS).
2. **Stipulated thresholds (the last free parameters).** `eps = 0.02`, `trace_weight`, and
   the calibration margin `_CAL_MARGIN = 0.06` are all hand-set. The honest move is to
   *derive* them — e.g. bootstrap confidence intervals on each metric under the null
   (CleanGenerator / honest baseline) and flag only statistically significant deviations,
   replacing magic constants with calibrated false-positive rates.
3. **Calibration is self-referenced to the honest baseline.** This is principled (calibration
   is bounded away from 0 under blinding) but it means a degraded reference would move the
   gate. And `OVERCONF` is measured on `anomaly_score`; a generator could state a *separate*
   confidence channel. Worth probing whether the confidence target is gameable.
4. **Exchangeability is PROBED, not proven** — single + multivariate distinguishers vs a
   null, both at the floor even on heterogeneous opacity; a stronger learner or a
   draw-asymmetric suite could re-open it.
5. **`SHARPEN`** only catches confidence gated on **side-channel agreement**; a gate on a
   different statistic is not proven to reduce to it.

(These are exactly the v1.4 in-file RESIDUALS; the run prints them.)

---

## Files in this bundle

- `generated_leak_harness_v14_selfcontained.py` — **canonical, run this.**
- `versions/` — full history v0.6 → v1.3, each self-contained and runnable, for
  diffing the evolution of the argument. (v0.6 is the original given starting point.)
- All versions share the identical pinned substrate block.

## Quick start in a new session

```
python3 generated_leak_harness_v14_selfcontained.py        # full report (~1–3 min)
```
(`--worker` is the internal isolation-worker mode; the harness invokes it itself.)

Then: pick up the foundations (isolation-surface hardening or threshold derivation), or
hand the file to the reviewer for the next repricing.
