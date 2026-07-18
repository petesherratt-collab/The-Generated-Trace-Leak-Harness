# Experiment diagrams — how the CCC study is designed

Flow diagrams of the *experimental method* (companion to [`PIPELINE_DIAGRAMS.md`](PIPELINE_DIAGRAMS.md),
which shows the judging architecture). GitHub renders these natively. Full numbers and
preregistrations are linked from [`../RESEARCH_NARRATIVE.md`](../RESEARCH_NARRATIVE.md).

## 1 — The investigation arc: what each experiment established

Each step was run to answer a question the previous step raised. The dark nodes are the two
load-bearing conclusions.

```mermaid
flowchart TD
    LH["Generated-trace leak harness<br/>(blind mirrored controls)"] --> PIVOT{"Pivot: is the judge grounded<br/>in the work, or in the answer key?"}
    PIVOT --> A1["Arithmetic pilot:<br/>a poisoned reference collapses discrimination"]
    A1 --> A2["2x2 factorial (verify x show-work):<br/>only the combination fixes it -- fragile"]
    A2 --> A3["Sensitivity matrix + transcript autopsy:<br/>prompt fix is model/wording-specific;<br/>correct working, wrong score"]
    A3 --> M1["Provenance x content factorial"]
    M1 --> M2["Preregistered confirmation:<br/>authority label adds nothing;<br/>bare answer = full rationale"]
    M2 --> CCC{{"Active ingredient isolated:<br/>the conflicting CONCLUSION itself<br/>= Contextual Conclusion Capture"}}
    CCC --> ARCH["Causal architecture test (numeric):<br/>isolation / router / verification<br/>under mirrored references"]
    ARCH --> CODE["Domain replication: CODE<br/>(unit-test gold), Stage 1 -> Stage 2"]
    ARCH --> SQL["Domain replication: SQL<br/>(SQLite oracle), Stage 1 -> Stage 2"]
    CODE --> SYN["Cross-domain synthesis"]
    SQL --> SYN
    SYN --> CONC{{"Capture is model- & domain-dependent;<br/>context isolation is the only<br/>structural safeguard"}}

    classDef dark fill:#1F8A70,stroke:#14614E,color:#FFFFFF;
    class CCC,CONC dark;
```

## 2 — The atomic measurement: one judging cell → harm

Every data point is a judge score. Discrimination compares a correct vs a matched wrong
candidate; harm is how much an injected conclusion erodes it.

```mermaid
flowchart LR
    T["Task<br/>(mechanical gold)"] --> J
    CC["Correct candidate<br/>(from oracle)"] --> J
    CW["Wrong candidate<br/>(oracle; named error)"] --> J
    COND["Condition<br/>content x label:<br/>none / bare / rationale / solver"] --> J
    PROT["Protocol:<br/>score_only | verify_written"] --> J
    J{{"LLM judge -> score 0-100"}} --> D["Discrimination<br/>D = mean s(correct) - mean s(wrong)"]
    D --> H["Harm = D(no injection) - D(injection)<br/>Susceptibility = D(correct ref) - D(wrong ref)"]

    classDef dark fill:#1F8A70,stroke:#14614E,color:#FFFFFF;
    class H dark;
```

## 3 — The two-stage design (run once per domain)

Stage 1 measures whether capture happens; a frozen threshold decides which models proceed;
Stage 2 tests the safeguards only on the captured subset.

```mermaid
flowchart TD
    subgraph S1["STAGE 1 - injection"]
        G1["items x 5 models x 4 conditions<br/>x 2 candidates x 2 protocols x 3 reps"]
        P1["PRIMARY: bare-conclusion harm (score_only)<br/>item-clustered bootstrap CI, fail-closed"]
        G1 --> P1
    end
    P1 --> TH{"Capture threshold:<br/>supported (CI>0, >= completeness floor)<br/>AND estimate >= +10 ?"}
    TH -- "no" --> EXC["excluded / non-capture<br/>(reported, never called 'safe')"]
    TH -- "yes" --> ADM["admitted -> frozen Stage-2 subset"]
    ADM --> S2
    subgraph S2["STAGE 2 - architectures (conditional)"]
        G2["admitted models x 4 architectures<br/>x 2 mirrored references x 2 candidates x 3 reps<br/>(+ router solves)"]
        O2["susceptibility · isolation gain · router gain ·<br/>router detection · verification RESIDUAL"]
        G2 --> O2
    end

    classDef dark fill:#1F8A70,stroke:#14614E,color:#FFFFFF;
    class O2 dark;
```

## 4 — Mechanism isolation: the provenance × content factorial

The contrasts that falsify the two intuitive explanations and leave only the conclusion.

```mermaid
flowchart TD
    B["Baseline: no injection"] --> AO["neutral / answer_only<br/>(bare wrong result)"]
    AO -- "rationale increment (full - bare)" --> NR["neutral / full_wrong_rationale"]
    NR -- "provenance increment (solver - neutral)" --> SR["solver / full_wrong_rationale"]
    AO --> R1{"bare answer already captures?<br/>YES => conclusion is sufficient"}
    NR --> R2{"rationale adds detectable capture?<br/>NO => persuasion not necessary"}
    SR --> R3{"authority label adds detectable capture?<br/>NO => authority not necessary"}
    R1 --> CONC{{"CCC: the conflicting conclusion itself"}}
    R2 --> CONC
    R3 --> CONC

    classDef dark fill:#1F8A70,stroke:#14614E,color:#FFFFFF;
    class CONC dark;
```

## 5 — The four architectures under mirrored references (Stage 2)

Each cell is run with a correct and a wrong external reference. Only isolation removes the
reference from the judge's context by construction; the router decides mechanically.

```mermaid
flowchart TD
    R[("External reference<br/>correct | wrong (mirrored)")]
    C["Candidate"]
    R --> A1["contaminated_score_only<br/>reference in prompt -> score"]
    R --> A2["contaminated_verify_written<br/>reference in prompt -> re-derive -> score"]
    R -. "never in prompt<br/>(byte-identical, audited)" .-> A3["context_isolated_score_only<br/>reference only in pipeline metadata"]
    R --> A4
    C --> A1
    C --> A2
    C --> A3
    C --> A4
    subgraph A4["conflict_router"]
        SOLVE["fresh spec-only solve<br/>(separate context)"] --> CMP{"mechanical compare<br/>solve vs reference<br/>(frozen canonicalizer)"}
        CMP -- "agree" --> EXP["exposed score-only path"]
        CMP -- "disagree / unparseable" --> QUAR["quarantine + fresh verify-written<br/>judge (never sees reference)"]
    end

    classDef quar fill:#BC4B33,stroke:#8F3323,color:#FFFFFF;
    classDef iso fill:#1F8A70,stroke:#14614E,color:#FFFFFF;
    class R quar;
    class A3 iso;
```

*Result across all three domains: isolation (structural, byte-audited) ≥ router (where mechanical
comparison is clean) ≫ written verification (partial everywhere). See the per-domain findings.*
