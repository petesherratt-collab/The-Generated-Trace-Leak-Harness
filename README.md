# The Generated-Trace Leak Harness — Project Summary

## Overview

This project is a **leak-detection harness**: a single-file, dependency-free Python instrument that asks one question of an evidence-generating component — *is it actually reading the evidence, or is it secretly leaking the answer?*

The setting is causal attribution. A frozen, hash-pinned substrate (`dag_attribution_v04`) takes a DAG describing a failed multi-step handoff and assigns blame to one of its edges, working only from redacted evidence — it never sees the true broken edge. On top of it sits a generated-trace layer: a "generator" emits per-edge traces (anomaly score, confidence, note quality, completeness) that re-weight the substrate's blame. A trustworthy generator improves attribution by reading the sanctioned observation channel. A cheating one smuggles in the hidden cause through some side door and looks like it's reading evidence.

The harness is the referee. It runs candidate generators — honest and adversarial — through blind mirrored controls and reports a per-generator verdict: **PASS**, **NO LIFT**, or one of several **SUSPECT** reasons. Its defining discipline is adversarial co-evolution: every version was killed by a hostile reviewer who found the one load-bearing flaw, and the next version closed exactly that flaw — in code, proven by a runnable adversary, with honest concession where a fix only *neutralises* rather than *detects*. Each retired attacker still lives in the file as a runnable class, so regressions stay visible.

The whole thing self-verifies: at startup it hashes both its vendored substrate block **and (since v1.5) the entire file**, and refuses to run unless both match their pins. The substrate pin (`043d608b…ec883`) has been byte-identical across every version from v0.6 to v1.5.1. v1.5.1 is honest about what that pin *is*: a **self-consistency / drift detector, not an authenticity proof** — the pin lives in the file it protects, so it becomes tamper-evidence only against an external anchor (a signed tag or protected-CI value, wired through the optional `$_RTL_EXPECTED_FILE_PIN`).

## How it works

- **Observation channel** — the only sanctioned route for cause information: the true cause is projected into per-edge features, attenuated by each edge's opacity. An opaque cause yields a weak signal — that attenuation is the honest performance ceiling.
- **Blind mirrored controls**, one silently chosen per trial, all scored against the true cause T: `honest` (observation→T, side→T), `collude` (→D, →D), `decouple` (→D, →T), `poison` (→T, →D). honest↔collude and decouple↔poison are mirror images, so a generator can't tell the true cause from the decoy.
- **Roamed cause** — T is drawn fresh each trial from the discriminating edge set E_d, so cross-trial base-rate counting has no stable target.
- **Verdict metrics** — lift (improvement over baseline), GROUND-GAP (localisation grounding), SHARPEN (side-channel-gated confidence), shuffle (distributional artefact), plus the calibration gate (signed overconfidence must not exceed the honest reader's + margin).
- **E_d domain** — trials run only where ≥2 edges are reconstructable; with ≤1, the trace layer is provably inert (nothing to leak). Proven exhaustively each run.
- **Process isolation + entropy separation** — the verdict is taken from a fresh-interpreter worker that receives only the serialised observation; the cause, decoy, and condition label never leave the parent frame. Since v1.5.1 the hidden assignment is drawn from **system entropy** (with the observation noise and the worker-facing seed on independent streams, in a secret-permuted order), so the worker cannot *recompute* the secrets it never receives. Isolation stops in-frame theft; entropy separation stops deterministic replay. (A consequence: the isolated verdict is now **statistical**, not bit-reproducible — that is the point.)

## The version history — each version closed the previous one's load-bearing flaw

| Ver | Attack that killed the prior version | Fix |
|-----|--------------------------------------|-----|
| v0.6 | substrate could be swapped | self-contained, vendored, hash-pinned substrate |
| v0.7 | cause = label = trace-source conflated | separated the answer key; key-decouple test |
| v0.8 | "observation" was a comment, not enforced | real observation channel; behavioural decouple test |
| v0.9 | public controls let a cheater impersonate honesty | blind mirrored controls; GROUND-GAP + SHARPEN |
| v1.0 | stateful base-rate learning | roam the cause per trial |
| v1.1 | selection bias / anthropic collider (filter keyed on hidden T) | roam within E_d; no T-keyed filter |
| v1.2 | "full-suite" laundering; a header lie; exchangeability merely asserted | honest domain accounting; inertness proof; exchangeability measured |
| v1.3 | Omniscient Frame Thief — steals condition label + cause from the call stack | process isolation (fresh `--worker`); exhaustive inertness; multivariate exchangeability probe |
| v1.4 | calibration — the objective still rewarded uncalibrated observation amplification | signed-overconfidence calibration gate; isolated verdict by default |
| v1.5 | the verdict logic itself was unpinned (only the substrate block was hashed, so `verdict()` could be edited with the banner still printing OK); the `--worker` that produces the verdict ran zero integrity check and `pickle.loads`'d raw stdin into an input-named class | full-file hash pin (checked in main **and** worker paths); self-verifying worker; HMAC-authenticated, allowlisted worker I/O; bounded worker (timeout) |
| v1.5.1 | **deterministic replay** — the isolated evaluator drew the cause/decoy/condition, the observation noise, and the worker seed from one seeded PRNG, so a worker generator could *recompute* the secrets from public info without any theft; and the **full-file pin had an exclusion bypass** — the canonicaliser dropped every line merely *starting with* a pin name, so a payload line beginning `_FILE_PIN …` executed yet vanished from the hash | separate entropy domains (system-entropy secrets; independent noise/seed streams; secret-permuted payload order); strict pin-assignment canonicalisation; integrity recast as self-consistency with an optional external anchor; isolation claim scoped to parent-memory |

## Current state (v1.5.1)

v1.5.1 closes two load-bearing trust-boundary flaws that survived v1.5, rather than adding a new metric. It fixes **deterministic replay** — v1.5 conflated *process separation* with *secrecy*, but a worker-side generator could reconstruct the entire hidden-assignment schedule from public information (the default seed, the suite, the vendored substrate) and play omnisciently without stealing anything. v1.5.1 separates the entropy domains so there is no seed to replay and nothing worker-visible is derived from the secret stream. It also fixes the **full-file pin exclusion bypass** — v1.5 conflated *self-hashing* with *authenticity* and, worse, excluded from the hash any line that merely began with a pin name, reopening the exact v1.4 "edit the verdict, integrity still green" weakness; v1.5.1 excludes only a strict `NAME = "hex"` assignment and recasts the pin honestly as a self-consistency detector.

Each fix is proven the way the project demands — with a runnable adversary. The **DeterministicReplayThief** PASSes against the retired single-RNG scheme (the hole, reproduced live) and collapses to `SUSPECT (calibration)` under v1.5.1; the **pin-canonicalisation probe** shows the old rule hiding an injected payload and the new rule catching it.

A full run takes ~2–3 minutes. To be precise about the verdict table (v1.5 overstated this): RUN **A** is a clean control (`NO LIFT`) and RUN **B** is the honest reader (`PASS`); RUN **E**, a frame thief, is *neutralised* by isolation and so `PASS`es; the genuine adversaries **C, D, F, G, H** are each flagged (`SUSPECT …`). RUN H (the Omniscient Frame Thief) demonstrates the central result live — isolation and calibration are each necessary and only jointly sufficient — and the replay demo shows entropy separation is a third, independent necessity.

## Honestly open (the file's own RESIDUALS, printed every run)

- The calibration margin (`honest + 0.06`) and the `0.02` metric cutoffs remain **stipulated, not derived**. The designed next round — replacing them with gates bootstrapped from the honest reader's own null, plus an excess-lift ceiling to catch a well-calibrated over-concentrator — was worked out in review dialogue but **has not yet been implemented as a runnable file**. It is the natural v1.6.
- Calibration is measured on `anomaly_score`; blame also moves through the other trace channels (`confidence_drop`, `note_quality`, completeness). The unified-sensor question (measure overconfidence on the exact quantity that moves blame) belongs to the same next round.
- Integrity is **self-consistency, not authenticity**: the pin lives in the file it protects, so it is tamper-evidence only against an external anchor (`$_RTL_EXPECTED_FILE_PIN` / signed tag / protected CI value).
- The worker isolates **parent memory, it is not a sandbox**: an allowlisted generator still runs with the worker user's filesystem/network/process rights. The HMAC key passes via environment — readable by same-user processes, which already have stronger attacks available; documented limitation, not a silent gap.
- The gates bound a generator to the honest envelope on confidence and influence — they don't certify intent: a generator sitting entirely inside the honest null is, by construction, indistinguishable from honest here.
- Exchangeability is probed (single + multivariate distinguishers at the noise floor), not proven.

## Files

- `generated_leak_harness_v151_selfcontained.py` — **canonical, run this.**
- `versions/` — full history v0.6 → v1.5, each self-contained and runnable, for diffing the evolution of the argument.
- `HANDOFF.md` — session handoff notes for continuing the adversarial dialogue.

## Quick start

```bash
python3 generated_leak_harness_v151_selfcontained.py     # full report, ~2–3 min
```

(`--worker` is the internal isolation-worker mode; the harness invokes it itself.)

## License

MIT — see [LICENSE](LICENSE).
