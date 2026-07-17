# Judge pipeline — with and without the harness

Two flow diagrams for explaining the architecture. GitHub renders these natively.

The single load-bearing difference: **both pipelines have client-side orchestration code**
doing the mechanical work (load data, collect the candidate, build the prompt, parse the
score, aggregate). Without the harness that code is a **passive courier** — it pastes the
reference answer into the judge's prompt and lets the model reconcile any conflict silently.
With the harness it is a **gatekeeper** — the reference never enters any model prompt; the
comparison is done in deterministic code, and disagreement is routed instead of absorbed.

## 1 — Without the harness (the typical LLM-as-judge setup)

The "steps before the LLM" are the benchmark's own eval script (or a product backend):
it loads the dataset (questions + answer key), runs the model under test to get the
candidate, fills one prompt template with all three, calls the judge, parses, aggregates.
Nothing checks what information crosses into the judge's context.

```mermaid
flowchart TD
    subgraph CS1["CLIENT SIDE - the benchmark's own eval script"]
        DS[("Dataset:<br/>questions + answer key")]
        C["Candidate answer"]
        T["Prompt template:<br/>question + candidate + REFERENCE<br/>pasted into one prompt"]
        PARSE["Parse score"]
        AGG["Aggregate scores"]
        LB["Leaderboard / verdict"]
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
    J --> PARSE --> AGG --> LB
    J -.-> X["If the key is wrong, the score follows it.<br/>The conflict is reconciled silently inside<br/>the model - no trace is left."]

    classDef neutral fill:#E9EEF3,stroke:#9FB0BE,color:#1C2733;
    classDef bad fill:#BC4B33,stroke:#8F3323,color:#FFFFFF;
    classDef warn fill:#F7E9E5,stroke:#BC4B33,color:#7A2F1D;
    class C,T,PARSE,AGG,LB,MUT,J neutral;
    class DS bad;
    class X warn;
    style CS1 fill:none,stroke:#9FB0BE,stroke-dasharray:4 3;
    style MS1 fill:none,stroke:#9FB0BE,stroke-dasharray:4 3;
```

**Measured:** a conflicting conclusion in the judge's context cost score-only judges
**39–88 points of discrimination** between correct and wrong candidates — with no authority
label and no supporting argument needed (the bare wrong conclusion sufficed). "Verify it
yourself first" instructions reduced the damage but did not eliminate it for every model.
See [`../experiments/results/FINDINGS_contextual_conclusion_capture_confirmatory.md`](../experiments/results/FINDINGS_contextual_conclusion_capture_confirmatory.md).

## 2 — With the harness (isolate, compare, route)

Same client-side machinery — but now it decides what crosses the line. The reference stays
quarantined in pipeline metadata; the judge and the independent solver each get a minimal,
fresh context; the comparison is code, not a model; disagreement is exposed and routed.

```mermaid
flowchart TD
    subgraph CS2["CLIENT SIDE - the harness (deterministic code)"]
        Q["Question / task"]
        C2["Candidate answer"]
        R[("Reference answer<br/>QUARANTINED in metadata")]
        BS["Blind score"]
        IC["Independent conclusion"]
        CMP{"Mechanical comparison<br/>(harness code, no model)"}
        OK["Accept the blind score"]
        FLAG["Route to review:<br/>deterministic check /<br/>second solve / human"]
    end
    subgraph MS2["MODEL SIDE - stateless calls"]
        J2{{"Blind judge<br/>sees question + candidate ONLY"}}
        SOL{{"Independent solver<br/>sees question ONLY"}}
    end
    Q --> J2
    C2 --> J2
    J2 --> BS
    Q --> SOL
    SOL --> IC
    IC --> CMP
    R -. "never enters any model prompt" .-> CMP
    CMP -- "agree" --> OK
    CMP -- "disagree" --> FLAG
    BS --> OK

    classDef neutral fill:#E9EEF3,stroke:#9FB0BE,color:#1C2733;
    classDef good fill:#1F8A70,stroke:#14614E,color:#FFFFFF;
    classDef quarantine fill:#BC4B33,stroke:#8F3323,color:#FFFFFF;
    class Q,C2,BS,IC,J2,SOL neutral;
    class CMP,OK,FLAG good;
    class R quarantine;
    style CS2 fill:none,stroke:#1F8A70,stroke-dasharray:4 3;
    style MS2 fill:none,stroke:#9FB0BE,stroke-dasharray:4 3;
```

**Measured:** context isolation was the most consistent safeguard tested and passes a
byte-level audit — **480 of 480** judge prompts were hash-identical whether the reference was
right or wrong, so the reference *provably* never reaches the judge. See
[`../experiments/results/FINDINGS_contextual_capture_architecture.md`](../experiments/results/FINDINGS_contextual_capture_architecture.md).

## Who does what

| | Model side | Client side |
|---|---|---|
| **Role** | Emit a 0–100 score from the prompt it is given — nothing else | Everything that determines what the evaluation *concludes* |
| **State** | Stateless; no memory between calls | Streams every attempt to auditable JSONL evidence |
| **Ground truth** | Never asked "is this right?" | Computed mechanically (unit tests / code-verified gold) |
| **Comparison / routing** | Never adjudicates its own disagreement | Deterministic compare; conflicts exposed and routed |
| **The difference between the two pipelines** | — | Courier (hands the key to the judge) vs. gatekeeper (withholds it) |

If the gold or the routing were model-side, you would be grading a judge with a judge —
the circularity the design exists to avoid.

**Scope:** validated on 16 numeric items across five models (preregistered, item-clustered
CIs); a code-domain replication is frozen and pending. No claim is made about any named
benchmark — that requires reproducing its real prompt, reference visibility, and routing.
Full arc: [`../RESEARCH_NARRATIVE.md`](../RESEARCH_NARRATIVE.md).
