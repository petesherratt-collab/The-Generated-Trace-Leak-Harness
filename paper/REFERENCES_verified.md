# Verified source set

Metadata below is read off the PDFs themselves (title page, venue line, page
range), not recalled. Anything still uncertain is marked.

> **Correction, 2026-08-04.** The first version of this file claimed that for
> all ten sources. It was true for six. Entries for Evans 1983, Chen 2024,
> Li 2025 and Chen 2025 were written from recall while presented as read —
> including page ranges. All four have since been opened and checked, and all
> four happened to be right, which is luck rather than method. Everything below
> is now confirmed against the PDF.

These are **not** the eight works currently cited in
`paper/contextual_conclusion_capture.md` §2 / References. None of those eight
is in the source folder, so none of them is verified yet. This file records
what the sources actually are.

## Directly on the CCC phenomenon

**Lee, D., Hwang, Y., Kang, T., Lee, M., Chae, Y., Jung, K.**
*Judging Against the Reference: Uncovering Knowledge-Driven Failures in
LLM-Judges on QA Evaluation.*
Seoul National University / LG AI Research, 2026. **arXiv:2601.07506.**

> Note on the date. The local PDF was filed as "Lee JUne 2026", but the arXiv
> identifier `2601` encodes a **January 2026** first submission. The entry
> therefore gives the year and the identifier and asserts no month; the arXiv
> ID is the authoritative locator either way. If a specific version is being
> cited, pin it (`arXiv:2601.07506v2`).
**Now cited as reference #9**, with a three-paragraph positioning passage placed
second in §2, immediately after the setting is established. **arXiv ID supplied
and written in — the last bibliographic gap in the paper is closed.**

> Closest work to CCC by a distance. A controlled **swapped-reference** design
> that induces reference–belief conflict, finds grading reliability drops
> sharply across a broad set of judges, and finds the failure **persists under
> common prompt-based mitigations**.
>
> The failure resolves in the *opposite direction* to ours. Their judges
> over-rely on parametric knowledge and **disregard** the provided reference —
> a candidate matching the swapped reference is graded Incorrect. CCC is
> capture *by* the conflicting conclusion: the judge follows the wrong
> reference and downgrades the correct candidate. Same conflict, opposite
> resolution. Their domain is entity QA; ours is three domains with executable
> oracles, which is likely why the direction differs — with an executable
> oracle there is no parametric belief to fall back on.

**Evans, J. St. B. T., Barston, J. L., Pollard, P.**
*On the conflict between logic and belief in syllogistic reasoning.*
Memory & Cognition, 1983, **11**(3), 295–306.

> The human antecedent. Belief bias survives controls for premise conversion
> and response bias, and is stronger on invalid syllogisms. CCC is this effect
> relocated into an evaluator's context window.

## LLM-judge bias, reference and auxiliary information

**Li, Q., Dou, S., Shao, K., Chen, C., Hu, H.** (Ant Group)
*Evaluating Scoring Bias in LLM-as-a-Judge.*
arXiv:2506.22316v4 [cs.CL], 3 February 2026.

> Explicitly about **scoring-based** rather than comparative judges — our
> setup. Defines **reference answer score bias** among three new scoring
> biases.

**Li, W., Wang, X., Yuan, S., Xu, R., Chen, J., Dong, Q., Xiao, Y., Yang, D.**
*Curse of Knowledge: When Complex Evaluation Context Benefits yet Biases
LLM Judges.*
Findings of the ACL: EMNLP 2025, pages 14900–14924.

> Auxiliary information — reference answers, rubrics — improves judges and
> simultaneously opens new attack surface. Reports Large Reasoning Models as
> *paradoxically* more vulnerable, which bears on our four-arm protocol split.

**Hwang, Y., Lee, D., Kang, T., Kim, Y., Jung, K.**
*Can You Trick the Grader? Adversarial Persuasion of LLM Judges.*
Findings of the ACL: EMNLP 2025, pages 14632–14651.

> Seven persuasion techniques including **Authority**, on **mathematical
> reasoning**, where correctness should be style-independent. Inflation up to
> 8%; model size does not mitigate; **persists under counter-prompting**.
> Bears directly on §5.2 and on §7's verification result.

**Chen, G. H., Chen, S., Liu, Z., Jiang, F., Wang, B.**
*Humans or LLMs as the Judge? A Study on Judgement Bias.*
Proceedings of the 2024 Conference on Empirical Methods in Natural Language
Processing, pages 8301–8327. November 12–16, 2024.
The Chinese University of Hong Kong, Shenzhen / Shenzhen Research Institute of
Big Data.

> Reference-free framework probing **Misinformation Oversight Bias, Gender
> Bias, Authority Bias, Beauty Bias** in human and LLM judges, including a
> **fake references** perturbation, then exploits the biases as attacks.
> Our §5.2 finds an authority label adds nothing over a bare wrong answer;
> that needs stating against their authority-bias result.

**Koo, R., Lee, M., Raheja, V., Park, J., Kim, Z. M., Kang, D.**
*Benchmarking Cognitive Biases in Large Language Models as Evaluators.*
Findings of the ACL: ACL 2024, pages 517–545. (COBBLER)

> 16 models, six cognitive biases, ~40% of comparisons showing bias; human–
> machine rank-biased overlap 44%.

## Why prompt-level verification cannot be trusted

**Turpin, M., Michael, J., Perez, E., Bowman, S. R.**
*Language Models Don't Always Say What They Think: Unfaithful Explanations in
Chain-of-Thought Prompting.*
NeurIPS 2023 (37th Conference on Neural Information Processing Systems).

> Biasing features change the answer while the CoT rationalises without ever
> mentioning them; accuracy drops up to 36%. This is the mechanism behind our
> `verify_written` arm reducing but never abolishing capture.

**Lanham, T., Chen, A., Radhakrishnan, A., et al.** (Anthropic; Brauner at Oxford)
*Measuring Faithfulness in Chain-of-Thought Reasoning.*
2023.
`Venue not stated on the title page — appears to be a preprint; confirm.`

> Intervention tests — early answering, adding mistakes, paraphrasing, filler
> tokens. Faithfulness *decreases* with scale on most tasks.

**Chen, Y., Benton, J., Radhakrishnan, A., Uesato, J., Denison, C., Schulman, J.,
Somani, A., Hase, P., Wagner, M., Roger, F., Mikulik, V., Bowman, S. R.,
Leike, J., Kaplan, J., Perez, E.** (Alignment Science Team, Anthropic)
*Reasoning Models Don't Always Say What They Think.*
May 2025. No venue line on the title page — preprint.

> Reasoning models reveal hint usage in under 20% of cases; outcome-based RL
> improves faithfulness then plateaus. Relevant to the reasoning-protocol
> differences across the four-arm panel.

## Status of the eight cited works — all confirmed

None is in the source folder, so each was confirmed separately against its
official proceedings record (ACL Anthology, NeurIPS proceedings, OpenReview,
ACM DL), supplied by the author. Venue, year, page range, DOI and arXiv
identifier now come from that record in every entry, and the "compiled without
live bibliographic access" warning has been removed from the paper because it
is no longer true.

| # | Work | Status |
|---|---|---|
| 1 | Zheng et al., MT-Bench / Chatbot Arena | **confirmed** — NeurIPS 2023 Datasets and Benchmarks Track, arXiv:2306.05685. Full author list and arXiv ID supplied by the author and written into the entry. |
| 2 | Liu et al., G-Eval | **confirmed** — EMNLP 2023, pp. 2511–2522, DOI 10.18653/v1/2023.emnlp-main.153, arXiv:2303.16634. §2 described it as reference-based; it is reference-free, and the sentence has been corrected. See below. |
| 3 | Wang et al., Not Fair Evaluators | **confirmed** — ACL 2024, Vol. 1 Long Papers, pp. 9440–9450, DOI 10.18653/v1/2024.acl-long.511, arXiv:2305.17926. In-text citation corrected from 2023 to **2024**. |
| 4 | Panickssery et al., Own Generations | **confirmed** — NeurIPS 37 (2024), DOI 10.52202/079017-2197, arXiv:2404.13076. Author list was already complete and the in-text year already correct; no body change needed. |
| 5 | Sharma et al., Sycophancy | **confirmed** — ICLR 2024, arXiv:2310.13548. All nineteen authors now listed. In-text citation corrected from 2023 to **2024**. |
| 6 | Greshake et al., Indirect Prompt Injection | **confirmed** — 16th ACM Workshop on AI and Security (AISec '23), pp. 79–90, DOI 10.1145/3605764.3623985, arXiv:2302.12173. Venue expanded from the bare "AISec" to the full workshop proceedings title. In-text year already correct. |
| 7 | Wei et al., Chain-of-Thought | **confirmed** — NeurIPS 35 (2022), arXiv:2201.11903. All nine authors now listed. In-text year already correct. |
| 8 | Wang et al., Self-Consistency | **confirmed** — ICLR 2023, arXiv:2203.11171. All eight authors now listed. In-text citation corrected from 2022 to **2023**. |

Two defects are independent of that check. Progress on both:

**Year mismatches (#3, #5, #8) — closed.** All three in-text citations now
carry the venue year rather than the arXiv year: ACL 2024, ICLR 2024, ICLR
2023. The body and the list agree throughout.

**The "Wang et al." collision (#3 vs #8) — closed.** Confirmed as ACL **2024**
and ICLR **2023**, so the year alone disambiguates and no a/b suffix is needed.
Worth knowing they are also different people: #3 is Peiyi Wang, #8 is Xuezhi
Wang, who is separately the second author of #7. Initials in the in-text
citations would make that explicit; the author's decision is to leave it, on
the grounds that a reader can look it up.

### Resolved on #2: G-Eval is reference-free, and §2 said otherwise

§2 previously read: *"…and reference-based variants such as G-Eval (Liu et al.,
2023)."* That was wrong. The G-Eval prompt template conditions the judge on the
**source document and the candidate**, and the auto-generated evaluation steps
read *"Read the news article carefully… Read the summary and compare it to the
news article."* No gold answer is supplied at any point. Confirmed against the
primary source text; aclanthology.org is 403 through this proxy, so the excerpt
came from the author.

§2 now describes G-Eval accurately as single-output scoring, notes explicitly
that it is reference-free, and states the reference-conditioned setting as the
paper's own rather than attributing it to G-Eval.

**Closed.** §2's prompt-injection paragraph claimed the wrong reference answer is
*"of the kind evaluation pipelines routinely paste into judge prompts"* with no
citation once #2 stopped supporting it. It now cites Lee et al. (#9), whose
swapped-reference framework is exactly a study of that practice.
