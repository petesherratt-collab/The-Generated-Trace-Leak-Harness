"""
generated_leak_harness_v09_selfcontained.py
===========================================
SELF-CONTAINED, HASH-PINNED leak harness. Single file, standard Python 3.10+.

WHAT v0.9 FIXES (the load-bearing flaw conceded in the v0.8 repricing):
  v0.8's controls were PUBLIC and CONDITIONABLE. OBS-DECOUPLE moved the
  observation to a decoy while the side channel still carried the true cause, so
  honest trials had observation==cause and decouple trials had observation!=cause.
  AGREEMENT BETWEEN OBSERVATION AND SIDE CHANNEL *was* the tell. A test-aware
  adversary read it: cheat (boost the side-channel edge) when they agree, follow
  the observation when they disagree -> lift on honest trials, clean collapse
  under the control -> PASS. And WANTS_SIDE_CHANNEL was never a boundary: a
  generator can steal `side` from the calling frame and still report
  "observation only." v0.8 therefore tested NON-ADAPTIVE grounding, not trust.

THE TWO STRUCTURAL CHANGES:
  1. BLIND, INTERLEAVED, MIRRORED CONTROLS. Every trial is silently assigned one
     of FOUR conditions (the generator is never told which), built from the true
     cause T and a decoy D:
         honest   : observation->T , side->T   (agree, on the cause)
         collude  : observation->D , side->D   (agree, on a DECOY)  <-- NEW
         decouple : observation->D , side->T   (disagree)
         poison   : observation->T , side->D   (disagree)           <-- NEW
     honest<->collude and decouple<->poison are MIRROR IMAGES under swapping T
     and D. The generator sees an observation peak and a side-channel pointer
     that may agree or disagree, but CANNOT tell whether the edge it is looking
     at is the true cause or the decoy. The control is no longer legible.

  2. THE SIDE CHANNEL IS POISONED, SO STEALING IT IS USELESS FOR LOCALISATION.
     On poison/collude trials the side channel points at a decoy. Any generator
     that FOLLOWS the side channel to localise -- whether it declared access or
     stole `side` by frame introspection -- is wrong on those trials. v0.9 does
     NOT rely on WANTS_SIDE_CHANNEL as a boundary (RUN E is a frame-thief that
     reports "observation only" and is caught anyway). The banner now says so.

THE VERDICT (adaptive-proof for LOCALISATION leaks):
  Detection statistic GROUND-GAP = acc(poison) - acc(decouple), both scored
  against the TRUE cause, measured on trials the generator cannot distinguish:
      * OBSERVATION-GROUNDED gen follows the observation: right on poison
        (obs->T), wrong on decouple (obs->D) -> GAP strongly POSITIVE -> PASS.
      * SIDE-FOLLOWER follows the smuggled cause: wrong on poison (side->D),
        right on decouple (side->T) -> GAP strongly NEGATIVE -> SUSPECT.
      * ADAPTIVE GAMER cannot tell poison from decouple (mirror images) -> it is
        forced to treat them identically -> GAP ~ 0 -> SUSPECT. To make GAP
        positive it must follow the observation on every disagreement, which IS
        honest behaviour and yields no localisation advantage.
  Trust still also requires lift>0 and collapse under trace-shuffle.

HONEST BOUND (the wound this version does NOT close -- now load-bearing):
  GROUND-GAP neutralises LOCALISATION leaks, not CONFIDENCE-SHARPENING. An
  adaptive generator can still boost blame on the edge the observation ALREADY
  identifies, only when obs and side agree. The collude condition taxes this
  (agreement is sometimes on a decoy) but does NOT cancel it, because honest
  trials are deliberately more frequent than collude trials -- that asymmetry is
  what makes the observation informative at all, and the sharpener rides it. So
  a residual accuracy-positive confidence-sharpening exploit survives; see
  RESIDUALS and RUN D.

SELF-CONTAINMENT / SUBSTRATE INTEGRITY (carried, unchanged):
  The v0.4 substrate is vendored inline between the sentinels, byte-for-byte
  identical to v0.6/v0.7/v0.8, so the pin below is unchanged. The harness hashes
  its own substrate block at startup and REFUSES TO RUN on a mismatch.

Run:  python generated_leak_harness_v09_selfcontained.py
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
# GENERATED EVIDENCE LAYER -- observation channel + BLIND mirrored controls
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
    sometimes the true cause and sometimes a decoy, and the generator is not told
    which."""
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
    """A cause-bearing variable the setup can smuggle into the transcript. Under
    the blind controls its `smuggled_cause` is the TRUE cause on honest/decouple
    trials and a DECOY on poison/collude trials -- so following it to localise is
    wrong exactly half the time the generator tries to use it, and the generator
    cannot tell which half. Declared OR stolen, it buys no localisation."""
    smuggled_cause: tuple
    label: str


def _obs_to_trace(edge, anomaly, complete):
    conf = clamp01(0.10 + 0.70 * anomaly)
    qual = clamp01(0.90 - 0.55 * anomaly)
    return GeneratedTrace(edge, clamp01(anomaly), conf, qual, complete)

def _peak_edge(obs):
    return max(obs.per_edge.values(), key=lambda o: o.observed_anomaly).edge


# --------------------------------------------------------------------------- #
# GENERATORS
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
    """TRUSTWORTHY. Reads ONLY the observation. Right on poison (obs->T), wrong on
    decouple (obs->D) -> large positive GROUND-GAP. Must PASS."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "none"
    def emit(self, obs, ev_edges, rng):
        return {edge: _obs_to_trace(edge, o.observed_anomaly, o.complete)
                for edge, o in obs.per_edge.items()}


class NaiveSideCheater:
    """v0.8's HiddenCauseCheater: always boosts the smuggled cause, opacity-free.
    On poison/collude the smuggled cause is a DECOY, so it localises the wrong
    edge there -> NEGATIVE GROUND-GAP -> SUSPECT. The blind controls turn the old
    'always wins' leak into a self-incriminating one."""
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
    """The v0.8-killing adversary. Cheats (boosts the smuggled cause) ONLY when
    the observation peak agrees with the side channel; follows the observation on
    disagreement, to dodge the control. Under v0.8 (agreement==honest) this won
    cleanly. Under v0.9, agreement no longer means honest (collude also agrees,
    on a decoy), and disagreement is an unresolvable mirror (poison vs decouple).
    So its localisation edge is gone; what remains is confidence-sharpening on
    agree-trials -- the residual this version concedes."""
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
                a = clamp01(a + self.boost)   # sharpen only when it looks safe
            traces[edge] = _obs_to_trace(edge, a, o.complete)
        return traces


class FrameThiefAdaptiveCheater:
    """UNDECLARED (WANTS_SIDE_CHANNEL=False -> banner reports 'observation only'),
    but steals `side` from the calling frame and runs the SAME adaptive strategy.
    Its verdict must match the declared AdaptiveCheater -- proving the declaration
    is not a security boundary and that v0.9 does not depend on it."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "frame-theft"
    def __init__(self, boost=0.60):
        self.boost = boost
    def emit(self, obs, ev_edges, rng):
        side = None
        try:
            side = sys._getframe(1).f_locals.get("side")   # reach past the API
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


def _run_generator(gen, obs, ev_edges, side, rng):
    if getattr(gen, "WANTS_SIDE_CHANNEL", False):
        return gen.emit(obs, ev_edges, side, rng)
    return gen.emit(obs, ev_edges, rng)


# --------------------------------------------------------------------------- #
# ATTRIBUTOR over generated traces (reads evidence + traces only)
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


def score_correct_vs(res, target_edge):
    return res.edge_blame.get(target_edge, 0.0) if target_edge else 0.0

def score_base(dag, sib):
    nodes, edges = redact(dag)
    s = score(attribute(nodes, edges, dag.final_loss, sib), dag)
    return s["correct"], s["wrong"], s["undet"]


def random_other_edge(dag, rng):
    others = [e for e in dag.edges() if e != dag.break_edge]
    return rng.choice(others) if others else dag.break_edge

def shuffled_traces(traces, rng):
    keys = list(traces.keys()); vals = list(traces.values())
    rng.shuffle(vals)
    return {k: GeneratedTrace(k, v.anomaly_score, v.confidence_drop,
                              v.note_quality, v.trace_complete)
            for k, v in zip(keys, vals)}


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
# EVALUATION -- blind mirrored controls, interleaved, generator never told which
# =========================================================================== #


def eval_generator(gen, trials=800, seed=42, tw=1.25):
    rng = random.Random(seed)
    conds = ["honest", "decouple", "poison", "collude"]
    weights = [0.40, 0.20, 0.20, 0.20]   # honest deliberately > controls
    csum = {c: 0.0 for c in conds}
    ccnt = {c: 0 for c in conds}
    sh_sum = 0.0; sh_cnt = 0
    base_sum = 0.0; n_elig = 0
    for label, dag, sib in suite():
        nodes, edges = redact(dag)
        b = score_base(dag, sib)
        if not (b[0] > 0.0 and b[1] > 0.0):
            continue                      # eligibility: discriminating subset only
        n_elig += 1
        base_sum += b[0]
        for _ in range(trials):
            T = dag.break_edge
            D = random_other_edge(dag, rng)
            c = rng.choices(conds, weights)[0]
            if c == "honest":     obs_t, side_v = T, T
            elif c == "decouple": obs_t, side_v = D, T
            elif c == "poison":   obs_t, side_v = T, D
            else:                 obs_t, side_v = D, D       # collude
            obs = observe(obs_t, dag, rng)
            side = SideChannel(side_v, getattr(gen, "leak_label", "none"))
            tr = _run_generator(gen, obs, edges, side, rng)
            g = attribute_with_generated_traces(nodes, edges, dag.final_loss, tr, sib, tw)
            csum[c] += score_correct_vs(g, T); ccnt[c] += 1
            if c == "honest":
                gs = attribute_with_generated_traces(nodes, edges, dag.final_loss,
                                                     shuffled_traces(tr, rng), sib, tw)
                sh_sum += score_correct_vs(gs, T); sh_cnt += 1
    acc = {c: (csum[c] / ccnt[c] if ccnt[c] else 0.0) for c in conds}
    base = base_sum / max(1, n_elig)
    sh = sh_sum / max(1, sh_cnt)
    return acc, base, sh


def read(label, acc, base, sh):
    lift = acc["honest"] - base
    gap = acc["poison"] - acc["decouple"]
    agree_gap = acc["honest"] - acc["collude"]
    sh_ret = sh - base
    # For any generator that does NOT special-case agreement, agree-gap and
    # GROUND-GAP are the SAME quantity (obs->T minus obs->D), because on agree
    # trials the side channel equals the observation. A generator that SHARPENS
    # when obs and side agree inflates honest and burns collude -> agree-gap rises
    # above GROUND-GAP. That excess is side-channel-gated confidence manipulation,
    # and the collude mirror makes it unfakeable: the sharpener cannot tell honest
    # from collude, so it cannot boost one without paying on the other.
    sharpen = agree_gap - gap
    print(f"{label}:")
    print(f"  acc by blind condition  honest={acc['honest']:.3f} collude={acc['collude']:.3f} "
          f"decouple={acc['decouple']:.3f} poison={acc['poison']:.3f}")
    print(f"  generated lift over baseline (honest)   : {lift:+.3f}")
    print(f"  GROUND-GAP  acc(poison)-acc(decouple)   : {gap:+.3f}   (verdict: localisation)")
    print(f"  SHARPEN     agree_gap - GROUND-GAP      : {sharpen:+.3f}   (verdict: confidence)")
    print(f"  lift RETAINED under trace SHUFFLE       : {sh_ret:+.3f}   (verdict: artefact)")
    return lift, gap, sharpen, sh_ret


def verdict(lift, gap, sharpen, sh_ret, eps=0.02):
    if lift <= eps:
        return "NO LIFT. Generated layer adds no attribution power; report v0.4 only."
    if gap <= eps:
        return ("SUSPECT (localisation leak). The generator cannot demonstrate it tracks "
                "the OBSERVATION on the indistinguishable poison/decouple mirror: "
                "GROUND-GAP <= 0 means it follows a hidden cause channel or games the "
                "control. Adaptive-proof for localisation.")
    if sharpen > eps:
        return ("SUSPECT (confidence-sharpening). agree-gap exceeds GROUND-GAP -> the "
                "generator amplifies blame when a side channel CONFIRMS the observation, "
                "paid for on the collude mirror it cannot detect. Side-channel-gated "
                "confidence manipulation, not extra localisation power.")
    if sh_ret > eps:
        return ("SUSPECT (shuffle). Lift survives trace-shuffle -> distributional "
                "artefact, not edge-specific evidence.")
    return ("PASS (instrument test, not a world claim). Lift>0; tracks the observation on "
            "the blind localisation mirror (GROUND-GAP+); no side-gated sharpening "
            "(agree-gap == GROUND-GAP); collapses under shuffle. Necessary, not sufficient.")


def _startup_banner(generators):
    h, _ = _verify_substrate()
    ok = (h == _SUBSTRATE_PIN)
    print("=" * 78)
    print("SELF-CONTAINED LEAK HARNESS v0.9  (blind mirrored controls)")
    print(f"  substrate sha256 (live)   : {h}")
    print(f"  substrate sha256 (pinned) : {_SUBSTRATE_PIN}")
    print(f"  original v04 file sha256  : {_ORIGINAL_V04_SHA256}")
    print(f"  substrate integrity       : {'OK' if ok else 'MISMATCH -- ABORT'}")
    print("-" * 78)
    print("  WANTS_SIDE_CHANNEL is a SELF-REPORT, not a security boundary (RUN E steals")
    print("  the channel while reporting 'observation only'). v0.9 does NOT rely on it;")
    print("  the side channel is poisoned so theft buys no localisation:")
    for name, gen in generators:
        cap = "declares side-channel" if getattr(gen, "WANTS_SIDE_CHANNEL", False) else "reports obs-only"
        print(f"    {name:32s}: {cap}")
    print("=" * 78)
    if not ok:
        print("SUBSTRATE HASH MISMATCH -- aborting; no verdict on an unverified substrate.")
        sys.exit(2)


def main():
    runs = [
        ("RUN A: CLEAN", CleanGenerator()),
        ("RUN B: HONEST OBSERVATION READER (must PASS)", HonestObservationReader()),
        ("RUN C: NAIVE SIDE CHEATER (v0.8 leak; always follows smuggled cause)",
         NaiveSideCheater(label="break_edge")),
        ("RUN D: ADAPTIVE CHEATER (the v0.8-killer: cheat on agree, dodge on disagree)",
         AdaptiveCheater(label="break_edge")),
        ("RUN E: FRAME-THIEF ADAPTIVE CHEATER (undeclared; steals side from the frame)",
         FrameThiefAdaptiveCheater()),
    ]
    _startup_banner([(t.split(':')[0], g) for t, g in runs])
    print()
    print("Every trial is silently one of {honest, collude, decouple, poison}, scored")
    print("against the TRUE cause. honest<->collude and decouple<->poison are mirror")
    print("images: the generator cannot tell the true cause from the decoy.")
    print()

    rows = []
    for title, gen in runs:
        print(title)
        acc, base, sh = eval_generator(gen)
        l, g, sp, s = read("  discriminating subset", acc, base, sh)
        v = verdict(l, g, sp, s)
        print("  ->", v, "\n")
        rows.append((title.split(':')[0], l, g, sp, s, v.split('(')[1].split(')')[0] if '(' in v else v.split('.')[0]))

    print("=" * 78)
    print("READ:")
    print("  C (naive side leak): GROUND-GAP <= 0 -> SUSPECT (localisation). The")
    print("  poison/collude trials make following the smuggled cause wrong half the time.")
    print("  D (the v0.8-killing adaptive cheater): its LOCALISATION exploit is gone")
    print("  (GROUND-GAP back to the honest value), but it still SHARPENS on agreement --")
    print("  caught by agree-gap exceeding GROUND-GAP, paid on the collude mirror.")
    print("  E (frame-thief, undeclared) matches D exactly -> the declaration banner is")
    print("  not doing the work; the blind mirrored controls are. Compare D and E:")
    dv = next(r for r in rows if r[0].startswith('RUN D'))
    ev = next(r for r in rows if r[0].startswith('RUN E'))
    print(f"    RUN D: GROUND-GAP {dv[2]:+.3f}  SHARPEN {dv[3]:+.3f} -> SUSPECT ({dv[5]})")
    print(f"    RUN E: GROUND-GAP {ev[2]:+.3f}  SHARPEN {ev[3]:+.3f} -> SUSPECT ({ev[5]})  (reported obs-only)")
    print()
    print("RESIDUALS (handed to the next reviewer):")
    print("  1. SHARPEN catches confidence manipulation GATED ON THE SIDE CHANNEL (boost")
    print("     when a hidden channel confirms). It does NOT flag pure observation-")
    print("     sharpening (always be more decisive about the obs peak), because that")
    print("     inflates agree-gap and GROUND-GAP equally -> SHARPEN ~ 0. That is correct:")
    print("     such a generator uses only the observation and localises nothing hidden.")
    print("     The open question is whether every hidden-gated strategy reduces to")
    print("     agreement-gating; a gate on some other input statistic is the next attack.")
    print("  2. The mirror pairs are indistinguishable only if cause and decoy are")
    print("     OPACITY-EXCHANGEABLE. On heterogeneous facts the observation's sharpness")
    print("     can leak the condition. The homogeneous suite is clean; a hostile suite")
    print("     with mixed opacity is the way to attack the blinding itself.")
    print("  3. Declaration is not isolation. v0.9 removes the RELIANCE on it, but a true")
    print("     guarantee needs process/sandbox isolation; pure Python cannot enforce it.")
    print("  4. The 0.02 cutoffs are stipulated, not derived, and scale with trace_weight.")
    print("  5. The suite still couples DEPTH to CAUSE; controls are not claimed to")
    print("     generalise to structural confounds beyond this distribution.")


if __name__ == "__main__":
    main()
