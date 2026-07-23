# CCC OpenRouter open-weight-focused extension

Status: **four complete full arms; all independently audited**

The OpenRouter extension now has complete evidence for Qwen 3.7 Plus, Kimi K2.7
Code, MiniMax M3, and GLM 5.2. It is an endpoint/model comparison, not a model-
license audit; Qwen is retained as the hosted comparator. The main result is
stronger than the individual model stories: **SQL capture appears in every tested
arm**, despite different providers and response-generation protocols.

## Full-arm result matrix

| Model | Protocol boundary | Arithmetic | Code | SQL | Full-path cost |
|---|---|---:|---:|---:|---:|
| Qwen 3.7 Plus | bounded reasoning, Alibaba | **+94.17 SUPPORTED** | -9.27 ns | **+165.28 SUPPORTED** | $1.895857* |
| Kimi K2.7 Code | native reasoning, Together | -11.88 ns | +1.46 ns | **+70.69 SUPPORTED** | $5.88112648 |
| MiniMax M3 | no reasoning, Minimax | **+75.17 SUPPORTED** | **+19.65 SUPPORTED** | **+143.68 SUPPORTED** | $0.08259708 |
| GLM 5.2 | no reasoning, Together | **+52.08 SUPPORTED** | +13.33 ns | **+148.61 SUPPORTED** | $0.30049448 |

`*` Qwen's recorded scored-cell cost is $1.895857; its earlier audit did not fold
separate launch preflight cost into that figure. The four documented totals sum
to approximately **$8.16**, dominated by Kimi's native reasoning.

## What the panel establishes

1. **SQL is the cross-model invariant.** All four arms support SQL capture, with
   effects from +70.69 to +165.28 points. This reproduces the frontier-panel SQL
   result in a materially different model family and cost tier.

2. **Arithmetic capture is common but not universal.** Qwen, MiniMax, and GLM
   support it; Kimi instead has a small reverse-direction estimate. This also
   shows that Fable's earlier arithmetic capture was not a one-model curiosity.

3. **Code remains model-specific.** Only MiniMax supports the primary code
   contrast. GLM's primary estimate is uncertain, although its +52.1 provenance
   increment is large. Qwen and Kimi show no code capture.

4. **Reasoning is not required for capture.** MiniMax and GLM used no reasoning
   tokens yet showed large arithmetic and SQL effects. Kimi's native reasoning
   also did not protect SQL judging.

5. **Pilot-first configuration worked.** The compatibility work identified the
   valid contract for every endpoint before the full runs. MiniMax plus GLM then
   delivered 2,688 complete cells for only **$0.38309156**, with zero final
   failures, retries, reasoning tokens, or endpoint drift.

## Evidence quality and comparison limits

Every arm has 1,344 unique successful cells and complete condition × candidate
strata. Prompt hashes, attempts, finish reasons, endpoint identity, balance, and
cost were independently audited. MiniMax and GLM additionally have zero reasoning
usage on every response and exact one-field JSON throughout.

The effect estimates can be compared descriptively, but protocol-separated arms
must not be naively pooled. Kimi used provider-default native reasoning; Qwen used
bounded reasoning; MiniMax and GLM used a terse no-reasoning contract. Those
differences are part of the endpoint-valid configurations, not nuisance details
to erase after the fact.

## Bottom line

The open-weight interrogation was worth doing. It replaces a single-family
frontier result with a broader pattern: SQL conclusion capture is robust across
all four tested arms, while arithmetic and code sensitivity vary sharply by
model. The cheap no-reasoning arms also show that this is not simply an artefact
of long chains of thought or expensive sampling.
