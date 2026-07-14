# Exploratory paired-choice probability analysis

This is a post-hoc, interpretation-focused analysis of the frozen confirmatory observations.
It does not change the preregistered score-discrimination analysis or its support calls.

## Probability interpretation

For each matched correct and wrong candidate pair, define a correct-branch win as the correct
candidate receiving the higher score. A tie contributes half a win:

\[
q = P(S_{correct} > S_{wrong})
  + \frac{1}{2}P(S_{correct} = S_{wrong}).
\]

The empirical probability form of Contextual Conclusion Capture is:

\[
\Delta q_{capture} = q_{no\ conflict} - q_{conflicting\ conclusion}.
\]

A positive value is the estimated probability that the conflicting conclusion diverts the
judge from the branch it would otherwise choose correctly. This is an observed paired-win
frequency over the frozen items and repetitions, not a calibrated estimate of the model's
internal belief or posterior probability of truth.

The analysis is fail-closed: an item enters a contrast only when both candidates succeeded in
all three repetitions under both the baseline and conflict conditions. Confidence intervals
are item-clustered bootstrap intervals (10,000 draws; seed 20260714).

## Results

| Model | Protocol | Conflict | Complete items | P(correct wins), baseline | P(correct wins), conflict | Probability drop [95% item-bootstrap CI] |
|---|---|---|---:|---:|---:|---:|
| GPT-4o mini | score_only | bare conclusion | 16 | 61.5% | 36.5% | +25.0% [+2.1%, +47.9%] |
| GPT-4o mini | score_only | full rationale | 16 | 61.5% | 37.5% | +24.0% [-2.1%, +50.0%] |
| GPT-4o mini | verify_written | bare conclusion | 16 | 86.5% | 86.5% | +0.0% [-12.5%, +11.5%] |
| GPT-4o mini | verify_written | full rationale | 16 | 86.5% | 74.0% | +12.5% [+3.1%, +24.0%] |
| Claude Haiku 4.5 | score_only | bare conclusion | 4 | 87.5% | 0.0% | +87.5% [+62.5%, +100.0%] |
| Claude Haiku 4.5 | score_only | full rationale | 3 | 100.0% | 83.3% | +16.7% [+0.0%, +50.0%] |
| Claude Haiku 4.5 | verify_written | bare conclusion | 16 | 100.0% | 100.0% | +0.0% [+0.0%, +0.0%] |
| Claude Haiku 4.5 | verify_written | full rationale | 16 | 100.0% | 96.9% | +3.1% [+0.0%, +9.4%] |
| Gemini 2.5 Flash | score_only | bare conclusion | 16 | 78.1% | 53.1% | +25.0% [+5.2%, +45.8%] |
| Gemini 2.5 Flash | score_only | full rationale | 16 | 78.1% | 59.4% | +18.8% [+3.1%, +37.5%] |
| Gemini 2.5 Flash | verify_written | bare conclusion | 12 | 97.2% | 100.0% | -2.8% [-8.3%, +0.0%] |
| Gemini 2.5 Flash | verify_written | full rationale | 9 | 96.3% | 100.0% | -3.7% [-11.1%, +0.0%] |
| DeepSeek Chat | score_only | bare conclusion | 16 | 71.9% | 41.7% | +30.2% [+18.8%, +41.7%] |
| DeepSeek Chat | score_only | full rationale | 16 | 71.9% | 50.0% | +21.9% [+11.5%, +33.3%] |
| DeepSeek Chat | verify_written | bare conclusion | 16 | 89.6% | 92.7% | -3.1% [-10.4%, +4.2%] |
| DeepSeek Chat | verify_written | full rationale | 16 | 89.6% | 77.1% | +12.5% [+3.1%, +22.9%] |
| Llama 3.3 70B | score_only | bare conclusion | 16 | 71.9% | 28.1% | +43.8% [+31.2%, +56.2%] |
| Llama 3.3 70B | score_only | full rationale | 16 | 71.9% | 29.2% | +42.7% [+26.0%, +56.2%] |
| Llama 3.3 70B | verify_written | bare conclusion | 16 | 82.3% | 44.8% | +37.5% [+21.9%, +53.1%] |
| Llama 3.3 70B | verify_written | full rationale | 16 | 82.3% | 43.8% | +38.5% [+14.6%, +60.4%] |

## Reading the fork

For all four measurable score-only models, the bare conflicting conclusion reduced the chance
that the correct candidate won the paired comparison. The estimated probability drop was 25.0
points for GPT-4o mini, 25.0 for Gemini, 30.2 for DeepSeek, and 43.8 for Llama. Claude's sparse
score-only estimate is not interpreted because only four items were complete.

Written verification removed the measurable bare-conclusion probability drop for GPT, Gemini,
and DeepSeek. Llama remained vulnerable: its correct-branch win probability fell from 82.3% to
44.8%, a 37.5-point drop. This matches the preregistered score-discrimination result while
expressing the effect as an intuitive branch-selection frequency.

Reproduce with:

```bash
python experiments/analyze_confirmatory_choice_probability.py
```
