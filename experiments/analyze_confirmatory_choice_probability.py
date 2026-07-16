#!/usr/bin/env python3
"""Post-hoc paired-win probability analysis for the frozen confirmatory run.

This analysis does not reinterpret judge scores as calibrated beliefs. It reports the
empirical probability that the correct candidate receives a higher score than the matched
wrong candidate, assigning half a win to ties. Contrasts use the same fail-closed rule as the
confirmatory analysis: all three repetitions of both candidates in both conditions must be
present for an item to enter a contrast.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Iterable


MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-haiku-4.5",
    "google/gemini-2.5-flash",
    "deepseek/deepseek-chat",
    "meta-llama/llama-3.3-70b-instruct",
]
MODEL_LABELS = {
    "openai/gpt-4o-mini": "GPT-4o mini",
    "anthropic/claude-haiku-4.5": "Claude Haiku 4.5",
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
    "deepseek/deepseek-chat": "DeepSeek Chat",
    "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B",
}
PROTOCOLS = ["score_only", "verify_written"]
TARGETS = [
    ("neutral/wrong_answer_only", "bare conclusion"),
    ("neutral/full_wrong_rationale", "full rationale"),
]
REPETITIONS = (0, 1, 2)


def condition_name(condition: dict[str, object]) -> str:
    label = condition.get("label_key")
    content = condition.get("content_key")
    if not label and not content:
        return "no_injection"
    return f"{label}/{content}"


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def paired_win(correct_score: float, wrong_score: float) -> float:
    if correct_score > wrong_score:
        return 1.0
    if correct_score < wrong_score:
        return 0.0
    return 0.5


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values)


def load_successes(path: Path) -> tuple[dict[tuple[str, ...], float], set[str]]:
    successes: dict[tuple[str, ...], float] = {}
    items: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            score = row.get("score")
            if score is None:
                continue
            item = str(row["item_id"])
            items.add(item)
            key = (
                str(row["model"]),
                str(row["protocol"]),
                condition_name(row["condition"]),
                item,
                str(row["repetition"]),
                str(row["candidate_type"]),
            )
            if key in successes:
                raise ValueError(
                    f"duplicate successful cell at line {line_number}: {key}"
                )
            successes[key] = float(score)
    return successes, items


def item_probabilities(
    successes: dict[tuple[str, ...], float],
    items: set[str],
    model: str,
    protocol: str,
    target: str,
) -> list[tuple[str, float, float, float]]:
    complete: list[tuple[str, float, float, float]] = []
    for item in sorted(items):
        baseline_wins: list[float] = []
        target_wins: list[float] = []
        missing = False
        for repetition in REPETITIONS:
            repetition = str(repetition)
            values: dict[tuple[str, str], float] = {}
            for condition in ("no_injection", target):
                for candidate in ("correct", "wrong_matching"):
                    key = (model, protocol, condition, item, repetition, candidate)
                    if key not in successes:
                        missing = True
                        break
                    values[(condition, candidate)] = successes[key]
                if missing:
                    break
            if missing:
                break
            baseline_wins.append(
                paired_win(
                    values[("no_injection", "correct")],
                    values[("no_injection", "wrong_matching")],
                )
            )
            target_wins.append(
                paired_win(
                    values[(target, "correct")],
                    values[(target, "wrong_matching")],
                )
            )
        if not missing:
            baseline = mean(baseline_wins)
            conflict = mean(target_wins)
            complete.append((item, baseline, conflict, baseline - conflict))
    return complete


def bootstrap_interval(
    item_rows: list[tuple[str, float, float, float]],
    iterations: int,
    seed: int,
) -> tuple[float, float]:
    rng = random.Random(seed)
    effects = [row[3] for row in item_rows]
    draws = [
        mean(rng.choice(effects) for _ in effects)
        for _ in range(iterations)
    ]
    return quantile(draws, 0.025), quantile(draws, 0.975)


def stable_seed(base_seed: int, *parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    return base_seed ^ int.from_bytes(digest[:8], "big")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=Path(__file__).parent / "results" / "provinj_obs_confirmatory.jsonl",
    )
    parser.add_argument("--bootstrap", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260714)
    args = parser.parse_args()

    successes, items = load_successes(args.jsonl)
    print(
        "| Model | Protocol | Conflict | Complete items | "
        "P(correct wins), baseline | P(correct wins), conflict | "
        "Probability drop [95% item-bootstrap CI] |"
    )
    print("|---|---|---|---:|---:|---:|---:|")
    for model in MODELS:
        for protocol in PROTOCOLS:
            for target, target_label in TARGETS:
                rows = item_probabilities(
                    successes, items, model, protocol, target
                )
                if not rows:
                    print(
                        f"| {MODEL_LABELS[model]} | {protocol} | {target_label} | "
                        "0 | unavailable | unavailable | unavailable |"
                    )
                    continue
                baseline = mean(row[1] for row in rows)
                conflict = mean(row[2] for row in rows)
                effect = mean(row[3] for row in rows)
                lower, upper = bootstrap_interval(
                    rows,
                    args.bootstrap,
                    stable_seed(args.seed, model, protocol, target),
                )
                print(
                    f"| {MODEL_LABELS[model]} | {protocol} | {target_label} | "
                    f"{len(rows)} | {baseline:.1%} | {conflict:.1%} | "
                    f"{effect:+.1%} [{lower:+.1%}, {upper:+.1%}] |"
                )


if __name__ == "__main__":
    main()
