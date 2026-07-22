# CCC MiniMax M3 full run v2

Status: **complete, preregistered full inferential arm**

MiniMax M3 shows Contextual Conclusion Capture in all three tested domains under
the frozen terse-score protocol. The run is unusually clean: all 1,344 cells
completed on the first judge and transport attempt, the endpoint stayed on
MiniMax first party, and observed reasoning use was exactly zero.

## Primary results

| Domain | Bare-conclusion harm | 95% CI | Items | Verdict | Provenance increment | Rationale increment |
|---|---:|---:|---:|---|---:|---:|
| Arithmetic | **+75.17** | **[+48.71, +101.83]** | 16 | **SUPPORTED** | -14.6 | -15.5 |
| Code | **+19.65** | **[+9.44, +30.25]** | 16 | **SUPPORTED** | +19.5 | -1.1 |
| SQL | **+143.68** | **[+126.44, +160.89]** | 24 | **SUPPORTED** | +4.4 | +0.2 |

SQL is the strongest effect, continuing the cross-model pattern that SQL judging
is highly capture-prone. MiniMax is also distinct from most frontier and open-
weight comparators because its arithmetic and code effects are both confirmatory.

The mechanism differs by domain. Code has a positive provenance increment of
+19.5 points, whereas the very large arithmetic and SQL bare-conclusion effects
do not become larger when provenance or a rationale is added. The conclusion
itself is therefore sufficient to drive the primary MiniMax effects; extra
source-like framing is not required.

## Completeness and endpoint integrity

- Scheduled and successful cells: 1,344/1,344
- Unique cells: 1,344; duplicates: 0
- Final failures, judge retries, and transport retries: 0
- Exact one-field JSON and `finish_reason=stop`: 1,344/1,344
- Resolved identity: `minimax/minimax-m3` / Minimax on every response
- Prompt records: 448; every SHA-256 verified and every reference resolved
- Completion, truncation, and content-filter balance gaps: 0.0% in every domain
- Reasoning telemetry: 1,344/1,344 records, all zero tokens

## Cost

| Domain | Cells | Scored cost |
|---|---:|---:|
| Arithmetic | 384 | $0.02600292 |
| Code | 384 | $0.02092848 |
| SQL | 576 | $0.03560220 |
| **Total scored cells** | **1,344** | **$0.08253360** |

Including the run-internal and separate launch preflights, the full-run-path total
was **$0.08259708**. MiniMax therefore supplied a complete three-domain
confirmatory arm for roughly eight pence in dollar-denominated OpenRouter spend.

## Interpretation boundary

This finding applies to the frozen score-only contract: reasoning disabled and
excluded, 128/256 output ceilings, structured one-field JSON, and first-party
MiniMax routing. It can be compared directly with the other terse-score arms, but
not pooled as though it used Kimi's separate native-reasoning protocol.

Within that boundary, MiniMax is the clearest broad-domain capture case in the
open-weight extension so far. It strengthens the central SQL result and shows
that vulnerability can extend to arithmetic and code for some judges.
