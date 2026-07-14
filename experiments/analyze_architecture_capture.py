#!/usr/bin/env python3
"""Fail-closed analysis for the frozen contextual-capture architecture run."""

from __future__ import annotations

import hashlib
import json
import random
import statistics
from collections import Counter
from pathlib import Path

from run_architecture_capture import (
    ARCHITECTURES,
    CANDIDATES,
    MODELS,
    OBS_PATH,
    REFERENCES,
    REPETITIONS,
    SOLVER_PATH,
    JudgeRow,
    SolverRow,
    judge_key,
    normalize_answer,
    solver_key,
)
from run_provenance_injection import CONFIRMATORY_CACHE, CONFIRMATORY_RAW, build_items


BOOTSTRAPS = 10_000
BOOTSTRAP_SEED = 20260714


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def stable_seed(label: str) -> int:
    digest = hashlib.sha256(label.encode()).digest()
    return BOOTSTRAP_SEED ^ int.from_bytes(digest[:8], "big")


def bootstrap(per_item: dict[str, float], label: str) -> tuple[float, float, float, int]:
    if not per_item:
        return float("nan"), float("nan"), float("nan"), 0
    values = list(per_item.values())
    rng = random.Random(stable_seed(label))
    draws = [statistics.fmean(rng.choice(values) for _ in values) for _ in range(BOOTSTRAPS)]
    return statistics.fmean(values), quantile(draws, 0.025), quantile(draws, 0.975), len(values)


def load_judges() -> list[JudgeRow]:
    return [JudgeRow(**json.loads(line)) for line in OBS_PATH.open(encoding="utf-8") if line.strip()]


def load_solvers() -> list[SolverRow]:
    return [SolverRow(**json.loads(line)) for line in SOLVER_PATH.open(encoding="utf-8") if line.strip()]


def successful_cells(rows: list[JudgeRow]) -> dict[tuple, JudgeRow]:
    grouped: dict[tuple, list[JudgeRow]] = {}
    for row in rows:
        grouped.setdefault(judge_key(row), []).append(row)
    duplicates = [key for key, group in grouped.items() if sum(x.score is not None for x in group) > 1]
    if duplicates:
        raise RuntimeError(f"duplicate successful judge cells: {duplicates[:3]}")
    return {
        key: next(x for x in group if x.score is not None)
        for key, group in grouped.items()
        if any(x.score is not None for x in group)
    }


def discrimination(
    cells: dict[tuple, JudgeRow], model: str, architecture: str, reference: str, item: str
):
    correct, wrong = [], []
    for repetition in range(REPETITIONS):
        base = (item, model, architecture, reference)
        ckey = (*base, "correct", repetition)
        wkey = (*base, "wrong_matching", repetition)
        if ckey not in cells or wkey not in cells:
            return None
        correct.append(cells[ckey].score)
        wrong.append(cells[wkey].score)
    return statistics.fmean(correct) - statistics.fmean(wrong)


def correct_win_probability(
    cells: dict[tuple, JudgeRow], model: str, architecture: str, reference: str, item: str
):
    wins = []
    for repetition in range(REPETITIONS):
        base = (item, model, architecture, reference)
        ckey = (*base, "correct", repetition)
        wkey = (*base, "wrong_matching", repetition)
        if ckey not in cells or wkey not in cells:
            return None
        c, w = cells[ckey].score, cells[wkey].score
        wins.append(1.0 if c > w else (0.0 if c < w else 0.5))
    return statistics.fmean(wins)


def paired_effect(items, function):
    out = {}
    for item in items:
        value = function(item)
        if value is not None:
            out[item] = value
    return out


def fmt(result, probability=False):
    mean, lower, upper, n = result
    scale = 100 if probability else 1
    suffix = "%" if probability else ""
    return f"n={n:<2} mean={mean*scale:+.2f}{suffix} 95% CI [{lower*scale:+.2f}{suffix}, {upper*scale:+.2f}{suffix}]"


def main() -> None:
    rows = load_judges()
    solvers = load_solvers()
    cells = successful_cells(rows)
    items = sorted({row.item_id for row in rows})

    print("[evidence]")
    print(f"  attempts={len(rows)} successes={sum(x.score is not None for x in rows)} failures={sum(x.score is None for x in rows)} unique_success_cells={len(cells)}")
    failures = Counter((x.model, x.architecture) for x in rows if x.score is None)
    for (model, architecture), count in sorted(failures.items()):
        print(f"  failures {model} | {architecture}: {count}")

    print("\n[primary fail-closed contrasts]")
    for model in MODELS:
        def disc(architecture, reference, item):
            return discrimination(cells, model, architecture, reference, item)

        susceptibility_score = paired_effect(items, lambda item: (
            None if disc("contaminated_score_only", "correct_reference", item) is None
                    or disc("contaminated_score_only", "wrong_reference", item) is None
            else disc("contaminated_score_only", "correct_reference", item)
                 - disc("contaminated_score_only", "wrong_reference", item)
        ))
        mitigation_verify = paired_effect(items, lambda item: (
            None if any(disc(a, r, item) is None for a in
                        ("contaminated_score_only", "contaminated_verify_written")
                        for r in REFERENCES)
            else (disc("contaminated_score_only", "correct_reference", item)
                  - disc("contaminated_score_only", "wrong_reference", item))
                 - (disc("contaminated_verify_written", "correct_reference", item)
                    - disc("contaminated_verify_written", "wrong_reference", item))
        ))
        isolation_gain = paired_effect(items, lambda item: (
            None if disc("context_isolated_score_only", "wrong_reference", item) is None
                    or disc("contaminated_score_only", "wrong_reference", item) is None
            else disc("context_isolated_score_only", "wrong_reference", item)
                 - disc("contaminated_score_only", "wrong_reference", item)
        ))
        router_gain = paired_effect(items, lambda item: (
            None if disc("conflict_router", "wrong_reference", item) is None
                    or disc("contaminated_score_only", "wrong_reference", item) is None
            else disc("conflict_router", "wrong_reference", item)
                 - disc("contaminated_score_only", "wrong_reference", item)
        ))
        print(f"\nMODEL: {model}")
        print("  reference susceptibility, contaminated score:", fmt(bootstrap(susceptibility_score, model + " susceptibility")))
        print("  written-verification mitigation:", fmt(bootstrap(mitigation_verify, model + " verify mitigation")))
        print("  isolation safeguard gain under wrong ref:", fmt(bootstrap(isolation_gain, model + " isolation gain")))
        print("  router safeguard gain under wrong ref:", fmt(bootstrap(router_gain, model + " router gain")))

    print("\n[secondary cell summaries]")
    for model in MODELS:
        print(f"\nMODEL: {model}")
        for architecture in ARCHITECTURES:
            for reference in REFERENCES:
                discs = paired_effect(items, lambda item, a=architecture, r=reference:
                                      discrimination(cells, model, a, r, item))
                wins = paired_effect(items, lambda item, a=architecture, r=reference:
                                     correct_win_probability(cells, model, a, r, item))
                print(f"  {architecture} | {reference}: disc {fmt(bootstrap(discs, model+architecture+reference+'disc'))}; correct-win {fmt(bootstrap(wins, model+architecture+reference+'win'), probability=True)}")

    solver_map = {solver_key(row): row for row in solvers}
    if len(solver_map) != len(solvers):
        raise RuntimeError("duplicate routing solver rows")
    frozen_items = {item.item_id: item for item in build_items(None, CONFIRMATORY_RAW, CONFIRMATORY_CACHE)}
    print("\n[router detection]")
    for model in MODELS:
        per_item = {}
        for item_id, item in frozen_items.items():
            correct_disagree, wrong_disagree = [], []
            complete = True
            for repetition in range(REPETITIONS):
                row = solver_map.get((item_id, model, repetition))
                if row is None:
                    complete = False
                    break
                parsed = normalize_answer(row.parsed_answer) if row.parsed_answer is not None else None
                correct_disagree.append(float(parsed != normalize_answer(item.correct_answer)))
                wrong_disagree.append(float(parsed != normalize_answer(item.wrong_answer)))
            if complete:
                per_item[item_id] = statistics.fmean(wrong_disagree) - statistics.fmean(correct_disagree)
        print(f"  {model}: wrong-minus-correct conflict detection {fmt(bootstrap(per_item, model+' detection'), probability=True)}")


if __name__ == "__main__":
    main()
