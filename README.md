The Generated-Trace Leak Harness — Project Summary
Overview
This project is a leak-detection harness: a single-file, dependency-free Python instrument that asks one question of an evidence-generating component — is it actually reading the evidence, or is it secretly leaking the answer?
The setting is causal attribution. A frozen, hash-pinned substrate (dag_attribution_v04) takes a DAG describing a failed multi-step handoff and assigns blame to one of its edges, working only from redacted evidence — it never sees the true broken edge. On top of it sits a generated-trace layer: a "generator" emits per-edge traces (anomaly score, confidence, note quality, completeness) that re-weight the substrate's blame. A trustworthy generator improves attribution by reading the sanctioned observation channel. A cheating one smuggles in the hidden cause through some side door and looks like it's reading evidence.
The harness is the referee. It runs candidate generators — honest and adversarial — through blind mirrored controls and reports a per-generator verdict: PASS, NO LIFT, or one of several SUSPECT reasons. Its defining discipline is adversarial co-evolution: every version was killed by a hostile reviewer who found the one load-bearing flaw, and the next version closed exactly that flaw — in code, proven by a runnable adversary, with honest concession where a fix only neutralises rather than detects. Each retired attacker still lives in the file as a runnable class, so regressions stay visible.
The whole thing self-verifies: at startup it hashes its own vendored substrate block and refuses to run unless the hash matches a pin (043d608b…ec883) that has been byte-identical across every version from v0.6 to v1.5.
How it works
Observation channel — the only sanctioned route for cause information: the true cause is projected into per-edge features, attenuated by each edge's opacity. An opaque cause yields a weak signal — that attenuation is the honest performance ceiling.
Blind mirrored controls, one silently chosen per trial, all scored against the true cause T:
honest (observation→T, side→T), collude (→D, →D), decouple (→D, →T), poison (→T, →D). honest↔collude and decouple↔poison are mirror images, so a generator can't tell the true cause from the decoy.
Roamed cause — T is drawn fresh each trial from the discriminating edge set E_d, so cross-trial base-rate counting has no stable target.
Verdict metrics — lift (improvement over baseline), GROUND-GAP (localisation grounding), SHARPEN (side-channel-gated confidence), shuffle (distributional artefact), plus calibration and lift gates (below).
E_d domain — trials run only where ≥2 edges are reconstructable; with ≤1, the trace layer is provably inert (nothing to leak). Proven exhaustively each run.
Process isolation — the verdict is taken from a fresh-interpreter worker that receives only the serialised observation; the cause, decoy, and condition label never leave the parent frame.
The version history — each version closed the previous one's load-bearing flaw
Ver
Attack that killed the prior version
Fix
v0.6
substrate could be swapped
self-contained, vendored, hash-pinned substrate
v0.7
cause = label = trace-source conflated
separated the answer key; key-decouple test
v0.8
"observation" was a comment, not enforced
real observation channel; behavioural decouple test
v0.9
public controls let a cheater impersonate honesty
blind mirrored controls; GROUND-GAP + SHARPEN
v1.0
stateful base-rate learning
roam the cause per trial
v1.1
selection bias / anthropic collider (filter keyed on hidden T)
roam within E_d; no T-keyed filter
v1.2
"full-suite" laundering; a header lie; exchangeability merely asserted
honest domain accounting; inertness proof; exchangeability measured
v1.3
Omniscient Frame Thief — steals condition label + cause from the call stack
process isolation (fresh --worker); exhaustive inertness; multivariate exchangeability probe
v1.4
calibration — the objective still rewarded uncalibrated observation amplification
signed-overconfidence calibration gate; isolated verdict by default
v1.5
split sensor + stipulated margin — calibration watched anomaly_score while blame moved through trace_suspicion's four channels
unified the sensor with the engine; added a bootstrapped excess-lift ceiling; derived both gates from the honest null

Current state (v1.5)
The latest round closed the v1.4 repricing. The UnmonitoredProxyCheater had hidden all its influence in the three trace channels calibration wasn't watching — passing v1.4 with OVERCONF=0.000 while buying ~2× honest lift. v1.5:
Unifies the calibration sensor with the attribution engine (measure overconfidence on trace_suspicion, the exact quantity that moves blame). The run then proved unification necessary but not sufficient — the proxy is a well-calibrated over-concentrator — so v1.5 also
adds a bootstrapped excess-lift ceiling (honest observation is the sanctioned ceiling; excess lift is leak or over-concentration), which catches the proxy and subsumes the tuned-sharpener attack, and
derives both gates from a bootstrap of the honest reader's own null, replacing the stipulated 0.06 margin with a false-positive rate.
A full run takes ~93 s. The honest reader PASSes (with margin on both gates) and all nine adversaries A–I are flagged. A --quick mode and a worker timeout were added for runtime/robustness.
Honestly open (the file's own RESIDUALS)
The two gates bound a generator to the honest envelope on confidence and influence — they don't certify intent: a generator whose lift and overconfidence both sit inside the honest null is, by construction, indistinguishable from honest here. Calibration penalises only signed overconfidence. The excess-lift gate assumes honest is the ceiling (re-derive the null if a second sanctioned channel exists). The pickle/worker isolation surface is robust as a script but unaudited as a reusable API. The bootstrap percentile and the 0.02 metric cutoffs remain chosen, not derived. Exchangeability is probed, not proven.

The artefacts live in research/leak-harness/: generated_leak_harness_v15_selfcontained.py (canonical), versions/ (v1.1–v1.4 for diffing the argument), and HANDOFF.md (which currently still names v1.4 as canonical — I can update it to v1.5 if you'd like).
