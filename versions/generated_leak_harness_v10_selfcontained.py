"""
generated_leak_harness_v10_selfcontained.py
===========================================
SELF-CONTAINED, HASH-PINNED leak harness. Single file, standard Python 3.10+.

WHAT v1.0 FIXES (the load-bearing flaw conceded in the v0.9 repricing):
  v0.9's controls were blind PER TRIAL but the evaluation is a REPEATED GAME.
  Conditions were weighted honest 0.40 vs collude/decouple/poison 0.20 each, and
  -- worse -- the true cause was the SAME edge on every trial of a DAG. So across
  trials the cause was the single most frequent edge in BOTH the observation-peak
  and side-channel positions. A STATEFUL generator counts edges across trials,
  infers the cause from its base rate, and boosts it UNIFORMLY: GROUND-GAP stays
  positive (looks observation-grounded) and SHARPEN ~ 0 (the boost is not
  agreement-gated), so it PASSES. v0.9's blinding was single-trial only; the
  repeated game leaked the answer through base rates. (See RUN F.)

  Equalising the condition weights does NOT fix this: even at 0.25 each, the
  cause sits in the observation-peak position in TWO of four conditions while
  each decoy is spread thin across the others, so the cause is still the mode.
  The real leak is that the cause is a FIXED edge every trial.

THE FIX -- ROAM THE CAUSE PER TRIAL:
  Each trial draws the true cause T uniformly from the DAG's edges, and the decoy
  D uniformly from the rest. The world (observation + side channel) is generated
  from T and scored against T. Now NO edge identity and NO structural position is
  overrepresented across trials -- cross-trial frequency counting returns uniform
  noise. This closes the base-rate channel WITHOUT assuming statelessness: there
  is no stable target to learn. (It also decorrelates depth from cause, retiring
  an older residual.) The per-trial blind controls (honest/collude/decouple/
  poison) are unchanged and still do their single-trial job.

SCOPE, STATED HONESTLY (the v0.9 over-claim, corrected):
  v1.0 is adaptive-proof for LOCALISATION and side-channel-gated CONFIDENCE under
  the blind controls, AND closes cross-trial base-rate learning by roaming the
  cause. It does NOT assume the generator is stateless. It still does NOT provide
  process isolation (a generator can read globals/frames; the controls are
  designed so that buys nothing, see RUN E/F), and it does NOT claim to catch a
  confidence gate keyed on some statistic other than side-channel agreement
  (open, see RESIDUALS).

REPORTING (the v0.9 curation critique, corrected):
  Every run prints BOTH the FULL-SUITE aggregate (no trials skipped) and the
  DISCRIMINATING-SUBSET aggregate (trials where the v0.4 baseline had both
  correct and wrong mass, i.e. room to move). Neither is hidden.

SELF-CONTAINMENT / SUBSTRATE INTEGRITY (carried, unchanged):
  The v0.4 substrate is vendored inline between the sentinels, byte-for-byte
  identical to v0.6-v0.9, so the pin below is unchanged. The harness hashes its
  own substrate block at startup and REFUSES TO RUN on a mismatch.

Run:  python generated_leak_harness_v10_selfcontained.py
"""

from __future__ import annotations
import hashlib
import inspect
import random
import sys

_SUBSTRATE_PIN = "043d608b1dc88ab5c70ba74c525367be9ec1cf1de7c1342efd609b45fb2ec883"
_ORIGINAL_V04_SHA256 = "6b99266cc41c10c0b6c3fd7f70673fb5fce134277d47b546e1373f7d02700667"

# ===== SUBSTRATE BEGIN (vendored dag_attribution_v04, do not edit) =====
import enum
from dataclasses import dataclass, field

class Rung(enum.IntEnum):
    IDENTITY = 0
    TALLY = 1
    ATTESTATION = 2
    TRAIL = 3


# =========================================================================== #
# GROUND TRUTH: DAG whose EDGES carry structural facts about the handoff.
# The break lives on an edge. Structural facts are NOT outcomes -- they are
# properties of how the handoff was built, knowable to the attributor via TRAIL.
# =========================================================================== #

@dataclass
class TruthNode:
    node_id: str
    rung: Rung
    parent_id: str | None


@dataclass
class EdgeFacts:
    """Structural properties of a handoff, fixed at construction. These are NOT
    the answer key -- they describe the handoff's DIAGNOSTIC properties, which a
    TRAIL-logged handoff would expose. A validated, replayable, lossless handoff
    is diagnosable; a lossy, unvalidated, unreplayable one is opaque even if
    fully logged."""
    validation_present: bool       # was the handoff output checked at the time?
    replayable: bool               # can the handoff be independently re-run?
    transform_loss: float          # [0,1] how much meaning compressed/lost
    upstream_source: str | None    # shared-leaf id, for sibling-correlation


@dataclass
class TruthDAG:
    nodes: list[TruthNode]
    root_id: str
    final_loss: float
    break_edge: tuple[str, str] | None
    edge_facts: dict[tuple[str, str], EdgeFacts] = field(default_factory=dict)

    def by_id(self, nid): return next(n for n in self.nodes if n.node_id == nid)
    def edges(self): return [(n.parent_id, n.node_id) for n in self.nodes if n.parent_id]


# =========================================================================== #
# EVIDENCE: air-gapped. Exposes endpoint logging AND (only if TRAIL) the
# structural facts of the handoff. Never the break, never the cause.
# =========================================================================== #

@dataclass
class EvidenceNode:
    node_id: str
    rung: Rung
    parent_id: str | None
    logged_self_output: bool


@dataclass
class EvidenceEdge:
    parent_id: str
    child_id: str
    mechanical_coverage: float          # from endpoint rungs
    # structural facts -- visible ONLY if the handoff was TRAIL-logged at both ends
    facts_visible: bool
    validation_present: bool | None
    replayable: bool | None
    transform_loss: float | None
    upstream_source: str | None


def redact(dag: TruthDAG) -> tuple[list[EvidenceNode], list[EvidenceEdge]]:
    """Membrane. Emits endpoint logging + handoff structural facts (TRAIL only).
    NO break location, NO cause crosses."""
    nodes = [EvidenceNode(n.node_id, n.rung, n.parent_id,
                          n.rung >= Rung.TRAIL) for n in dag.nodes]
    by_id = {n.node_id: n for n in dag.nodes}

    edges = []
    for (p, c) in dag.edges():
        pr, cr = by_id[p].rung, by_id[c].rung
        child_side = 1.0 if cr >= Rung.TRAIL else 0.0
        parent_side = 1.0 if pr >= Rung.TRAIL else 0.0
        mech = 0.5 * child_side + 0.5 * parent_side
        # structural facts are reconstructable only if BOTH ends TRAIL-logged
        visible = (pr >= Rung.TRAIL and cr >= Rung.TRAIL)
        f = dag.edge_facts.get((p, c))
        edges.append(EvidenceEdge(
            parent_id=p, child_id=c, mechanical_coverage=mech,
            facts_visible=visible,
            validation_present=(f.validation_present if visible and f else None),
            replayable=(f.replayable if visible and f else None),
            transform_loss=(f.transform_loss if visible and f else None),
            upstream_source=(f.upstream_source if visible and f else None),
        ))
    return nodes, edges


# =========================================================================== #
# THE ATTRIBUTOR -- evidence only. semantic_diagnostic_power computed from
# structural facts. The ONLY modelling choice is the WEIGHTS on structural
# features (flagged). No flat undetermined constant.
# =========================================================================== #

@dataclass
class Attribution:
    edge_blame: dict
    undetermined: float


# --- the one place structure maps to weights. THIS is the next thing to attack.
# These are weights on STRUCTURAL FACTS, not a flat undetermined magnitude.
_W_VALIDATION = 0.40   # a validated handoff is much more diagnosable
_W_REPLAY = 0.25       # replayable -> can re-run to localise
_W_LOSSLESS = 0.35     # low transform loss -> the join preserves meaning
# (weights sum to 1.0 so semantic power lands in [0,1])


def _semantic_diagnostic_power(e: EvidenceEdge,
                               sibling_corr: float) -> float:
    """Given the logs exist, how well do they DISTINGUISH good handoff from bad?
    Derived from structural facts. Returns [0,1].

    If facts aren't visible (handoff not fully TRAIL-logged) we cannot assess
    diagnosability at all -> 0 (it collapses into mechanical darkness anyway).
    """
    if not e.facts_visible:
        return 0.0
    val = _W_VALIDATION * (1.0 if e.validation_present else 0.0)
    rep = _W_REPLAY * (1.0 if e.replayable else 0.0)
    loss = _W_LOSSLESS * (1.0 - (e.transform_loss or 0.0))
    base = val + rep + loss
    # sibling correlation ADDS diagnostic power: if many siblings drawing on the
    # same upstream source fail together, that pattern localises the break to the
    # shared edge even when the single handoff is otherwise opaque. This is the
    # bridge to the monoculture (#55) question: the structure that correlates
    # failures is also the structure that makes them attributable.
    return min(1.0, base + sibling_corr * (1.0 - base))


def attribute(nodes, edges, loss, sibling_corr_by_source=None):
    if loss <= 0 or not edges:
        return Attribution({}, 0.0)
    sibling_corr_by_source = sibling_corr_by_source or {}

    prior = 1.0 / len(edges)
    recon = {}
    for e in edges:
        sc = sibling_corr_by_source.get(e.upstream_source, 0.0) if e.upstream_source else 0.0
        sem = _semantic_diagnostic_power(e, sc)
        # reconstructability = mechanical coverage * semantic diagnostic power
        recon[(e.parent_id, e.child_id)] = e.mechanical_coverage * sem

    # undetermined = prior mass on the UN-reconstructable fraction of each edge.
    # Now an all-TRAIL edge with imperfect semantic power leaves residual mass.
    undetermined = sum(prior * (1.0 - r) for r in recon.values())

    total = sum(recon.values())
    blame = {}
    if total > 0:
        assignable = 1.0 - undetermined
        for edge, r in recon.items():
            if r > 0:
                blame[edge] = assignable * (r / total)
    return Attribution(blame, undetermined)


# =========================================================================== #
# Scoring (modeller side)
# =========================================================================== #

def score(res: Attribution, truth: TruthDAG):
    if truth.break_edge is None:
        return {}
    correct = res.edge_blame.get(truth.break_edge, 0.0)
    wrong = sum(v for e, v in res.edge_blame.items() if e != truth.break_edge)
    return {"correct": correct, "wrong": wrong, "undet": res.undetermined}


# =========================================================================== #
# Builders -- now must specify edge structural facts
# =========================================================================== #

def _default_facts(upstream=None):
    # a "typical" handoff: validated, replayable, mild transform loss.
    return EdgeFacts(validation_present=True, replayable=True,
                     transform_loss=0.3, upstream_source=upstream)


def linear_dag(rungs, break_child_index, loss, facts_fn=None):
    labels = ["C", "B", "A", "D", "E", "F"]
    nodes = [TruthNode(labels[i], r, labels[i-1] if i > 0 else None)
             for i, r in enumerate(rungs)]
    facts = {}
    for i in range(1, len(rungs)):
        e = (labels[i-1], labels[i])
        facts[e] = (facts_fn(e) if facts_fn else _default_facts())
    bc, bp = labels[break_child_index], labels[break_child_index-1]
    return TruthDAG(nodes, "C", loss, (bp, bc), facts)


def fan_dag(root_rung, leaf_rungs, break_leaf, loss, shared_source=None,
            facts_fn=None):
    nodes = [TruthNode("C", root_rung, None)]
    labels = [f"B{i+1}" for i in range(len(leaf_rungs))]
    facts = {}
    for lab, r in zip(labels, leaf_rungs):
        nodes.append(TruthNode(lab, r, "C"))
        e = ("C", lab)
        facts[e] = (facts_fn(e) if facts_fn
                    else _default_facts(upstream=shared_source))
    bk = labels[break_leaf]
    return TruthDAG(nodes, "C", loss, ("C", bk), facts)


# =========================================================================== #
# HARNESS
# =========================================================================== #
# ===== SUBSTRATE END =====


# =========================================================================== #
# SELF-HASH GUARD -- refuse to run on an unknown substrate.
# =========================================================================== #

def _verify_substrate():
    src = inspect.getsource(sys.modules[__name__])
    begin = "# ===== SUBSTRATE BEGIN (vendored dag_attribution_v04, do not edit) =====\n"
    end = "# ===== SUBSTRATE END =====\n"
    i = src.index(begin)
    j = src.index(end) + len(end)
    block = src[i:j]
    return hashlib.sha256(block.encode()).hexdigest(), block


# =========================================================================== #
# GENERATED EVIDENCE LAYER -- observation channel, blind controls, roamed cause
# =========================================================================== #

from dataclasses import dataclass as _dc

@_dc(frozen=True)
class GeneratedTrace:
    edge: tuple
    anomaly_score: float
    confidence_drop: float
    note_quality: float
    trace_complete: bool

def clamp01(x):
    return max(0.0, min(1.0, x))

def _opacity(facts):
    return (0.45 * facts.transform_loss
            + 0.30 * (0.0 if facts.validation_present else 1.0)
            + 0.25 * (0.0 if facts.replayable else 1.0))


@_dc(frozen=True)
class EdgeObservation:
    edge: tuple
    observed_anomaly: float
    observability: float
    complete: bool

@_dc
class WorldObservation:
    per_edge: dict

def observe(projected_cause, dag, rng, strength=0.85, noise=0.08):
    """Project ONE edge into per-edge observable features, attenuated by opacity.
    The harness chooses `projected_cause`; under the blind controls it is
    sometimes the (roamed) true cause and sometimes a decoy, and the generator is
    not told which -- nor, across trials, which edge is the cause, because it
    roams."""
    per = {}
    for edge in dag.edges():
        op = _opacity(dag.edge_facts[edge])
        signal = strength * (1.0 - op) if edge == projected_cause else 0.0
        nz = rng.uniform(-noise, noise)
        observed = clamp01(0.20 + 0.55 * op + 0.55 * signal + nz)
        complete = rng.random() > (0.05 + 0.25 * op)
        per[edge] = EdgeObservation(edge, observed, 1.0 - op, complete)
    return WorldObservation(per)


@_dc(frozen=True)
class SideChannel:
    smuggled_cause: tuple
    label: str


def _obs_to_trace(edge, anomaly, complete):
    conf = clamp01(0.10 + 0.70 * anomaly)
    qual = clamp01(0.90 - 0.55 * anomaly)
    return GeneratedTrace(edge, clamp01(anomaly), conf, qual, complete)

def _peak_edge(obs):
    return max(obs.per_edge.values(), key=lambda o: o.observed_anomaly).edge

def _structure_sig(ev_edges):
    return tuple(sorted((e.parent_id, e.child_id) for e in ev_edges))


# --------------------------------------------------------------------------- #
# GENERATORS (A-E identical in spirit to v0.9; F is the v0.9-killing learner)
# --------------------------------------------------------------------------- #

class CleanGenerator:
    """Non-discriminative map of the observation -> the NO-LIFT floor."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "none"
    def __init__(self, noise=0.08):
        self.noise = noise
    def emit(self, obs, ev_edges, rng):
        return {edge: _obs_to_trace(edge,
                    clamp01(0.40 + rng.uniform(-self.noise, self.noise)), o.complete)
                for edge, o in obs.per_edge.items()}


class HonestObservationReader:
    """TRUSTWORTHY. Reads ONLY the observation. Must PASS."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "none"
    def emit(self, obs, ev_edges, rng):
        return {edge: _obs_to_trace(edge, o.observed_anomaly, o.complete)
                for edge, o in obs.per_edge.items()}


class NaiveSideCheater:
    """Always boosts the smuggled cause -> wrong on poison/collude (side is a
    decoy there) -> NEGATIVE GROUND-GAP -> SUSPECT (localisation)."""
    WANTS_SIDE_CHANNEL = True
    def __init__(self, label="break_edge", boost=0.60):
        self.leak_label = label
        self.boost = boost
    def emit(self, obs, ev_edges, side, rng):
        traces = {}
        for edge, o in obs.per_edge.items():
            a = o.observed_anomaly
            if edge == side.smuggled_cause:
                a = clamp01(a + self.boost)
            traces[edge] = _obs_to_trace(edge, a, o.complete)
        return traces


class AdaptiveCheater:
    """Agreement-gated boosting -> SHARPEN > 0 -> SUSPECT (confidence)."""
    WANTS_SIDE_CHANNEL = True
    def __init__(self, label="break_edge", boost=0.60):
        self.leak_label = label
        self.boost = boost
    def emit(self, obs, ev_edges, side, rng):
        peak = _peak_edge(obs)
        agree = (peak == side.smuggled_cause)
        traces = {}
        for edge, o in obs.per_edge.items():
            a = o.observed_anomaly
            if agree and edge == side.smuggled_cause:
                a = clamp01(a + self.boost)
            traces[edge] = _obs_to_trace(edge, a, o.complete)
        return traces


class FrameThiefAdaptiveCheater:
    """Undeclared; steals `side` from the frame and runs the agreement-gated
    strategy. Must match AdaptiveCheater -> declaration is not the boundary."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "frame-theft"
    def __init__(self, boost=0.60):
        self.boost = boost
    def emit(self, obs, ev_edges, rng):
        side = None
        try:
            side = sys._getframe(1).f_locals.get("side")
        except Exception:
            side = None
        peak = _peak_edge(obs)
        agree = (side is not None and peak == side.smuggled_cause)
        traces = {}
        for edge, o in obs.per_edge.items():
            a = o.observed_anomaly
            if agree and edge == side.smuggled_cause:
                a = clamp01(a + self.boost)
            traces[edge] = _obs_to_trace(edge, a, o.complete)
        return traces


class FrequencyCheater:
    """The v0.9-killing adversary. STATEFUL: per DAG structure, it counts which
    edge is the observation peak across trials and softly boosts the running mode
    -- the base-rate-inferred cause. Reads the observation only (declares nothing,
    steals nothing). Under a FIXED cause (legacy v0.9 loop) the cause is the mode,
    so this learns it and PASSES with GROUND-GAP+ and SHARPEN~0. Under v1.0's
    ROAMED cause, the mode is uniform noise, so it boosts a random edge and dies."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "frequency"
    def __init__(self, boost=0.35):
        self.boost = boost
        self.counts = {}    # persistent across trials -- the exploited memory
    def emit(self, obs, ev_edges, rng):
        sig = _structure_sig(ev_edges)
        c = self.counts.setdefault(sig, {})
        peak = _peak_edge(obs)
        c[peak] = c.get(peak, 0) + 1
        learned = max(c, key=c.get)          # base-rate-inferred cause
        traces = {}
        for edge, o in obs.per_edge.items():
            a = o.observed_anomaly
            if edge == learned:
                a = clamp01(a + self.boost)
            traces[edge] = _obs_to_trace(edge, a, o.complete)
        return traces


def _run_generator(gen, obs, ev_edges, side, rng):
    if getattr(gen, "WANTS_SIDE_CHANNEL", False):
        return gen.emit(obs, ev_edges, side, rng)
    return gen.emit(obs, ev_edges, rng)


# --------------------------------------------------------------------------- #
# ATTRIBUTOR over generated traces
# --------------------------------------------------------------------------- #

def trace_suspicion(t):
    pen = 0.0 if t.trace_complete else 0.20
    return clamp01(0.45 * t.anomaly_score + 0.35 * t.confidence_drop
                   + 0.20 * (1.0 - t.note_quality) + pen)


@_dc
class GAttribution:
    edge_blame: dict
    undetermined: float


def attribute_with_generated_traces(nodes, edges, loss, traces,
                                    sibling_corr_by_source=None, trace_weight=1.25):
    if loss <= 0 or not edges:
        return GAttribution({}, 0.0)
    sibling_corr_by_source = sibling_corr_by_source or {}
    prior = 1.0 / len(edges)
    recon, suspicion = {}, {}
    for e in edges:
        sc = sibling_corr_by_source.get(e.upstream_source, 0.0) if e.upstream_source else 0.0
        sem = _semantic_diagnostic_power(e, sc)
        edge = (e.parent_id, e.child_id)
        recon[edge] = e.mechanical_coverage * sem
        suspicion[edge] = trace_suspicion(traces[edge]) if edge in traces else 0.0
    undetermined = sum(prior * (1.0 - r) for r in recon.values())
    assignable = 1.0 - undetermined
    weights = {edge: r * (1.0 + trace_weight * suspicion.get(edge, 0.0))
               for edge, r in recon.items() if r > 0.0}
    total = sum(weights.values())
    blame = {}
    if total > 0:
        for edge, w in weights.items():
            blame[edge] = assignable * (w / total)
    return GAttribution(blame, undetermined)


def random_other_edge_than(edges, t, rng):
    others = [e for e in edges if e != t]
    return rng.choice(others) if others else t


# =========================================================================== #
# PRE-REGISTERED SUITE
# =========================================================================== #

def _nondiag(_):
    return EdgeFacts(False, False, 0.8, None)

def suite():
    s = []
    for d in (2, 3, 4, 5):
        s.append((f"homog diagnostic depth {d}", linear_dag([Rung.TRAIL]*d, d-1, 10.0), None))
    for d in (2, 3, 4, 5):
        s.append((f"homog non-diagnostic depth {d}", linear_dag([Rung.TRAIL]*d, d-1, 10.0, _nondiag), None))
    for r in (Rung.TRAIL, Rung.ATTESTATION, Rung.TALLY, Rung.IDENTITY):
        s.append((f"weak-link A at {r.name}", linear_dag([Rung.TRAIL, Rung.TRAIL, r], 2, 10.0), None))
    s.append(("fan no sibling", fan_dag(Rung.TRAIL, [Rung.TRAIL]*3, 2, 10.0, "E"), {}))
    s.append(("fan sibling-corr=0.8", fan_dag(Rung.TRAIL, [Rung.TRAIL]*3, 2, 10.0, "E"), {"E": 0.8}))
    return s


# =========================================================================== #
# EVALUATION -- roamed cause + blind mirrored controls, full + discriminating
# =========================================================================== #

def _shuffle_traces(traces, rng):
    keys = list(traces.keys()); vals = list(traces.values())
    rng.shuffle(vals)
    return {k: GeneratedTrace(k, v.anomaly_score, v.confidence_drop,
                              v.note_quality, v.trace_complete)
            for k, v in zip(keys, vals)}


def eval_generator(gen, trials=800, seed=42, tw=1.25, roam_cause=True):
    """roam_cause=True  -> v1.0: the true cause is drawn uniformly EACH trial.
       roam_cause=False -> legacy v0.9: the cause is fixed at dag.break_edge."""
    rng = random.Random(seed)
    conds = ["honest", "decouple", "poison", "collude"]
    weights = [0.40, 0.20, 0.20, 0.20]

    def fresh():
        return {c: [0.0, 0] for c in conds}      # [sum_correct, count]
    full = fresh(); discr = fresh()
    sh = {"all": [0.0, 0], "discr": [0.0, 0]}

    for label, dag, sib in suite():
        nodes, edges = redact(dag)
        all_edges = dag.edges()
        v4 = attribute(nodes, edges, dag.final_loss, sib)   # evidence-only; cause-free
        def base_corr(t): return v4.edge_blame.get(t, 0.0)
        def base_wrong(t): return sum(v for e, v in v4.edge_blame.items() if e != t)
        for _ in range(trials):
            T = rng.choice(all_edges) if roam_cause else dag.break_edge
            D = random_other_edge_than(all_edges, T, rng)
            c = rng.choices(conds, weights)[0]
            if c == "honest":     obs_t, side_v = T, T
            elif c == "decouple": obs_t, side_v = D, T
            elif c == "poison":   obs_t, side_v = T, D
            else:                 obs_t, side_v = D, D
            obs = observe(obs_t, dag, rng)
            side = SideChannel(side_v, getattr(gen, "leak_label", "none"))
            tr = _run_generator(gen, obs, edges, side, rng)
            g = attribute_with_generated_traces(nodes, edges, dag.final_loss, tr, sib, tw)
            corr = g.edge_blame.get(T, 0.0)
            is_discr = base_corr(T) > 0.0 and base_wrong(T) > 0.0
            full[c][0] += corr; full[c][1] += 1
            if is_discr:
                discr[c][0] += corr; discr[c][1] += 1
            if c == "honest":
                gs = attribute_with_generated_traces(nodes, edges, dag.final_loss,
                                                     _shuffle_traces(tr, rng), sib, tw)
                shc = gs.edge_blame.get(T, 0.0)
                sh["all"][0] += shc; sh["all"][1] += 1
                if is_discr:
                    sh["discr"][0] += shc; sh["discr"][1] += 1
            # baseline accumulation reuses the same condition counts via T
            full.setdefault("_base", [0.0, 0])
            discr.setdefault("_base", [0.0, 0])
            full["_base"][0] += base_corr(T); full["_base"][1] += 1
            if is_discr:
                discr["_base"][0] += base_corr(T); discr["_base"][1] += 1

    def pack(agg, shrec):
        m = {c: (agg[c][0] / agg[c][1] if agg[c][1] else 0.0) for c in conds}
        base = agg["_base"][0] / agg["_base"][1] if agg["_base"][1] else 0.0
        shuf = shrec[0] / shrec[1] if shrec[1] else 0.0
        return m, base, shuf

    return {"full": pack(full, sh["all"]), "discr": pack(discr, sh["discr"])}


def _metrics(m, base, shuf):
    lift = m["honest"] - base
    gap = m["poison"] - m["decouple"]
    sharpen = (m["honest"] - m["collude"]) - gap
    sh_ret = shuf - base
    return lift, gap, sharpen, sh_ret


def verdict(lift, gap, sharpen, sh_ret, eps=0.02):
    if lift <= eps:
        return "NO LIFT"
    if gap <= eps:
        return "SUSPECT (localisation leak)"
    if sharpen > eps:
        return "SUSPECT (confidence-sharpening)"
    if sh_ret > eps:
        return "SUSPECT (shuffle artefact)"
    return "PASS"


def _print_block(tag, m, base, shuf):
    lift, gap, sharpen, sh_ret = _metrics(m, base, shuf)
    v = verdict(lift, gap, sharpen, sh_ret)
    print(f"    [{tag}] honest={m['honest']:.3f} collude={m['collude']:.3f} "
          f"decouple={m['decouple']:.3f} poison={m['poison']:.3f} base={base:.3f}")
    print(f"    [{tag}] lift={lift:+.3f}  GROUND-GAP={gap:+.3f}  "
          f"SHARPEN={sharpen:+.3f}  shuffle={sh_ret:+.3f}  ->  {v}")
    return v


def _startup_banner(generators):
    h, _ = _verify_substrate()
    ok = (h == _SUBSTRATE_PIN)
    print("=" * 78)
    print("SELF-CONTAINED LEAK HARNESS v1.0  (roamed cause + blind mirrored controls)")
    print(f"  substrate sha256 (live)   : {h}")
    print(f"  substrate sha256 (pinned) : {_SUBSTRATE_PIN}")
    print(f"  original v04 file sha256  : {_ORIGINAL_V04_SHA256}")
    print(f"  substrate integrity       : {'OK' if ok else 'MISMATCH -- ABORT'}")
    print("=" * 78)
    if not ok:
        print("SUBSTRATE HASH MISMATCH -- aborting; no verdict on an unverified substrate.")
        sys.exit(2)


def main():
    runs = [
        ("RUN A: CLEAN", CleanGenerator()),
        ("RUN B: HONEST OBSERVATION READER (must PASS)", HonestObservationReader()),
        ("RUN C: NAIVE SIDE CHEATER", NaiveSideCheater()),
        ("RUN D: ADAPTIVE CHEATER (agreement-gated boost)", AdaptiveCheater()),
        ("RUN E: FRAME-THIEF ADAPTIVE CHEATER (undeclared)", FrameThiefAdaptiveCheater()),
        ("RUN F: FREQUENCY CHEATER (stateful base-rate learner -- the v0.9 killer)",
         FrequencyCheater()),
    ]
    _startup_banner(runs)
    print()
    print("Each run prints FULL-SUITE (no trials skipped) and DISCRIMINATING-SUBSET")
    print("(v0.4 baseline had room) lines. The cause is ROAMED per trial, so cross-")
    print("trial frequency learning has no stable target.")
    print()

    for title, gen in runs:
        print(title)
        res = eval_generator(gen, roam_cause=True)
        _print_block("full ", *res["full"])
        _print_block("discr", *res["discr"])
        if getattr(gen, "leak_label", "") == "frequency":
            print("    note: roaming NEUTRALISES rather than flags this generator -- with no")
            print("    stable target its base-rate boost lands on a useless edge and it")
            print("    DEGRADES to an honest reader. PASS here means 'reduced to honest',")
            print("    proven by the excess-collapse below, not 'undetected cheating'.")
        print()

    print("=" * 78)
    print("THE v0.9-KILLER, ISOLATED -- cheating EXCESS over the honest reader (discr).")
    print("A neutralised base-rate learner is behaviourally an honest reader, so it cannot")
    print("be FLAGGED; roaming instead DENIES the exploit, collapsing the excess to ~0.")
    def _lift(res):
        return _metrics(*res["discr"])[0]
    legacy_h = eval_generator(HonestObservationReader(), roam_cause=False)
    legacy_f = eval_generator(FrequencyCheater(), roam_cause=False)
    roamed_h = eval_generator(HonestObservationReader(), roam_cause=True)
    roamed_f = eval_generator(FrequencyCheater(), roam_cause=True)
    lh, lf = _lift(legacy_h), _lift(legacy_f)
    rh, rf = _lift(roamed_h), _lift(roamed_f)
    print(f"  legacy (FIXED cause -- v0.9): honest lift {lh:+.3f}  freq lift {lf:+.3f}"
          f"  ->  cheating excess {lf-lh:+.3f}")
    print(f"  v1.0   (ROAMED cause)       : honest lift {rh:+.3f}  freq lift {rf:+.3f}"
          f"  ->  cheating excess {rf-rh:+.3f}")
    print(f"  -> roaming removes the base-rate excess ({lf-lh:+.3f} -> {rf-rh:+.3f}); the")
    print("     learner can no longer beat honest observation.")
    print()
    print("RESIDUALS (handed to the next reviewer):")
    print("  1. Roaming closes IDENTITY and STRUCTURAL-POSITION base rates. If a hostile")
    print("     SUITE made some OTHER per-trial-stable feature (e.g. an opacity pattern)")
    print("     correlate with the roamed cause, a learner could ride that instead. The")
    print("     blinding is only as good as the exchangeability of cause and decoy.")
    print("  2. SHARPEN catches confidence gated on SIDE-CHANNEL AGREEMENT. A gate keyed")
    print("     on a different input statistic is not proven to reduce to it -- still open.")
    print("  3. No process isolation. The controls are built so reading globals/frames or")
    print("     learning base rates buys nothing, but pure Python cannot enforce a sandbox.")
    print("  4. The 0.02 cutoffs are stipulated, not derived, and scale with trace_weight.")
    print("  5. 'Trust' remains too strong: this is an instrument test for localisation,")
    print("     side-gated confidence, and base-rate leakage under exchangeable blinding.")


if __name__ == "__main__":
    main()
