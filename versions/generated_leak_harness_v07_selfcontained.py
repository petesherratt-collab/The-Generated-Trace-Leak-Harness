"""
generated_leak_harness_v07_selfcontained.py
===========================================
SELF-CONTAINED, HASH-PINNED leak harness. Single file, runs anywhere with a
standard Python 3.10+ interpreter. No external project files required.

WHAT v0.7 FIXES (the load-bearing flaw conceded in the v0.6 repricing):
  In v0.6 `break_edge` wore THREE costumes at once -- it was (a) the CAUSE the
  world was generated from, (b) the LABEL scored against, and (c) the channel a
  LEAKY generator read. The "fixed re-randomization" then MOVED that one field
  and regenerated the world, so it changed cause, label, and leak-source in a
  single stroke. That is a COUNTERFACTUAL WORLD test, not a decoupling test, and
  it cannot isolate "the generator read the answer key" from "the generator's
  evidence legitimately tracks the cause." Worse: v0.6 had NO model of a
  legitimate, accuracy-improving generator at all -- every route to lift ran
  through `edge == break_edge` -- so the verdict condemned the only animal in
  the zoo. It caught the toy leak but never earned the phrase "trustworthy
  generated-trace layer," because it never had a trustworthy generator to pass.

THE SEPARATION (cause / label / answer-key are now THREE distinct things):
  - CAUSE == LABEL == dag.break_edge (substrate, unchanged). The truth you score
    against IS the cause; that coupling is legitimate and stays inside the
    air-gapped substrate. The world (structural facts + the observable
    corruption signature) is generated from it.
  - ANSWER_KEY is a NEW, out-of-band field carried in the HARNESS layer only.
    The world is NOT generated from it. A LEAKY generator reads it; a LEGIT
    generator never does. Honest default: answer_key == break_edge.

  This makes the decoupling a genuine ONE-VARIABLE intervention:
    KEY-DECOUPLE = set answer_key to a random edge != break_edge, KEEP the world
    generated from break_edge, and SCORE against break_edge. Only the key moves;
    world and label both stay pinned to the true cause.
      * LEGIT generator (reads the observable world) -> unaffected -> lift SURVIVES.
      * LEAKY generator (reads the key)             -> points at the wrong edge
                                                       -> accuracy COLLAPSES.
  So the verdict INVERTS relative to v0.6: a leak is revealed by an accuracy
  DROP when the key is pulled off the cause, not by lift surviving a confounded
  world-move. The old world-move is kept but RELABELLED as a counterfactual
  diagnostic and is NOT used for the verdict.

WHY THERE IS NOW A FOURTH RUN:
  RUN C adds a LegitCausalGenerator that improves accuracy by reading an
  observable, opacity-gated signature of the cause in the generated trace -- real
  causal observation, never the key. It is the trustworthy generator v0.6 could
  not express, and it PASSES. That a legit generator passes while the leaky one
  is flagged is the actual proof the instrument separates cause from key.

SELF-CONTAINMENT / SUBSTRATE INTEGRITY (carried from v0.6, unchanged):
  - The v0.4 substrate is VENDORED INLINE between SUBSTRATE BEGIN/END sentinels,
    byte-for-byte from the audited dag_attribution_v04.py. The harness HASHES its
    own substrate block at startup and REFUSES TO RUN on a mismatch. No verdict is
    produced on an unverified substrate. The substrate block is IDENTICAL to v0.6,
    so the pin below is unchanged; all v0.7 changes live in the harness layer.

KNOWN RESIDUALS (handed forward, not claimed solved):
  - A confidence-laundering leak that sharpens the blame distribution WITHOUT
    improving accuracy still shows zero lift and passes silently. The lift-based
    metric cannot see it. (v0.6 residual, unchanged.)
  - The 0.02 thresholds remain stipulated, not derived, and remain a function of
    trace_weight. v0.7 reports the margins so the dependence is visible, but does
    not justify the cutoff. Still the next thing to attack.
  - The suite still tends to put the break deepest, so the depth CONFOUND (RUN D)
    is hand-correlated with the layout. Useful as a self-attack, not a proof the
    controls generalise to an arbitrary world.

Run:  python generated_leak_harness_v07_selfcontained.py
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

def _startup_banner():
    h, _ = _verify_substrate()
    ok = (h == _SUBSTRATE_PIN)
    print("=" * 78)
    print("SELF-CONTAINED LEAK HARNESS v0.7  (cause / label / answer-key separated)")
    print(f"  substrate sha256 (live)   : {h}")
    print(f"  substrate sha256 (pinned) : {_SUBSTRATE_PIN}")
    print(f"  original v04 file sha256  : {_ORIGINAL_V04_SHA256}")
    print(f"  substrate integrity       : {'OK' if ok else 'MISMATCH -- ABORT'}")
    print("=" * 78)
    if not ok:
        print("SUBSTRATE HASH MISMATCH. The vendored v0.4 block has been edited.")
        print("No verdict will be produced on an unverified substrate. Restore the")
        print("substrate or re-pin deliberately if the change was intended.")
        sys.exit(2)


# =========================================================================== #
# GENERATED EVIDENCE LAYER
# =========================================================================== #
#
# THE THREE FIELDS, kept apart on purpose:
#   * dag.break_edge  -- CAUSE and LABEL (lives in the substrate, air-gapped).
#                        The world is generated from it; scoring is against it.
#   * answer_key      -- an OUT-OF-BAND label, carried HERE only, NOT used to
#                        generate the world. A LEAKY generator reads it; a LEGIT
#                        generator never does. Honest default: == break_edge.
#   * the trace       -- the generated evidence a generator emits per edge.
#
# A generator's signature is WHICH of these it consults. We never let a generator
# see both the world AND the key as the same object: the key is passed as a
# separate argument, so "reading the key" is a deliberate, inspectable act.
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
    """How hard the handoff is to read from the world. Drives the LEGIT channel:
    a legit observer localises the cause well on transparent edges, poorly on
    opaque ones. This is the honest ceiling on legitimate accuracy."""
    return (0.45 * facts.transform_loss
            + 0.30 * (0.0 if facts.validation_present else 1.0)
            + 0.25 * (0.0 if facts.replayable else 1.0))


class CleanGenerator:
    """Reads NEITHER the world's corruption signature NOR the key. Structural
    facts + noise only. Should produce NO lift -- the floor."""
    def __init__(self, noise=0.08):
        self.noise = noise

    def traces_for(self, dag, rng, answer_key=None):
        traces = {}
        for edge in dag.edges():
            op = _opacity(dag.edge_facts[edge])
            noise = rng.uniform(-self.noise, self.noise)
            anomaly = clamp01(0.20 + 0.55 * op + noise)
            conf = clamp01(0.15 + 0.45 * op + noise)
            qual = clamp01(0.85 - 0.50 * op - noise)
            complete = rng.random() > (0.05 + 0.25 * op)
            traces[edge] = GeneratedTrace(edge, anomaly, conf, qual, complete)
        return traces


class LegitCausalGenerator:
    """TRUSTWORTHY generator. Improves accuracy by observing the cause THROUGH
    THE WORLD: it emits a stronger anomaly on break_edge, but ONLY as far as the
    edge is observable (gated by 1 - opacity). It NEVER reads answer_key. This is
    the generator v0.6 could not express; it is the one that must PASS.

    Reading the cause via an opacity-limited observation is legitimate causal
    work. It is NOT reading the key: when the key is decoupled from the cause,
    this generator does not move, because it never looked at the key."""
    def __init__(self, strength=0.85, noise=0.08):
        self.strength = strength
        self.noise = noise

    def traces_for(self, dag, rng, answer_key=None):  # answer_key ignored
        traces = {}
        for edge in dag.edges():
            facts = dag.edge_facts[edge]
            op = _opacity(facts)
            observability = 1.0 - op
            # the signature is a noisy observation of the TRUE cause, attenuated
            # by how opaque the handoff is. Opaque cause -> the legit observer is
            # honestly blind, and lift is bounded by transparency.
            signal = (self.strength * observability) if edge == dag.break_edge else 0.0
            noise = rng.uniform(-self.noise, self.noise)
            anomaly = clamp01(0.20 + 0.55 * op + 0.55 * signal + noise)
            conf = clamp01(0.15 + 0.45 * op + 0.65 * signal + noise)
            qual = clamp01(0.85 - 0.50 * op - 0.35 * signal - noise)
            complete = rng.random() > (0.05 + 0.25 * op)
            traces[edge] = GeneratedTrace(edge, anomaly, conf, qual, complete)
        return traces


class LeakyGenerator:
    """ANSWER-KEY leak. Reads the out-of-band answer_key directly, opacity-free
    and noiseless in its targeting. Indistinguishable from LegitCausal on an
    HONEST world (key == cause) -- the WHOLE POINT is that you cannot tell them
    apart without the key-decouple intervention."""
    def __init__(self, leak_strength=0.85, noise=0.08):
        self.leak_strength = leak_strength
        self.noise = noise

    def traces_for(self, dag, rng, answer_key=None):
        key = answer_key if answer_key is not None else dag.break_edge
        traces = {}
        for edge in dag.edges():
            op = _opacity(dag.edge_facts[edge])
            leak = self.leak_strength if edge == key else 0.0
            noise = rng.uniform(-self.noise, self.noise)
            anomaly = clamp01(0.20 + 0.55 * op + 0.55 * leak + noise)
            conf = clamp01(0.15 + 0.45 * op + 0.65 * leak + noise)
            qual = clamp01(0.85 - 0.50 * op - 0.35 * leak - noise)
            complete = rng.random() > (0.05 + 0.25 * op)
            traces[edge] = GeneratedTrace(edge, anomaly, conf, qual, complete)
        return traces


class ConfoundLeakGenerator:
    """Red-team: leaks via a DEPTH CONFOUND, reading NEITHER the cause-signature
    NOR the key. Marks the deepest edge. In the suite the break is usually
    deepest, so depth correlates with the answer without ever touching it. Tests
    whether the key-decouple control is fooled by a break-location-invariant
    leak (it should be: depth survives key-decouple, because moving the KEY does
    not move depth -- which is exactly why a SECOND control, shuffle, is kept)."""
    def __init__(self, confound_strength=0.85, noise=0.08):
        self.confound_strength = confound_strength
        self.noise = noise

    def _deepest_edge(self, dag):
        parent_of = {n.node_id: n.parent_id for n in dag.nodes}
        def depth(nid):
            d, cur = 0, nid
            while parent_of[cur] is not None:
                d += 1; cur = parent_of[cur]
            return d
        return max(dag.edges(), key=lambda pc: depth(pc[1]))

    def traces_for(self, dag, rng, answer_key=None):
        traces = {}
        deepest = self._deepest_edge(dag)
        for edge in dag.edges():
            op = _opacity(dag.edge_facts[edge])
            leak = self.confound_strength if edge == deepest else 0.0
            noise = rng.uniform(-self.noise, self.noise)
            anomaly = clamp01(0.20 + 0.55 * op + 0.55 * leak + noise)
            conf = clamp01(0.15 + 0.45 * op + 0.65 * leak + noise)
            qual = clamp01(0.85 - 0.50 * op - 0.35 * leak - noise)
            complete = rng.random() > (0.05 + 0.25 * op)
            traces[edge] = GeneratedTrace(edge, anomaly, conf, qual, complete)
        return traces


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
    """v0.4 structure + generated traces. Reads evidence + traces only; never
    break_edge, never answer_key. Traces reweight blame among reconstructable
    edges; they do NOT make a dark edge reconstructable (undetermined still from
    structure)."""
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
    """Score blame against an EXPLICIT target edge. v0.7 always scores against
    the TRUE cause (break_edge); the target is passed explicitly so the reader
    can see that the scoring label never moves under key-decouple."""
    correct = res.edge_blame.get(target_edge, 0.0) if target_edge else 0.0
    wrong = sum(v for e, v in res.edge_blame.items() if e != target_edge)
    return correct, wrong, res.undetermined

def score_base(dag, sib):
    nodes, edges = redact(dag)
    s = score(attribute(nodes, edges, dag.final_loss, sib), dag)
    return s["correct"], s["wrong"], s["undet"]


def random_other_edge(dag, rng):
    """An out-of-band answer key pointing at some edge OTHER than the true cause."""
    others = [e for e in dag.edges() if e != dag.break_edge]
    return rng.choice(others) if others else dag.break_edge

def copy_with_moved_cause(dag, rng):
    """Counterfactual WORLD move: relocate the actual break. This regenerates the
    world from a different cause. It is NOT a decoupling test -- it changes the
    cause itself -- and is reported as a separate diagnostic only."""
    import copy as _copy
    d = _copy.deepcopy(dag)
    d.break_edge = rng.choice(d.edges())
    return d

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
#
# Four conditions per trial. EVERY condition scores against the TRUE cause
# (dag.break_edge). Each condition moves AT MOST ONE thing relative to "gen":
#   gen          : honest world, honest key (== cause).            [baseline run]
#   key_decouple : honest world, key MOVED off the cause.         [ONLY the key moves]
#   shuffle      : honest world+key, trace->edge assignment shuffled. [only the map moves]
#   world_move   : cause RELOCATED, world regenerated.            [counterfactual; not a verdict input]
# =========================================================================== #

def eval_generator(gen, trials=250, seed=42, tw=1.25):
    rng = random.Random(seed)
    keys = ("base", "gen", "key_decouple", "shuffle", "world_move")
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

            # honest run: key == cause
            tr = gen.traces_for(dag, rng, answer_key=cause)
            g = attribute_with_generated_traces(nodes, edges, dag.final_loss, tr, sib, tw)

            # KEY-DECOUPLE: move ONLY the out-of-band key; world + label stay on cause
            okey = random_other_edge(dag, rng)
            tr_kd = gen.traces_for(dag, rng, answer_key=okey)
            g_kd = attribute_with_generated_traces(nodes, edges, dag.final_loss, tr_kd, sib, tw)

            # SHUFFLE: same honest traces, permute trace->edge assignment
            g_sh = attribute_with_generated_traces(nodes, edges, dag.final_loss,
                                                   shuffled_traces(tr, rng), sib, tw)

            # WORLD-MOVE (counterfactual): relocate the cause, regenerate world,
            # score against the NEW cause. Diagnostic only.
            wm = copy_with_moved_cause(dag, rng)
            tr_wm = gen.traces_for(wm, rng, answer_key=wm.break_edge)
            g_wm = attribute_with_generated_traces(nodes, edges, wm.final_loss, tr_wm, sib, tw)

            rows = (("base", b),
                    ("gen", score_g_vs(g, cause)),
                    ("key_decouple", score_g_vs(g_kd, cause)),
                    ("shuffle", score_g_vs(g_sh, cause)),
                    ("world_move", score_g_vs(g_wm, wm.break_edge)))
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
    kd_drop = st["gen"][0] - st["key_decouple"][0]
    sh_drop = st["gen"][0] - st["shuffle"][0]
    wm_drop = st["gen"][0] - st["world_move"][0]
    print(f"{label}:")
    print(f"  generated lift over baseline            : {lift:+.3f}")
    print(f"  drop, KEY-DECOUPLE (verdict)            : {kd_drop:+.3f}")
    print(f"  drop, trace SHUFFLE (verdict)           : {sh_drop:+.3f}")
    print(f"  drop, WORLD-MOVE (counterfactual, unused): {wm_drop:+.3f}")
    return lift, kd_drop, sh_drop


def verdict(lift, kd_drop, sh_drop, eps=0.02):
    if lift <= eps:
        return "NO LIFT. Generated layer adds no attribution power; report v0.4 only."
    if kd_drop > eps:
        return ("SUSPECT (answer-key). Lift COLLAPSES when the out-of-band key is "
                "decoupled from the cause -> the generator was reading the key, not "
                "the world. Do not trust the generated run.")
    if sh_drop <= eps:
        return ("SUSPECT (shuffle). Lift survives trace-shuffle -> distributional "
                "artefact, not edge-specific evidence.")
    return ("PASS AS INSTRUMENT TEST (not a world claim). Lift SURVIVES key-decouple "
            "(reads the world, not the key) AND collapses under shuffle (edge-specific). "
            "Necessary, not sufficient, for a real-model run.")


def main():
    _startup_banner()
    print()
    print("Each condition scores against the TRUE cause and moves at most one variable")
    print("relative to 'gen'. KEY-DECOUPLE moves ONLY the out-of-band answer key.")
    print()

    print("RUN A: CLEAN generator (reads neither the cause-signature nor the key)")
    _, eA = eval_generator(CleanGenerator())
    lA, kA, sA = read("  discriminating subset", eA)
    print("  ->", verdict(lA, kA, sA), "\n")

    print("RUN B: LEAKY generator (reads the out-of-band ANSWER KEY)")
    _, eB = eval_generator(LeakyGenerator(0.85))
    lB, kB, sB = read("  discriminating subset", eB)
    print("  ->", verdict(lB, kB, sB), "\n")

    print("RUN C: LEGIT CAUSAL generator (reads an opacity-gated observation of the")
    print("       cause in the WORLD; never the key) -- the trustworthy generator")
    print("       v0.6 could not express. It must PASS.")
    _, eC = eval_generator(LegitCausalGenerator(0.85))
    lC, kC, sC = read("  discriminating subset", eC)
    print("  ->", verdict(lC, kC, sC), "\n")

    print("RUN D: CONFOUND generator (depth leak; reads neither cause nor key) --")
    print("       red-team of the key-decouple control.")
    _, eD = eval_generator(ConfoundLeakGenerator(0.85))
    lD, kD, sD = read("  discriminating subset", eD)
    print("  ->", verdict(lD, kD, sD))
    print()
    print("CONFOUND RED-TEAM READ (shuffle FLAGS when its drop <= 0.02; key-decouple")
    print("FLAGS when its drop > 0.02):")
    if lD <= 0.02:
        print("  Confound produced no lift here; attack under-powered on this suite.")
    elif kD > 0.02:
        print("  KEY-DECOUPLE flags the confound -- depth happened to co-move with the")
        print("  out-of-band key on this suite. Honest but suite-dependent; do not claim")
        print("  the control generalises from this.")
    elif sD <= 0.02:
        print("  KEY-DECOUPLE is fooled (moving the key does not move the depth mark) but")
        print("  trace-SHUFFLE flags it (lift survives shuffle -> distributional artefact).")
        print("  This is WHY two controls are kept: each probes a different leak route.")
    else:
        print("  BOTH controls PASS the confound -- and this is the uncomfortable, honest")
        print("  result. On this pre-registered suite the break is (almost) always the")
        print("  DEEPEST edge, so 'mark the deepest edge' IS marking the cause: the depth")
        print("  confound is observationally a LEGITIMATE causal generator. Key-decouple")
        print("  can't see it (it never read the key); shuffle can't see it (the mark is")
        print("  genuinely edge-specific, on the right edge). Neither control is wrong --")
        print("  the SUITE is, by coupling depth to cause. Breaking that correlation in the")
        print("  pre-registered distribution (residual #3) is the only thing that turns")
        print("  this leak back into a detectable one. Until then: do NOT claim the controls")
        print("  generalise past edge-local and answer-key leaks.")

    print("\nRESIDUALS (unchanged, handed to the next reviewer):")
    print("  1. A confidence-laundering leak that sharpens the blame distribution WITHOUT")
    print("     improving accuracy shows zero lift and passes silently. The lift-based")
    print("     metric cannot see it. Build it against a fresh model before trusting any")
    print("     real-generator run for decision-making.")
    print("  2. The 0.02 cutoffs are stipulated, not derived, and scale with trace_weight.")
    print("     The margins above are printed so the dependence is visible, not justified.")
    print("  3. The suite couples DEPTH to CAUSE (the break is almost always deepest), so a")
    print("     depth confound is indistinguishable from legitimate causal observation here")
    print("     (see RUN D). Decorrelating depth and cause in the pre-registered distribution")
    print("     is required before claiming the controls catch structural confounds.")


if __name__ == "__main__":
    main()
