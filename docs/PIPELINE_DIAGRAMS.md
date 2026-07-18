# Judge pipeline — contamination and the two safeguards

Flow diagrams for explaining the judging architecture. GitHub renders these natively.
The two safeguards are shown **separately** because they are different mechanisms: context
isolation *removes* the reference-to-judge pathway; the hybrid router *detects and routes*
around a conflict using a model-derived conclusion plus a deterministic comparison.

Both the contaminated and the safeguarded pipelines have the same client-side orchestration
(load data, collect the candidate, build the prompt, parse, aggregate). The difference is one
decision: whether that code pastes the reference into the judge's prompt (courier) or withholds
it (gatekeeper).

## 1 — Contaminated: reference pasted into the judge prompt

The "steps before the LLM" are the benchmark's own eval script (or a product backend): it loads
the dataset (questions + answer key), runs the model under test to get the candidate, fills one
prompt with all three, calls the judge, parses, aggregates. Nothing checks what crosses into the
judge's context.

```mermaid
flowchart TD
    subgraph CS1["CLIENT SIDE - the eval script"]
        DS[("Dataset:<br/>questions + answer key")]
        C["Candidate answer"]
        T["Prompt template:<br/>question + candidate + REFERENCE"]
        PARSE["Parse score"]
        LB["Aggregate -> leaderboard"]
    end
    subgraph MS1["MODEL SIDE - stateless calls"]
        MUT{{"Model under test"}}
        J{{"LLM judge"}}
    end
    DS -- "question" --> MUT
    MUT --> C
    DS -- "question" --> T
    C --> T
    DS -- "reference answer" --> T
    T --> J
    J --> PARSE --> LB
    J -.-> X["If the key is wrong, the score MAY follow it.<br/>Any reconciliation happens silently<br/>inside the model - no trace is left."]

    classDef neutral fill:#E9EEF3,stroke:#9FB0BE,color:#1C2733;
    classDef bad fill:#BC4B33,stroke:#8F3323,color:#FFFFFF;
    classDef warn fill:#F7E9E5,stroke:#BC4B33,color:#7A2F1D;
    class C,T,PARSE,LB,MUT,J neutral;
    class DS bad;
    class X warn;
    style CS1 fill:none,stroke:#9FB0BE,stroke-dasharray:4 3;
    style MS1 fill:none,stroke:#9FB0BE,stroke-dasharray:4 3;
```

**Measured:** a conflicting conclusion in the judge's context reduced score-only discrimination
between correct and wrong candidates — with no authority label and no supporting argument needed
(a bare wrong conclusion sufficed) — by +39 to +88 points (arithmetic), +12 to +44 (code), and
+106 to +153 (SQL, observed). "Verify first" instructions reduced but did not eliminate it in any
domain.

## 2 — Safeguard A: context isolation (structural)

The reference is never placed in the judge's prompt. It may still exist in pipeline metadata for
logging or an offline audit, but the scoring judge sees only the task and the candidate. Because
the judge prompt does not contain the reference, it is **byte-identical whether the reference is
correct or wrong** — so the reference-to-judge pathway is provably absent.

```mermaid
flowchart TD
    subgraph CS2["CLIENT SIDE - the harness"]
        Q["Question / task"]
        C2["Candidate answer"]
        R[("Reference<br/>held in metadata only")]
        S["Score"]
        LB2["Aggregate -> leaderboard"]
    end
    subgraph MS2["MODEL SIDE - stateless call"]
        J2{{"Isolated judge<br/>prompt = task + candidate ONLY"}}
    end
    Q --> J2
    C2 --> J2
    J2 --> S --> LB2
    R -. "audited: never enters THIS judge's prompt<br/>(prompt hash identical for correct vs wrong ref)" .-> J2

    classDef neutral fill:#E9EEF3,stroke:#9FB0BE,color:#1C2733;
    classDef iso fill:#1F8A70,stroke:#14614E,color:#FFFFFF;
    classDef quarantine fill:#BC4B33,stroke:#8F3323,color:#FFFFFF;
    class Q,C2,S,LB2 neutral;
    class J2 iso;
    class R quarantine;
    style CS2 fill:none,stroke:#1F8A70,stroke-dasharray:4 3;
    style MS2 fill:none,stroke:#9FB0BE,stroke-dasharray:4 3;
```

**Measured (structural):** across the three architecture experiments, every isolated judge prompt
was hash-identical across the correct/wrong reference variants — **480/480** (arithmetic),
**384/384** (code), **720/720** (SQL). This guarantees the pathway is absent; it does **not**
guarantee the judge is otherwise correct.

## 3 — Safeguard B: the hybrid conflict-router

A *separate*, complementary design. A model produces an independent conclusion by solving the task
in a fresh context; **deterministic code** then compares that conclusion to the external reference;
routing is mechanical *after* the comparison. The router therefore inherits the solver's fallibility
(unparseable solves fail-safe to quarantine). The tested router uses a **model-derived** conclusion;
a deterministic test-oracle variant (using the unit tests / SQLite oracle directly) is stronger but
untested here.

```mermaid
flowchart TD
    Q3["Question / task"] --> SOL{{"Independent solver<br/>(model, separate context)"}}
    SOL --> IC["Parsed conclusion"]
    R3[("External reference<br/>correct | wrong")] --> CMP
    IC --> CMP{"Deterministic compare<br/>(canonicalize, no model)"}
    CMP -- "agree" --> EXP{{"Exposed judge<br/>(reference in prompt) -> score"}}
    CMP -- "disagree / unparseable<br/>(fail-safe)" --> QJ{{"Fresh judge<br/>NO reference -> score"}}
    EXP --> V["Verdict"]
    QJ --> V

    classDef neutral fill:#E9EEF3,stroke:#9FB0BE,color:#1C2733;
    classDef good fill:#1F8A70,stroke:#14614E,color:#FFFFFF;
    classDef quarantine fill:#BC4B33,stroke:#8F3323,color:#FFFFFF;
    class Q3,IC,V,EXP neutral;
    class SOL,QJ good;
    class CMP good;
    class R3 quarantine;
```

**Measured:** the router detected wrong-vs-correct references at +60 to +100 percentage points and
recovered discrimination where the conclusion-comparison was clean (in SQL, on 334/360 parseable
solves; the rest quarantined). Recovery was partial in code and strong in SQL — safeguard efficacy
is domain-dependent.

## Who does what

| | Model side | Client side |
|---|---|---|
| **Role** | Emit a 0–100 score, and (in the router) an independent solve | Decide what enters each prompt; parse; compare; route; aggregate |
| **State** | Stateless; no memory between calls | Streams every attempt to auditable JSONL evidence |
| **The gold** | The judge *is* asked "is this right?" — but no model ever **establishes** the correctness label | Correctness is set by an executable oracle (arithmetic in code, unit tests, SQLite), never by a model |
| **Comparison / routing** | Never adjudicates its own disagreement | Deterministic compare; conflicts routed or the pathway removed |

If the *gold* or the *routing decision* were set by a model, you would be measuring a judge with a
judge — the circularity the design avoids. (The router does use a model to *solve*, but the
compare-and-route step is deterministic.)

**Scope:** replicated across three domains with executable correctness oracles — arithmetic
(16 items), code (16 items, unit-test gold), and SQL (24 items, SQLite) — all preregistered with
item-clustered CIs. Isolation is byte-audited in all three (480/480, 384/384, 720/720). Capture and
safeguard efficacy are model- and domain-dependent; domain was observed, not randomized, so
magnitude differences are not attributed causally to domain. No claim is made about any named
benchmark — that requires reproducing its real prompt, reference visibility, ordering, and routing.
Full arc: [`../RESEARCH_NARRATIVE.md`](../RESEARCH_NARRATIVE.md); paper:
[`../paper/contextual_conclusion_capture.md`](../paper/contextual_conclusion_capture.md).
