"""
generated_leak_harness_v06_selfcontained.py
===========================================
SELF-CONTAINED, HASH-PINNED leak harness. Single file, runs anywhere with a
standard Python 3.10+ interpreter. No external project files required.

WHY THIS VERSION EXISTS (two defects in v0.5_fixed, both conceded):
  1. PACKAGING: v0.5 imported dag_attribution_v04 at load time. Uploaded alone it
     died at import -- a dependent fragment, not a runnable artifact. A harness
     meant to be checked by other reviewers must run in THEIR sandbox.
  2. SUBSTRATE SUBSTITUTION: every verdict is computed by the v0.4 functions. With
     the dependency named only as "a file in the same directory," two reviewers
     could run "the same harness" against different (or tampered) substrates and
     both get honest-but-incomparable numbers. The instrument was air-gapped
     against TRACE leaks and wide open to SUBSTRATE swaps.

THE FIX:
  - The v0.4 substrate is VENDORED INLINE below, between SUBSTRATE BEGIN/END
    sentinels, copied byte-for-byte from the audited dag_attribution_v04.py
    (sha256 of the original standalone file recorded as _ORIGINAL_V04_SHA256).
  - At startup the harness HASHES ITS OWN SUBSTRATE BLOCK and compares it to a
    pinned value (_SUBSTRATE_PIN). If the substrate was edited, the hash diverges
    and the harness REFUSES TO RUN -- no verdict is produced on an unknown
    substrate. Tampering is loud, not silent.
  - The runtime banner prints both hashes so any verdict is reproducible: a
    reviewer knows exactly which substrate produced which number.

DISCIPLINE PRESERVED FROM EARLIER VERSIONS:
  one mechanism, one falsification, one honest read; air gap intact (the
  attributor reads evidence only; no break_edge/cause crosses redact()); broken
  baseline kept VISIBLE next to the fixed one as a documented trap; the confound
  red-team of the fixed baseline is included as a runnable self-attack.

VERDICT LOGIC (corrected across two prior rounds):
  A generated trace layer is trustworthy only if its accuracy lift over the v0.4
  baseline COLLAPSES under re-randomization (re-point the break, regenerate
  traces, re-run, score vs the new break) AND under trace-shuffle. If the lift
  survives EITHER decoupling, the signal is answer-key-coupled -> SUSPECT.
  (The broken baseline -- fixed attribution vs a random label -- is shown but
  NOT used for the verdict; it is the trap that fooled two models.)

Run:  python generated_leak_harness_v06_selfcontained.py
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
    print("SELF-CONTAINED LEAK HARNESS v0.6")
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


class SimulatedLocalTraceGenerator:
    """leak_strength 0 -> structural facts + noise only; >0 -> mark the TRUE break
    edge (edge-local leak)."""
    def __init__(self, leak_strength=0.0, noise=0.08):
        self.leak_strength = leak_strength
        self.noise = noise

    def traces_for(self, dag, rng):
        traces = {}
        for edge in dag.edges():
            facts = dag.edge_facts[edge]
            opacity = (0.45 * facts.transform_loss
                       + 0.30 * (0.0 if facts.validation_present else 1.0)
                       + 0.25 * (0.0 if facts.replayable else 1.0))
            noise = rng.uniform(-self.noise, self.noise)
            leak = self.leak_strength if edge == dag.break_edge else 0.0
            anomaly = clamp01(0.20 + 0.55 * opacity + 0.55 * leak + noise)
            conf = clamp01(0.15 + 0.45 * opacity + 0.65 * leak + noise)
            qual = clamp01(0.85 - 0.50 * opacity - 0.35 * leak - noise)
            complete = rng.random() > (0.05 + 0.25 * opacity)
            traces[edge] = GeneratedTrace(edge, anomaly, conf, qual, complete)
        return traces


class ConfoundLeakGenerator(SimulatedLocalTraceGenerator):
    """Red-team generator: leaks via a DEPTH CONFOUND, never reading break_edge.
    Marks the deepest edge. In the suite the break is always deepest, so depth is
    correlated with the answer WITHOUT a direct copy. Tests whether the fixed
    baseline is fooled by a break-location-invariant leak."""
    def __init__(self, leak_strength=0.85, noise=0.08):
        super().__init__(leak_strength=0.0, noise=noise)
        self.confound_strength = leak_strength

    def _deepest_edge(self, dag):
        parent_of = {n.node_id: n.parent_id for n in dag.nodes}
        def depth(nid):
            d, cur = 0, nid
            while parent_of[cur] is not None:
                d += 1; cur = parent_of[cur]
            return d
        return max(dag.edges(), key=lambda pc: depth(pc[1]))

    def traces_for(self, dag, rng):
        traces = {}
        deepest = self._deepest_edge(dag)
        for edge in dag.edges():
            facts = dag.edge_facts[edge]
            opacity = (0.45 * facts.transform_loss
                       + 0.30 * (0.0 if facts.validation_present else 1.0)
                       + 0.25 * (0.0 if facts.replayable else 1.0))
            noise = rng.uniform(-self.noise, self.noise)
            leak = self.confound_strength if edge == deepest else 0.0
            anomaly = clamp01(0.20 + 0.55 * opacity + 0.55 * leak + noise)
            conf = clamp01(0.15 + 0.45 * opacity + 0.65 * leak + noise)
            qual = clamp01(0.85 - 0.50 * opacity - 0.35 * leak - noise)
            complete = rng.random() > (0.05 + 0.25 * opacity)
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
    break_edge. Traces reweight blame among reconstructable edges; they do NOT
    make a dark edge reconstructable (undetermined still from structure)."""
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


def score_g(res, dag):
    correct = res.edge_blame.get(dag.break_edge, 0.0) if dag.break_edge else 0.0
    wrong = sum(v for e, v in res.edge_blame.items() if e != dag.break_edge)
    return correct, wrong, res.undetermined

def score_base(dag, sib):
    nodes, edges = redact(dag)
    s = score(attribute(nodes, edges, dag.final_loss, sib), dag)
    return s["correct"], s["wrong"], s["undet"]


def copy_with_randomized_break(dag, rng):
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

def eval_generator(gen, trials=250, seed=42, tw=1.25):
    rng = random.Random(seed)
    agg = {k: [0.0, 0.0, 0.0] for k in ("base", "gen", "rr_broken", "rr_fixed", "shuf")}
    elig = {k: [0.0, 0.0, 0.0] for k in agg}
    n_all = 0; n_elig = 0
    for label, dag, sib in suite():
        nodes, edges = redact(dag)
        b = score_base(dag, sib)
        is_elig = b[0] > 0.0 and b[1] > 0.0
        cell = {k: [0.0, 0.0, 0.0] for k in agg}
        for _ in range(trials):
            traces = gen.traces_for(dag, rng)
            g = attribute_with_generated_traces(nodes, edges, dag.final_loss, traces, sib, tw)
            rr_dag = copy_with_randomized_break(dag, rng)
            rr_broken = g  # broken: same output vs new label
            rr_fixed = attribute_with_generated_traces(nodes, edges, rr_dag.final_loss,
                                                       gen.traces_for(rr_dag, rng), sib, tw)
            sh = attribute_with_generated_traces(nodes, edges, dag.final_loss,
                                                 shuffled_traces(traces, rng), sib, tw)
            rows = (("base", b), ("gen", score_g(g, dag)),
                    ("rr_broken", score_g(rr_broken, rr_dag)),
                    ("rr_fixed", score_g(rr_fixed, rr_dag)),
                    ("shuf", score_g(sh, dag)))
            for k, t in rows:
                for i in range(3):
                    cell[k][i] += t[i] / trials
        n_all += 1
        for k in agg:
            for i in range(3):
                agg[k][i] += cell[k][i]
        if is_elig:
            n_elig += 1
            for k in elig:
                for i in range(3):
                    elig[k][i] += cell[k][i]
    for k in agg:
        for i in range(3):
            agg[k][i] /= max(1, n_all)
            elig[k][i] /= max(1, n_elig)
    return agg, elig


def read(label, st):
    lift = st["gen"][0] - st["base"][0]
    broken = st["gen"][0] - st["rr_broken"][0]
    fixed = st["gen"][0] - st["rr_fixed"][0]
    shuf = st["gen"][0] - st["shuf"][0]
    print(f"{label}:")
    print(f"  generated lift over baseline       : {lift:+.3f}")
    print(f"  drop, re-rand BROKEN (trap, unused): {broken:+.3f}")
    print(f"  drop, re-rand FIXED                : {fixed:+.3f}")
    print(f"  drop, trace shuffle                : {shuf:+.3f}")
    return lift, fixed, shuf


def verdict(lift, fixed, shuf):
    if lift <= 0.02:
        return "NO LIFT. Generated layer adds no attribution power; report v0.4 only."
    if fixed <= 0.02:
        return ("SUSPECT (re-rand). Lift survives FIXED re-randomization -> the signal "
                "is answer-key-coupled. Do not trust the generated run.")
    if shuf <= 0.02:
        return ("SUSPECT (shuffle). Lift survives trace-shuffle -> distributional "
                "artefact, not edge-specific causal evidence.")
    return ("PASS AS INSTRUMENT TEST (not a world claim). Lift collapses under BOTH "
            "decouplings. Necessary, not sufficient, for a real-model run.")


def main():
    _startup_banner()
    print()
    print("RUN A: CLEAN generator (traces from structure + noise, break-independent)")
    aA, eA = eval_generator(SimulatedLocalTraceGenerator(0.0))
    _, fA, sA = read("  discriminating subset", eA)
    print("  ->", verdict(eA["gen"][0]-eA["base"][0], fA, sA), "\n")

    print("RUN B: LEAKY generator (edge-local: marks the true break edge)")
    aB, eB = eval_generator(SimulatedLocalTraceGenerator(0.85))
    lB, fB, sB = read("  discriminating subset", eB)
    print("  ->", verdict(lB, fB, sB), "\n")

    print("RUN C: CONFOUND generator (depth leak, never reads break_edge -- red-team")
    print("       of the FIXED baseline: is it fooled by a break-location-invariant leak?)")
    aC, eC = eval_generator(ConfoundLeakGenerator(0.85))
    lC, fC, sC = read("  discriminating subset", eC)
    print("  ->", verdict(lC, fC, sC))
    print()
    print("CONFOUND RED-TEAM READ:")
    if lC > 0.02 and fC > 0.02:
        print("  The FIXED re-randomization baseline CATCHES the confound leak (fixed-drop")
        print("  > 0): re-pointing the break leaves the depth-mark stranded, so accuracy")
        print("  collapses. The fixed baseline generalises beyond edge-local leaks.")
    elif lC > 0.02 and fC <= 0.02 and sC > 0.02:
        print("  The FIXED baseline is FOOLED (fixed-drop ~0) but trace-shuffle catches it.")
        print("  Require BOTH baselines; fixed re-rand alone is insufficient.")
    elif lC > 0.02:
        print("  BOTH baselines fooled by the confound. A third control is required.")
    else:
        print("  Confound produced no lift here; attack under-powered on this suite.")

    print("\nRESIDUAL (neither baseline addresses, handed to the next reviewer):")
    print("  A confidence-laundering leak that sharpens the blame distribution WITHOUT")
    print("  improving accuracy would show zero lift and pass silently. The lift-based")
    print("  harness cannot see it. Build it against a fresh model before trusting any")
    print("  real-generator run for decision-making.")


if __name__ == "__main__":
    main()
