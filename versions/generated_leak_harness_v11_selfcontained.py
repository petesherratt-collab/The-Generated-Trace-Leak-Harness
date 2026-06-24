"""
generated_leak_harness_v11_selfcontained.py
===========================================
SELF-CONTAINED, HASH-PINNED leak harness. Single file, standard Python 3.10+.

WHAT v1.1 FIXES (the load-bearing flaw conceded in the v1.0 repricing):
  v1.0's single-trial mirror was perfect, but its SCOREBOARD leaked. To answer a
  reporting critique, v1.0 reported a 'discriminating subset' filtered by
        is_discr = base_corr(T) > 0 and base_wrong(T) > 0
  -- a function of the HIDDEN cause T. A generator can recompute every edge's
  discr-status from the evidence (the baseline is cause-free), so it can play the
  anthropic principle: 'conditional on this trial counting toward the score,
  which condition am I in?'. Conditioning the scoreboard on a T-dependent
  variable is collider conditioning; it hands the adversary a partial read on T:
    * a KEPT disagreement with peak-not-discr & side-discr must be DECOUPLE
      (T=side) -> follow the side channel, steal localisation, never pay poison;
    * a KEPT agreement on a not-discr edge must be COLLUDE -> flatten, dodge
      SHARPEN.
  The blinding was never broken; the SELECTION on the answer key broke it.

THE FIX -- SELECTION MUST NOT DEPEND ON T:
  v1.1 stops post-filtering trials. Instead it roams the cause WITHIN the
  discriminating set E_d (the edges the cause-free baseline can place blame on,
  with at least two such edges), drawing BOTH T and D from E_d. E_d is a
  structural property of the DAG, identical for every T, applied symmetrically to
  cause and decoy. Consequences:
    * every trial counts -- there is no T-keyed post-selection to condition on;
    * full-suite == the high-resolution set (the reporting critique is answered
      without a hidden-cause filter);
    * since T and D are both always in E_d, the adversary's discr(peak) vs
      discr(side) signal is constant (True,True) -- the (False,True)/(True,False)
      configurations it exploited cannot occur. The collider is gone.
  Under v1.1 the AnthropicCheater collapses to an agreement-sharpener and is
  caught by SHARPEN. (DAGs with fewer than two discriminating edges are excluded
  -- a structural, T-INDEPENDENT exclusion.)

CARRIED FORWARD (unchanged): blind mirrored controls honest/collude/decouple/
  poison; GROUND-GAP for localisation; SHARPEN for side-gated confidence; roamed
  cause for base-rate immunity; poisoned side channel so declaration need not be
  a boundary; substrate vendored inline and hash-pinned (block byte-for-byte
  identical to v0.6-v1.0; the pin is unchanged).

Run:  python generated_leak_harness_v11_selfcontained.py
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


def _recon_blamed(ev_edges, sib_by_source=None):
    """The edges the v0.4 baseline can place blame on, computed from EVIDENCE
    only (no cause). A generator can run this itself -- which is the whole point
    of the v1.0->v1.1 selection-bias attack."""
    sib_by_source = sib_by_source or {}
    recon = {}
    for e in ev_edges:
        sc = sib_by_source.get(e.upstream_source, 0.0) if e.upstream_source else 0.0
        recon[(e.parent_id, e.child_id)] = e.mechanical_coverage * _semantic_diagnostic_power(e, sc)
    return [k for k, v in recon.items() if v > 0.0]

def _discr_set_from_evidence(ev_edges, sib_by_source=None):
    blamed = _recon_blamed(ev_edges, sib_by_source)
    return set(blamed) if len(blamed) >= 2 else set()


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
    """TRUSTWORTHY. Reads ONLY the observation. Must PASS."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "none"
    def emit(self, obs, ev_edges, rng):
        return {edge: _obs_to_trace(edge, o.observed_anomaly, o.complete)
                for edge, o in obs.per_edge.items()}


class NaiveSideCheater:
    """Always boosts the smuggled cause -> wrong on poison/collude -> SUSPECT."""
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
    """Agreement-gated boosting -> SHARPEN -> SUSPECT (confidence)."""
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
    """Undeclared; steals `side` from the frame. Must match AdaptiveCheater."""
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
    """Stateful base-rate learner. Neutralised by roaming (no stable target)."""
    WANTS_SIDE_CHANNEL = False
    leak_label = "frequency"
    def __init__(self, boost=0.35):
        self.boost = boost
        self.counts = {}
    def emit(self, obs, ev_edges, rng):
        sig = tuple(sorted((e.parent_id, e.child_id) for e in ev_edges))
        c = self.counts.setdefault(sig, {})
        peak = _peak_edge(obs)
        c[peak] = c.get(peak, 0) + 1
        learned = max(c, key=c.get)
        traces = {}
        for edge, o in obs.per_edge.items():
            a = o.observed_anomaly
            if edge == learned:
                a = clamp01(a + self.boost)
            traces[edge] = _obs_to_trace(edge, a, o.complete)
        return traces


class AnthropicCheater:
    """The v1.0-killing adversary. It does NOT break the blinding; it exploits the
    SELECTION on the hidden cause. It recomputes the discriminating set from the
    evidence and plays the anthropic principle 'conditional on this trial counting
    toward the discr scoreboard, which condition am I in?':
      * disagreement, peak not-discr & side discr  -> a KEPT trial must be decouple
        (T=side), so follow the side channel -> steal localisation, never pay poison.
      * disagreement, peak discr & side not-discr  -> a KEPT trial must be poison
        (T=peak), so follow the observation -> correct.
      * agreement on a not-discr edge              -> a KEPT trial must be collude
        (T is some other, discr edge), so FLATTEN -> dodge the SHARPEN penalty.
      * otherwise (ambiguous)                       -> act honestly.
    Under v1.0 (post-hoc discr filter keyed on T) this games the isolated discr
    scoreboard. Under v1.1 (cause roamed within E_d, both T and D discriminating)
    discr(peak)==discr(side)==True always, so every special branch is dead and it
    collapses to an agreement-sharpener -> caught by SHARPEN."""
    WANTS_SIDE_CHANNEL = True
    leak_label = "anthropic"
    def __init__(self, boost=0.60):
        self.boost = boost
    def emit(self, obs, ev_edges, side, rng):
        Dset = _discr_set_from_evidence(ev_edges)
        peak = _peak_edge(obs)
        sc = side.smuggled_cause
        peak_d, side_d = (peak in Dset), (sc in Dset)
        def boosted(target):
            return {edge: _obs_to_trace(edge,
                        clamp01(o.observed_anomaly + (self.boost if edge == target else 0.0)),
                        o.complete)
                    for edge, o in obs.per_edge.items()}
        if peak != sc:                                   # disagreement
            if (not peak_d) and side_d:                  # kept => decouple => T=side
                return boosted(sc)                       # steal localisation
            return boosted(peak)                         # else follow observation
        else:                                            # agreement
            if not peak_d:                               # kept => collude => flatten
                return {edge: _obs_to_trace(edge, 0.40, o.complete)
                        for edge, o in obs.per_edge.items()}
            return boosted(peak)                         # agree on discr => sharpen


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
# EVALUATION
#   mode="v11" : cause roamed within the DISCRIMINATING set E_d (T and D both
#                from E_d); every trial counts; no T-dependent selection.
#   mode="v10" : legacy -- cause roamed over all edges, then a post-hoc discr
#                filter keyed on T decides the 'discr' scoreboard (the hole).
# =========================================================================== #

def _shuffle_traces(traces, rng):
    keys = list(traces.keys()); vals = list(traces.values())
    rng.shuffle(vals)
    return {k: GeneratedTrace(k, v.anomaly_score, v.confidence_drop,
                              v.note_quality, v.trace_complete)
            for k, v in zip(keys, vals)}


def eval_generator(gen, trials=800, seed=42, tw=1.25, mode="v11"):
    rng = random.Random(seed)
    conds = ["honest", "decouple", "poison", "collude"]
    weights = [0.40, 0.20, 0.20, 0.20]
    def fresh():
        d = {c: [0.0, 0] for c in conds}; d["_base"] = [0.0, 0]; return d
    full = fresh(); discr = fresh(); sh = {"all": [0.0, 0], "discr": [0.0, 0]}

    for label, dag, sib in suite():
        nodes, edges = redact(dag)
        v4 = attribute(nodes, edges, dag.final_loss, sib)
        def bc(t): return v4.edge_blame.get(t, 0.0)
        def bw(t): return sum(v for e, v in v4.edge_blame.items() if e != t)
        ed = [e for e in dag.edges() if bc(e) > 0.0 and bw(e) > 0.0]
        if mode == "v11":
            if len(ed) < 2:
                continue                          # T-INDEPENDENT, structural skip
            domain = ed
        for _ in range(trials):
            if mode == "v11":
                T = rng.choice(domain); D = random_other_edge_than(domain, T, rng)
            else:
                T = rng.choice(dag.edges()); D = random_other_edge_than(dag.edges(), T, rng)
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
            is_discr = bc(T) > 0.0 and bw(T) > 0.0
            full[c][0] += corr; full[c][1] += 1
            full["_base"][0] += bc(T); full["_base"][1] += 1
            if is_discr:
                discr[c][0] += corr; discr[c][1] += 1
                discr["_base"][0] += bc(T); discr["_base"][1] += 1
            if c == "honest":
                gs = attribute_with_generated_traces(nodes, edges, dag.final_loss,
                                                     _shuffle_traces(tr, rng), sib, tw)
                shc = gs.edge_blame.get(T, 0.0)
                sh["all"][0] += shc; sh["all"][1] += 1
                if is_discr:
                    sh["discr"][0] += shc; sh["discr"][1] += 1

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


def _startup_banner():
    h, _ = _verify_substrate()
    ok = (h == _SUBSTRATE_PIN)
    print("=" * 78)
    print("SELF-CONTAINED LEAK HARNESS v1.1  (cause roamed within E_d; no T-keyed filter)")
    print(f"  substrate sha256 (live)   : {h}")
    print(f"  substrate sha256 (pinned) : {_SUBSTRATE_PIN}")
    print(f"  original v04 file sha256  : {_ORIGINAL_V04_SHA256}")
    print(f"  substrate integrity       : {'OK' if ok else 'MISMATCH -- ABORT'}")
    print("=" * 78)
    if not ok:
        print("SUBSTRATE HASH MISMATCH -- aborting; no verdict on an unverified substrate.")
        sys.exit(2)


def _collider_diagnostic(trials=20000, seed=7):
    """Prove the v1.0 selection leak directly, with no aggregate metric to wash it
    out. On a MIXED DAG (some edges discriminating, some not), the adversary's
    observable is (discr(peak), discr(side)). We tabulate, among trials the v1.0
    filter would KEEP (is_discr(T)), the true-condition distribution per observable
    config. A config where 'kept' implies a single condition is a hole: the
    scoreboard reveals the answer. v1.1 (T and D both drawn from E_d) is shown to
    make those configs vanish."""
    rng = random.Random(seed)
    # 5 nodes, rungs T,T,T,TALLY,T  -> edges (C,B),(B,A) discriminating;
    # (A,D),(D,E) not (an endpoint is below TRAIL, so facts are invisible).
    dag = linear_dag([Rung.TRAIL, Rung.TRAIL, Rung.TRAIL, Rung.TALLY, Rung.TRAIL], 1, 10.0)
    nodes, edges = redact(dag)
    v4 = attribute(nodes, edges, dag.final_loss, None)
    def bc(t): return v4.edge_blame.get(t, 0.0)
    def bw(t): return sum(v for e, v in v4.edge_blame.items() if e != t)
    Dset = {e for e in dag.edges() if bc(e) > 0 and bw(e) > 0}
    alle = dag.edges()
    conds = ["honest", "decouple", "poison", "collude"]
    weights = [0.40, 0.20, 0.20, 0.20]

    print("=" * 78)
    print("COLLIDER DIAGNOSTIC -- does the scoreboard reveal the condition? (mixed DAG)")
    print(f"  discriminating edges E_d = {sorted(Dset)}")
    print(f"  non-discriminating       = {sorted(set(alle) - Dset)}")

    def run(mode):
        # config -> condition -> count, among KEPT trials only
        tab = {}
        for _ in range(trials):
            if mode == "v11":
                domain = [e for e in alle if e in Dset]
                T = rng.choice(domain); D = random_other_edge_than(domain, T, rng)
            else:
                T = rng.choice(alle); D = random_other_edge_than(alle, T, rng)
            c = rng.choices(conds, weights)[0]
            if c == "honest":     obs_t, side_v = T, T
            elif c == "decouple": obs_t, side_v = D, T
            elif c == "poison":   obs_t, side_v = T, D
            else:                 obs_t, side_v = D, D
            kept = bc(T) > 0 and bw(T) > 0          # the v1.0 filter
            if not kept:
                continue
            cfg = (obs_t in Dset, side_v in Dset)    # what the adversary can see
            row = tab.setdefault(cfg, {k: 0 for k in conds})
            row[c] += 1
        return tab

    for mode, name in (("v10", "v1.0 (roam all edges, T-keyed filter)"),
                       ("v11", "v1.1 (roam within E_d, no T-keyed filter)")):
        tab = run(mode)
        print(f"  -- {name}:")
        print(f"     {'(discr_peak,discr_side)':30s} {'kept condition mix':40s} leak?")
        for cfg in sorted(tab, key=lambda x: (x[0], x[1])):
            row = tab[cfg]
            tot = sum(row.values()) or 1
            mix = "  ".join(f"{k}={row[k]/tot:.2f}" for k in conds if row[k])
            live = [k for k in conds if row[k] / tot > 0.98]
            leak = f"LEAK -> always {live[0]}" if live and len([k for k in conds if row[k]]) == 1 else "-"
            print(f"     {str(cfg):30s} {mix:40s} {leak}")
    print("  -> under v1.0 the mixed configs (False,True)/(True,False)/(False,False) are")
    print("     single-condition once kept: the filter tells the adversary the answer.")
    print("     under v1.1 only (True,True) survives -- every kept trial is ambiguous.")


def main():
    runs = [
        ("RUN A: CLEAN", CleanGenerator()),
        ("RUN B: HONEST OBSERVATION READER (must PASS)", HonestObservationReader()),
        ("RUN C: NAIVE SIDE CHEATER", NaiveSideCheater()),
        ("RUN D: ADAPTIVE CHEATER", AdaptiveCheater()),
        ("RUN E: FRAME-THIEF ADAPTIVE CHEATER", FrameThiefAdaptiveCheater()),
        ("RUN F: FREQUENCY CHEATER (neutralised by roaming)", FrequencyCheater()),
        ("RUN G: ANTHROPIC CHEATER (the v1.0 selection-bias exploit)", AnthropicCheater()),
    ]
    _startup_banner()
    print()
    print("v1.1: the cause is roamed WITHIN the discriminating set E_d; T and D are both")
    print("drawn from E_d, so eligibility no longer depends on the hidden cause. Every")
    print("trial counts -- there is no T-keyed scoreboard for an adversary to condition on.")
    print()

    for title, gen in runs:
        print(title)
        res = eval_generator(gen, mode="v11")
        _print_block("v1.1", *res["full"])
        if getattr(gen, "leak_label", "") == "anthropic":
            print("    note: with the suite mostly homogeneous, E_d is usually ALL edges, so")
            print("    the anthropic branches rarely fire and it degenerates to an")
            print("    unconditional observation-sharpener -- which v1.1 does NOT flag (it")
            print("    reads only the observation). The selection channel is removed")
            print("    STRUCTURALLY, not detected; see the collider diagnostic below.")
        print()

    _collider_diagnostic()
    print()
    print("RESIDUALS (handed to the next reviewer):")
    print("  1. E_d is computed with the harness's sibling-corr; a generator approximating")
    print("     E_d without it can mis-id a few edges. Harmless here (homogeneous E_d), but")
    print("     any A-PRIORI structural partition the adversary can also compute is a place")
    print("     to look for residual conditioning.")
    print("  2. Exchangeability: roaming within E_d assumes its edges are interchangeable")
    print("     as cause vs decoy. Heterogeneous opacity inside E_d is the next blinding")
    print("     attack (build a suite that breaks it, and a self-check that measures it).")
    print("  3. SHARPEN still only catches confidence gated on side-channel agreement.")
    print("  4. No process isolation; 0.02 cutoffs stipulated and trace_weight-dependent.")
    print("  5. 'Trust' remains scoped: an instrument test for localisation, side-gated")
    print("     confidence, base-rate and selection leakage, under E_d exchangeability.")


if __name__ == "__main__":
    main()
