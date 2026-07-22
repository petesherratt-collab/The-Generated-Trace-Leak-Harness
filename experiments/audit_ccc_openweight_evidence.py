"""Independent structural audit for frozen CCC OpenRouter evidence.

This script does not call an API and does not reuse the runner's completion
metadata builder.  It recomputes cell uniqueness, prompt hashes, response
contracts, endpoint identity, reasoning use, attempts, balance, and cost from
the raw JSONL evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def exact_score(raw: object, expected: object) -> bool:
    if not isinstance(raw, str) or raw != raw.strip():
        return False
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return False
    if not isinstance(parsed, dict) or set(parsed) != {"score"}:
        return False
    value = parsed["score"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value)) and 0 <= float(value) <= 100 and float(value) == float(expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--reasoning-ceiling", type=int, default=0)
    args = parser.parse_args()

    root = args.evidence_dir.resolve()
    prefix = args.prefix
    meta_path = root / f"{prefix}_meta.json"
    completion_path = root / f"{prefix}_completion_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    completion = json.loads(completion_path.read_text(encoding="utf-8"))

    conditions = list(meta["conditions"])
    candidates = list(meta["candidates"])
    protocols = list(meta["protocols"])
    models = list(meta["models"])
    reps = int(meta["reps"])
    expected_identity = meta["endpoint_identities"]
    provider_requested = meta["provider_route"]

    errors: list[str] = []
    total_rows = total_expected = total_attempts = total_transport = 0
    total_provider_responses = total_reasoning_records = 0
    total_cost = 0.0
    all_files: list[Path] = []

    print("CCC open-weight raw-evidence independent audit")
    print(f"study: {meta['study']}")
    print(f"run_id: {meta['run_id']}")
    print(f"config_sha256: {meta['config_sha256']}")
    print(f"schedule: {meta['schedule_version']}; seed: {meta['seed']}; repetitions: {reps}")
    print(f"models: {', '.join(models)}")
    print(f"provider route: {provider_requested}; fallbacks: {meta['provider_fallbacks']}")
    print(f"reasoning policy: {json.dumps(meta['reasoning_policy'], sort_keys=True)}")
    print()
    print("domain rows expected unique duplicate success attempts transport reasoning max_reason cost")

    for domain in meta["domains"]:
        obs_path = root / f"{prefix}_{domain}_obs.jsonl"
        prompt_path = root / f"{prefix}_{domain}_prompts.jsonl"
        all_files.extend((obs_path, prompt_path))
        rows = load_jsonl(obs_path)
        prompts = load_jsonl(prompt_path)
        item_ids = list(meta["selected_item_ids"][domain])
        expected = len(item_ids) * len(models) * len(conditions) * len(candidates) * len(protocols) * reps
        expected_prompts = len(item_ids) * len(conditions) * len(candidates) * len(protocols)
        keys = [
            (
                row.get("domain"), row.get("item_id"), row.get("model"),
                row.get("condition"), row.get("candidate_type"),
                row.get("repetition"), row.get("protocol"),
            )
            for row in rows
        ]
        unique = len(set(keys))
        duplicates = len(keys) - unique
        successes = sum(row.get("score") is not None and not row.get("error") for row in rows)
        attempts = sum(len(row.get("attempts") or []) for row in rows)
        transport = 0
        provider_responses = reasoning_records = 0
        max_reasoning = 0
        cost = 0.0

        prompt_map: dict[str, str] = {}
        for record in prompts:
            digest, prompt = record.get("sha256"), record.get("prompt")
            if not isinstance(digest, str) or not isinstance(prompt, str):
                errors.append(f"{domain}: malformed prompt record")
                continue
            if sha256_bytes(prompt.encode()) != digest:
                errors.append(f"{domain}: prompt digest mismatch {digest}")
            if digest in prompt_map:
                errors.append(f"{domain}: duplicate prompt digest {digest}")
            prompt_map[digest] = prompt
        if len(prompt_map) != expected_prompts:
            errors.append(f"{domain}: prompts {len(prompt_map)} != {expected_prompts}")

        strata = Counter()
        for row_index, row in enumerate(rows):
            if row.get("run_id") != meta["run_id"]:
                errors.append(f"{domain}: run_id mismatch")
            if row.get("prompt_sha256") not in prompt_map:
                errors.append(f"{domain}: missing prompt reference")
            if row.get("attempt_count") != len(row.get("attempts") or []):
                errors.append(f"{domain}: attempt_count mismatch")
            if row.get("score") is None or row.get("error"):
                errors.append(f"{domain}: failed final cell {keys[row_index]}")
            if row.get("finish_reason") != "stop":
                errors.append(f"{domain}: final finish_reason {row.get('finish_reason')!r}")
            if not exact_score(row.get("raw_response"), row.get("score")):
                errors.append(f"{domain}: non-exact final score response")
            strata[(row.get("condition"), row.get("candidate_type"))] += 1

            for index, attempt in enumerate(row.get("attempts") or [], start=1):
                if attempt.get("attempt") != index:
                    errors.append(f"{domain}: non-sequential judge attempts")
                if attempt.get("provider_requested") != provider_requested:
                    errors.append(f"{domain}: provider request changed")
                transport += int(attempt.get("transport_attempt_count") or 0)
                if not attempt.get("call_error"):
                    provider_responses += 1
                    identity = expected_identity[row["model"]]
                    if attempt.get("response_model") != identity["response_model"]:
                        errors.append(f"{domain}: response model changed")
                    if attempt.get("provider") != identity["provider"]:
                        errors.append(f"{domain}: provider changed")
                usage = attempt.get("usage") or {}
                details = usage.get("completion_tokens_details") or {}
                reasoning = details.get("reasoning_tokens")
                if reasoning is not None:
                    reasoning_records += 1
                    max_reasoning = max(max_reasoning, int(reasoning))
                if usage.get("cost") is not None:
                    cost += float(usage["cost"])

        expected_per_stratum = len(item_ids) * len(models) * len(protocols) * reps
        for condition in conditions:
            for candidate in candidates:
                actual = strata[(condition, candidate)]
                if actual != expected_per_stratum:
                    errors.append(
                        f"{domain}: stratum {condition}/{candidate} {actual} != {expected_per_stratum}"
                    )

        if len(rows) != expected:
            errors.append(f"{domain}: rows {len(rows)} != {expected}")
        if unique != expected or duplicates:
            errors.append(f"{domain}: unique/duplicate cells {unique}/{duplicates}")
        if successes != expected:
            errors.append(f"{domain}: successes {successes} != {expected}")
        if reasoning_records != provider_responses:
            errors.append(f"{domain}: reasoning telemetry missing")
        if max_reasoning > args.reasoning_ceiling:
            errors.append(f"{domain}: reasoning {max_reasoning} > {args.reasoning_ceiling}")

        complete_domain = completion["domains"][domain]
        if complete_domain["observation_sha256"] != sha256_file(obs_path):
            errors.append(f"{domain}: completion observation hash mismatch")
        if complete_domain["prompt_manifest_sha256"] != sha256_file(prompt_path):
            errors.append(f"{domain}: completion prompt hash mismatch")

        print(
            f"{domain:5} {len(rows):4} {expected:8} {unique:6} {duplicates:9} "
            f"{successes:7} {attempts:8} {transport:9} {reasoning_records:9} "
            f"{max_reasoning:10} ${cost:.8f}"
        )
        total_rows += len(rows)
        total_expected += expected
        total_attempts += attempts
        total_transport += transport
        total_provider_responses += provider_responses
        total_reasoning_records += reasoning_records
        total_cost += cost

    if completion.get("run_id") != meta.get("run_id"):
        errors.append("completion run_id mismatch")
    if completion.get("config_sha256") != meta.get("config_sha256"):
        errors.append("completion config hash mismatch")
    if completion.get("initial_metadata_sha256") != sha256_file(meta_path):
        errors.append("completion initial metadata hash mismatch")
    if not completion.get("evidence_complete"):
        errors.append("completion metadata does not mark evidence complete")

    all_files.extend((meta_path, completion_path))
    print(
        f"TOTAL {total_rows:4} {total_expected:8} {total_rows:6} {0:9} "
        f"{total_rows:7} {total_attempts:8} {total_transport:9} "
        f"{total_reasoning_records:9} {'-':>10} ${total_cost:.8f}"
    )
    print(f"provider responses: {total_provider_responses}")
    print(f"prompt records: {sum(len(load_jsonl(root / f'{prefix}_{d}_prompts.jsonl')) for d in meta['domains'])}")
    print("file SHA-256:")
    for path in all_files:
        print(f"  {path.name} {sha256_file(path)}")

    if errors:
        print("AUDIT: FAIL")
        for error in errors[:100]:
            print(f"  - {error}")
        if len(errors) > 100:
            print(f"  ... and {len(errors) - 100} more")
        return 1
    print("AUDIT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
