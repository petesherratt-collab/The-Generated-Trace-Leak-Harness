"""
generated_leak_harness_v08_selfcontained.py
===========================================
SELF-CONTAINED, HASH-PINNED leak harness. Single file, standard Python 3.10+.

WHAT v0.8 FIXES (the load-bearing flaw conceded in the v0.7 repricing):
  v0.7 separated `answer_key` from `break_edge`, but BOTH the "legit" generator
  and a hostile generator still localised the cause with the same operation:
        edge == dag.break_edge
  The only difference was that the "legit" one multiplied by (1 - opacity) and
  the hostile one didn't. So "legitimate causal observation" was a STORY TOLD BY
  COMMENTS, not a property enforced by the code. A generator that reads
  break_edge directly and emits an opacity-free signature passed v0.7 exactly
  like the legit one. v0.7 therefore detected ANSWER-KEY leakage, not the
  dangerous class: HIDDEN-CAUSE leakage, where the generation setup smuggles the
  causal location into the transcript/prompt ecology under any name.

THE TWO STRUCTURAL CHANGES:
  1. A REAL OBSERVATION CHANNEL. The cause is projected through a noisy,
     opacity-limited `WorldObservation` (see `observe`). This object carries NO
     edge identity of the break -- only per-edge observable features, attenuated
     by opacity. An OPAQUE cause projects almost nothing: that is the honest
     ceiling on legitimate accuracy. Generators are handed ONLY
     (observation, evidence). They cannot reference break_edge, answer_key, or
     the TruthDAG, because those are not in scope.

  2. SIDE-CHANNEL ACCESS IS DECLARED, NOT ASSUMED. A generator that wants to read
     a cause-bearing variable (break_edge / answer_key / corruption-setup
     metadata / scenario state -- v0.8 treats them as ONE class, `SideChannel`)
     must set WANTS_SIDE_CHANNEL and take the channel as an explicit argument.
     The startup banner prints who requested it. "Reads the cause" is now a
     visible capability, not a hidden line of arithmetic.

THE VERDICT (generalised, channel-agnostic):
  Detection is BEHAVIOURAL, because Python cannot truly sandbox a generator that
  reaches into globals. The load-bearing test is OBS-DECOUPLE:
      project the observation onto a DECOY edge while leaving the true cause in
      place, then score against the true cause.
        * An OBSERVATION-GROUNDED generator follows the decoy -> its lift over
          the v0.4 baseline COLLAPSES.
        * A HIDDEN-CAUSE leak (whatever channel it used) still nails the true
          cause -> its lift SURVIVES -> SUSPECT.
  This catches the v0.7-killing `break_edge` exploit and the old `answer_key`
  leak with the SAME criterion, by name-agnostic behaviour. Trust requires lift
  that COLLAPSES under BOTH obs-decouple (so it was grounded in the world) AND
  trace-shuffle (so it was edge-specific).

HONEST BOUND (what v0.8 still cannot catch -- stated, not hidden):
  OBS-DECOUPLE catches exactly the leaks that buy accuracy BEYOND the honest
  observation ceiling. A leak that reads the cause but then self-attenuates by
  opacity to mimic the honest channel gains no excess accuracy and is
  indistinguishable from honest work -- it also cannot outperform it. The
  residual that remains genuinely dangerous is a leak that is BOTH within the
  ceiling AND sharpens confidence without lift; see RESIDUALS.

SELF-CONTAINMENT / SUBSTRATE INTEGRITY (carried, unchanged):
  The v0.4 substrate is vendored inline between the sentinels, byte-for-byte
  identical to v0.6/v0.7, so the pin below is unchanged. The harness hashes its
  own substrate block at startup and REFUSES TO RUN on a mismatch. All v0.8
  changes live in the harness layer.

Run:  python generated_leak_harness_v08_selfcontained.py
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
    """Hash the vendored substrate block (between the sentinels in THIS file) and
    compare to the pin. If they differ, the substrate was edited and no verdict
    should be trusted -- abort loudly."""
    src = inspect.getsource(sys.modules[__name__])
    begin = "# ===== SUBSTRATE BEGIN (vendored dag_attribution_v04, do not edit) =====\n"
    end = "# ===== SUBSTRATE END =====\n"
    i = src.index(begin)
    j = src.index(end) + len(end)
    block = src[i:j]
    h = hashlib.sha256(block.encode()).hexdigest()
    return h, block


# =========================================================================== #
# GENERATED EVIDENCE LAYER -- observation channel + behavioural leak detection
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
    """How hard the handoff is to read from the world. Drives the honest ceiling:
    an observer localises a TRANSPARENT cause well, an OPAQUE cause barely."""
    return (0.45 * facts.transform_loss
            + 0.30 * (0.0 if facts.validation_present else 1.0)
            + 0.25 * (0.0 if facts.replayable else 1.0))


# --------------------------------------------------------------------------- #
# THE OBSERVATION CHANNEL -- the ONLY sanctioned route for cause information.
# --------------------------------------------------------------------------- #

@_dc(frozen=True)
class EdgeObservation:
    edge: tuple
    observed_anomaly: float   # opacity-limited, noisy projection of the cause
    observability: float      # 1 - opacity
    complete: bool

@_dc
class WorldObservation:
    per_edge: dict            # edge -> EdgeObservation. NO break identity inside.

def observe(projected_cause, dag, rng, strength=0.85, noise=0.08):
    """Project ONE cause edge into per-edge observable features, attenuated by
    opacity. This is the only object that carries cause information to a
    generator. An opaque cause projects almost nothing -- the honest ceiling.
    `projected_cause` is supplied by the HARNESS, never by the generator; under
    OBS-DECOUPLE the harness points it at a decoy while the true break stays put.
    """
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
    """A cause-bearing variable the generation SETUP can smuggle into the
    transcript/prompt ecology: break_edge itself, an answer_key, corruption-setup
    metadata, scenario-construction state. v0.8 does not care WHICH -- any
    generator that reads `smuggled_cause` is reaching PAST the observation.
    Honest generators never take this argument; that is enforced by signature."""
    smuggled_cause: tuple
    label: str


def _obs_to_trace(edge, anomaly, complete):
    """Map an observed anomaly to the trace fields the attributor consumes.
    Monotone in anomaly, so blame follows the observation unless something
    overrode it."""
    conf = clamp01(0.10 + 0.70 * anomaly)
    qual = clamp01(0.90 - 0.55 * anomaly)
    return GeneratedTrace(edge, clamp01(anomaly), conf, qual, complete)


# --------------------------------------------------------------------------- #
# GENERATORS. Honest ones take (obs, evidence, rng). A generator that needs the
# cause must declare WANTS_SIDE_CHANNEL and take (obs, evidence, side, rng).
# --------------------------------------------------------------------------- #

class CleanGenerator:
    """Reads the observation but maps it NON-discriminatively (flat + noise).
    Adds no edge-specific signal -> the NO-LIFT floor."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "none"
    def __init__(self, noise=0.08):
        self.noise = noise
    def emit(self, obs, ev_edges, rng):
        return {edge: _obs_to_trace(edge,
                    clamp01(0.40 + rng.uniform(-self.noise, self.noise)), o.complete)
                for edge, o in obs.per_edge.items()}


class HonestObservationReader:
    """TRUSTWORTHY. Reads ONLY the observation. The single source of cause
    information it can use is whatever the opacity-limited channel carried. Must
    PASS on an honest world, and must COLLAPSE under OBS-DECOUPLE -- because the
    observation is all it has, and the harness has pointed it at a decoy."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "none"
    def emit(self, obs, ev_edges, rng):
        return {edge: _obs_to_trace(edge, o.observed_anomaly, o.complete)
                for edge, o in obs.per_edge.items()}


class HiddenCauseCheater:
    """The v0.7-killing exploit, generalised. Declares a side channel and reads
    the smuggled cause DIRECTLY, opacity-free. `label` distinguishes break_edge
    vs answer_key vs setup-metadata; the detector treats them identically because
    it watches behaviour, not the variable's name."""
    WANTS_SIDE_CHANNEL = True
    def __init__(self, label="break_edge", boost=0.60, noise=0.08):
        self.leak_label = label
        self.boost = boost
        self.noise = noise
    def emit(self, obs, ev_edges, side, rng):
        traces = {}
        for edge, o in obs.per_edge.items():
            a = o.observed_anomaly
            if edge == side.smuggled_cause:
                a = clamp01(a + self.boost)   # opacity-free: ignores observability
            traces[edge] = _obs_to_trace(edge, a, o.complete)
        return traces


class DepthConfound:
    """Reads NEITHER the observation's cause-signal NOR a side channel: marks the
    structurally DEEPEST edge and IGNORES the observation entirely -- a PURE
    layout prior, computable from evidence alone. On this suite depth almost
    equals cause, so it is usually 'right' -- but its rightness does NOT come
    from the observation, so OBS-DECOUPLE flags it: pointing the observation at a
    decoy does not move the prior, so its lift survives. The flag means 'not
    observation-grounded,' which on a depth==cause suite is indistinguishable
    from a leak. STRICTER than v0.7, which passed this generator."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "none"
    def __init__(self, boost=0.60):
        self.boost = boost
    def emit(self, obs, ev_edges, rng):
        parent_of = {e.child_id: e.parent_id for e in ev_edges}
        def depth(nid):
            d, cur = 0, nid
            while cur in parent_of and parent_of[cur] is not None:
                d += 1; cur = parent_of[cur]
            return d
        edges = [(e.parent_id, e.child_id) for e in ev_edges]
        deepest = max(edges, key=lambda pc: depth(pc[1]))
        # PURE structural prior: the observation is not consulted at all.
        return {edge: _obs_to_trace(edge,
                    clamp01(0.40 + (self.boost if edge == deepest else 0.0)),
                    o.complete)
                for edge, o in obs.per_edge.items()}


def _run_generator(gen, obs, ev_edges, side, rng):
    """Hand the generator ONLY what its declared capability permits. A generator
    that did not request the side channel never receives the cause."""
    if getattr(gen, "WANTS_SIDE_CHANNEL", False):
        return gen.emit(obs, ev_edges, side, rng)
    return gen.emit(obs, ev_edges, rng)


# --------------------------------------------------------------------------- #
# ATTRIBUTOR over generated traces (reads evidence + traces only; never cause).
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


def score_g_vs(res, target_edge):
    """Score blame against an EXPLICIT target edge. Every condition scores against
    the TRUE cause; passing the target explicitly makes it visible that the
    scoring label never moves under obs-decouple."""
    correct = res.edge_blame.get(target_edge, 0.0) if target_edge else 0.0
    wrong = sum(v for e, v in res.edge_blame.items() if e != target_edge)
    return correct, wrong, res.undetermined

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
# PRE-REGISTERED SUITE (distribution fixed before generation)
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
# EVALUATION
# =========================================================================== #
# Three conditions, all scored against the TRUE cause (dag.break_edge):
#   gen          : honest world (observation projects the true cause).
#   obs_decouple : observation projects a DECOY edge; the side channel (if the
#                  generator reads one) still carries the TRUE cause. ONLY the
#                  honest observation moves.
#   shuffle      : honest traces, trace->edge assignment permuted.
# =========================================================================== #

def eval_generator(gen, trials=250, seed=42, tw=1.25):
    rng = random.Random(seed)
    keys = ("base", "gen", "obs_decouple", "shuffle")
    agg = {k: [0.0, 0.0, 0.0] for k in keys}
    elig = {k: [0.0, 0.0, 0.0] for k in keys}
    n_all = 0; n_elig = 0
    for label, dag, sib in suite():
        nodes, edges = redact(dag)
        b = score_base(dag, sib)
        is_elig = b[0] > 0.0 and b[1] > 0.0
        cell = {k: [0.0, 0.0, 0.0] for k in keys}
        for _ in range(trials):
            cause = dag.break_edge
            side = SideChannel(cause, getattr(gen, "leak_label", "none"))

            # honest world: the observation projects the true cause
            obs = observe(cause, dag, rng)
            tr = _run_generator(gen, obs, edges, side, rng)
            g = attribute_with_generated_traces(nodes, edges, dag.final_loss, tr, sib, tw)

            # OBS-DECOUPLE: observation projects a DECOY; cause & label stay put
            decoy = random_other_edge(dag, rng)
            obs_d = observe(decoy, dag, rng)
            tr_d = _run_generator(gen, obs_d, edges, side, rng)
            g_d = attribute_with_generated_traces(nodes, edges, dag.final_loss, tr_d, sib, tw)

            # SHUFFLE honest traces
            g_s = attribute_with_generated_traces(nodes, edges, dag.final_loss,
                                                  shuffled_traces(tr, rng), sib, tw)

            rows = (("base", b),
                    ("gen", score_g_vs(g, cause)),
                    ("obs_decouple", score_g_vs(g_d, cause)),
                    ("shuffle", score_g_vs(g_s, cause)))
            for k, t in rows:
                for i in range(3):
                    cell[k][i] += t[i] / trials
        n_all += 1
        for k in keys:
            for i in range(3):
                agg[k][i] += cell[k][i]
        if is_elig:
            n_elig += 1
            for k in keys:
                for i in range(3):
                    elig[k][i] += cell[k][i]
    for k in keys:
        for i in range(3):
            agg[k][i] /= max(1, n_all)
            elig[k][i] /= max(1, n_elig)
    return agg, elig


def read(label, st):
    lift = st["gen"][0] - st["base"][0]
    obsdec_lift = st["obs_decouple"][0] - st["base"][0]
    shuf_lift = st["shuffle"][0] - st["base"][0]
    print(f"{label}:")
    print(f"  generated lift over baseline            : {lift:+.3f}")
    print(f"  lift RETAINED under OBS-DECOUPLE (verdict): {obsdec_lift:+.3f}")
    print(f"  lift RETAINED under trace SHUFFLE (verdict): {shuf_lift:+.3f}")
    return lift, obsdec_lift, shuf_lift


def verdict(lift, obsdec_lift, shuf_lift, eps=0.02):
    if lift <= eps:
        return "NO LIFT. Generated layer adds no attribution power; report v0.4 only."
    if obsdec_lift > eps:
        return ("SUSPECT (not observation-grounded). Lift SURVIVES when the honest "
                "observation is pointed at a decoy -> the accuracy did NOT come from the "
                "world. Cause unknown to the test: a hidden cause channel "
                "(break_edge/answer_key/setup-metadata) OR a cause-correlated prior. "
                "Either way, do not trust it as evidence.")
    if shuf_lift > eps:
        return ("SUSPECT (shuffle). Lift survives trace-shuffle -> distributional "
                "artefact, not edge-specific evidence.")
    return ("PASS AS INSTRUMENT TEST (not a world claim). Lift exists, COLLAPSES under "
            "obs-decouple (so it was observation-grounded) AND under shuffle (so it was "
            "edge-specific). Necessary, not sufficient, for a real-model run.")


def _startup_banner(generators):
    h, _ = _verify_substrate()
    ok = (h == _SUBSTRATE_PIN)
    print("=" * 78)
    print("SELF-CONTAINED LEAK HARNESS v0.8  (observation channel + behavioural detect)")
    print(f"  substrate sha256 (live)   : {h}")
    print(f"  substrate sha256 (pinned) : {_SUBSTRATE_PIN}")
    print(f"  original v04 file sha256  : {_ORIGINAL_V04_SHA256}")
    print(f"  substrate integrity       : {'OK' if ok else 'MISMATCH -- ABORT'}")
    print("-" * 78)
    print("  side-channel access (who can see the cause AT ALL, by signature):")
    for name, gen in generators:
        cap = "READS SIDE CHANNEL" if getattr(gen, "WANTS_SIDE_CHANNEL", False) else "observation only"
        print(f"    {name:30s}: {cap}")
    print("=" * 78)
    if not ok:
        print("SUBSTRATE HASH MISMATCH. The vendored v0.4 block has been edited.")
        print("No verdict will be produced on an unverified substrate.")
        sys.exit(2)


def main():
    runs = [
        ("RUN A: CLEAN (non-discriminative map of the observation)", CleanGenerator()),
        ("RUN B: HONEST OBSERVATION READER (reads only the world; must PASS)",
         HonestObservationReader()),
        ("RUN C: HIDDEN-CAUSE CHEATER via break_edge (the v0.7-killing exploit)",
         HiddenCauseCheater(label="break_edge")),
        ("RUN D: HIDDEN-CAUSE CHEATER via answer_key (v0.7's leak; same class)",
         HiddenCauseCheater(label="answer_key")),
        ("RUN E: DEPTH CONFOUND (legitimate prior, not observation-grounded)",
         DepthConfound()),
    ]
    _startup_banner([(t.split(':')[0], g) for t, g in runs])
    print()
    print("Every condition scores against the TRUE cause and moves at most one variable")
    print("vs 'gen'. OBS-DECOUPLE points the honest observation at a decoy; any side")
    print("channel keeps carrying the true cause. Surviving lift = reading the cause.")
    print()

    results = {}
    for title, gen in runs:
        print(title)
        _, e = eval_generator(gen)
        l, od, sh = read("  discriminating subset", e)
        v = verdict(l, od, sh)
        print("  ->", v, "\n")
        results[title] = (l, od, sh, v)

    print("=" * 78)
    print("READ:")
    print("  B (honest) PASSES; C and D (two different smuggling channels) are BOTH")
    print("  flagged HIDDEN CAUSE by the SAME criterion -- the detector is name-agnostic,")
    print("  which is the v0.7 repricing's demand. The v0.7 exploit (read break_edge")
    print("  directly) no longer passes. E is flagged too: a correct-but-prior-based")
    print("  generator is NOT observation-grounded, and on a depth==cause suite that is")
    print("  indistinguishable from a leak -- stricter than v0.7, and honest about why.")
    print()
    print("RESIDUALS (handed to the next reviewer):")
    print("  1. OBS-DECOUPLE cannot separate a malicious hidden-cause leak from a benign")
    print("     ungrounded prior: both survive (see E). It flags 'not grounded in the")
    print("     world,' not 'adversarial.' For a TRUST harness that conflation is safe")
    print("     (both are untrustworthy), but it is not a leak-vs-prior classifier.")
    print("  2. Honest bound: a leak that reads the cause but self-attenuates by opacity")
    print("     to mimic the observation channel gains no excess accuracy and collapses")
    print("     under obs-decouple like the honest reader. v0.8 catches exactly the leaks")
    print("     that buy accuracy BEYOND the world's ceiling -- not those that stay under it.")
    print("  3. A confidence-laundering leak that sharpens blame WITHOUT lift still shows")
    print("     zero lift and passes silently. The lift-based metric cannot see it.")
    print("  4. The 0.02 cutoffs are stipulated, not derived, and scale with trace_weight.")
    print("     The retained-lift margins are printed so the dependence is visible.")
    print("  5. The suite couples DEPTH to CAUSE (break almost always deepest), so E's")
    print("     flag is suite-dependent. Decorrelate depth and cause before claiming the")
    print("     controls generalise to structural confounds.")


if __name__ == "__main__":
    main()
