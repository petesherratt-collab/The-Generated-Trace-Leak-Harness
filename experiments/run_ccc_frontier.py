"""run_ccc_frontier.py -- frontier-model extension of the CCC study across all three domains.

Tests whether more capable ("frontier latest") judges are susceptible to Contextual
Conclusion Capture, using the SAME FROZEN ITEMS as the small-tier runs so the small-vs-
frontier comparison is paired within item (the models are judges, not task-takers, and gold
is oracle-computed, so item reuse is a paired-design feature, not a leakage risk).

Design (Phase 1, cost-bounded): 3 domains (arithmetic / code / SQL) x N frontier models x
4 conditions x 2 candidate types x {score_only} x 3 reps, per domain. score_only is the
vulnerable, cheap protocol; verify_written is a separate Phase 2. Fresh seed. Each domain
reuses its own frozen prompt construction (no re-implementation):
  - arithmetic: confirmatory 16-item set (frozen cache + overrides) + build_judge_prompt;
  - code: ccc_code_items + run_ccc_codedomain.build_prompt (unit-test gold);
  - SQL: ccc_sql_items + run_ccc_sql.build_prompt (SQLite oracle, gold-signature gate).

Models are supplied at run time (--models a,b,c,d); aliases are NOT hardcoded because
"latest" drifts. `--check-models` validates each alias against the live API (one cheap call)
and reports resolve/pricing BEFORE any real run. Concurrency: fixed pool + single writer,
same invariants as the SQL adapters.

Modes: --check-models | --dry-run | --wiring-check | --run | --resume | --analyse-only
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _load_env import load_env
from provenance_injection_harness import parse_score

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

SEED = 305774821                     # authoritative frontier v3 seed
REPS = 3
DEFAULT_WORKERS = 4                  # conservative (frontier endpoints, tighter rate limits)
RUNNER_VERSION = "frontier-v3"
DEFAULT_STUDY = "frontier_v3"
DEFAULT_RUN_ID = "ccc_frontier_v3_305774821"
DEFAULT_OUTPUT_PREFIX = "ccc_frontier_v3"
PROMPT_INSTRUMENT = "ccc_frontier_prompt_v1"
SCHEDULE_VERSION = "sha256-domain-cell-v2"
DEFAULT_BALANCE_GAP = 0.05
COND_IDS = ["no_injection", "answer_only", "full_rationale", "solver_rationale"]
CANDIDATES = ["correct", "wrong_matching"]
# Budgets sized for REASONING judges: a frontier model spends reasoning tokens (counted
# against the completion budget) before emitting the verdict. The original 60/240 was tuned
# for terse small-tier judges and truncated reasoning models before they scored (amendment
# 2026-07-19). Terse models stop early and are billed on actual tokens, so the headroom is
# free for them and necessary for the reasoners.
MAX_TOK = {"score_only": 1024, "verify_written": 2048}
RETRY_TOK = {"score_only": 2048, "verify_written": 4096}


# --- Domain registry: each maps the 4 canonical conditions to its own frozen builder ------
def _sql_domain():
    import ccc_sql_items as it
    import run_ccc_sql as a
    stim = a.build_stimuli()
    cmap = {"no_injection": ("none", "no_injection"), "answer_only": ("neutral", "answer_only"),
            "full_rationale": ("neutral", "full_wrong_rationale"),
            "solver_rationale": ("solver", "full_wrong_rationale")}
    items = list(it.ITEMS)
    def build(item, cond_id, cand, proto):
        la, co = cmap[cond_id]
        return a.build_prompt(item, a.candidate_readable(item, cand), la, co, proto, stim)
    def gate():
        a.release_gate()
    return dict(items=items, id=lambda x: x["name"], build=build, gate=gate)


def _code_domain():
    import ccc_code_items as it
    import run_ccc_codedomain as a
    stim = a.build_stimuli()
    cmap = {"no_injection": ("none", "no_injection"), "answer_only": ("neutral", "answer_only"),
            "full_rationale": ("neutral", "full_wrong_rationale"),
            "solver_rationale": ("solver", "full_wrong_rationale")}
    items = list(it.ITEMS)
    def build(item, cond_id, cand, proto):
        la, co = cmap[cond_id]
        return a.build_prompt(item, a.cand_source(item, cand), la, co, proto, stim)
    def gate():
        a.release_gate()
    return dict(items=items, id=lambda x: x["name"], build=build, gate=gate)


def _arith_domain():
    import run_provenance_injection as rp
    from provenance_injection_harness import build_judge_prompt, Condition
    items = rp.build_items(None, rp.CONFIRMATORY_RAW, rp.CONFIRMATORY_CACHE)
    conds, _ = rp.confirmatory_conditions()
    by = {(c.label_key, c.content_key): c for c in conds}
    cmap = {"no_injection": (None, None), "answer_only": ("neutral", "wrong_answer_only"),
            "full_rationale": ("neutral", "full_wrong_rationale"),
            "solver_rationale": ("solver", "full_wrong_rationale")}
    def build(item, cond_id, cand, proto):
        return build_judge_prompt(item, by[cmap[cond_id]], cand, proto)
    def gate():
        if not rp.confirmatory_cache_frozen():
            raise RuntimeError("arithmetic confirmatory text cache is not frozen/verified")
        print("arith gate OK: confirmatory 16-item cache frozen and verified")
    return dict(items=items, id=lambda x: x.item_id, build=build, gate=gate)


DOMAINS = {"arith": _arith_domain, "code": _code_domain, "sql": _sql_domain}


def _sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _git_state():
    root = os.path.dirname(HERE)
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, check=True,
            capture_output=True, text=True,
        ).stdout.strip())
        return commit, dirty
    except (OSError, subprocess.SubprocessError):
        return None, None


def _stable_domain_seed(seed, domain):
    """Derive a process-stable sub-seed; never use Python's salted hash()."""
    digest = hashlib.sha256(f"{SCHEDULE_VERSION}|{seed}|{domain}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _identity_key(value):
    """Compare provider display names and slugs without case/punctuation noise."""
    return "".join(ch.lower() for ch in (value or "") if ch.isalnum())


# OpenRouter requests use stable provider slugs, while responses expose display
# names. Most normalize identically (``deepinfra`` -> ``DeepInfra``), but some do
# not (``alibaba`` -> ``Alibaba Cloud Int.``). Keep the exceptional mapping
# explicit and fail closed for everything else.
_PROVIDER_IDENTITY_ALIASES = {
    "alibaba": {"alibaba", "alibabacloudint"},
    "together": {"together", "togetherai"},
}

SCORE_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "ccc_score",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 100},
            },
            "required": ["score"],
            "additionalProperties": False,
        },
    },
}


def _provider_identity_matches(expected, actual):
    expected_key = _identity_key(expected)
    actual_key = _identity_key(actual)
    accepted = _PROVIDER_IDENTITY_ALIASES.get(expected_key, {expected_key})
    return bool(expected_key and actual_key in accepted)


# --- OpenRouter model preflight (validates aliases + score protocol) ---------------------
def check_models(models, key, call_fn=None, provider=None,
                 max_tok=MAX_TOK, retry_tok=RETRY_TOK, protocol="score_only",
                 score_acceptance="parsed"):
    if call_fn is None:
        from judge_integrity_real import call_openrouter
        call_fn = call_openrouter
    if protocol not in max_tok or protocol not in retry_tok:
        raise ValueError(f"unknown preflight protocol: {protocol}")
    print(f"preflight: validating model aliases and {protocol} score parsing")
    ok, records = [], []
    if protocol == "verify_written":
        prompt = ('Briefly verify in writing that 2 + 2 = 4. Then end with exactly one '
                  'JSON score object: {"score": 100}')
    else:
        prompt = 'Reply with only: {"score": 100}'
    for model in models:
        score, raw, err, fin, attempts = judge_once(
            prompt, model, protocol, key, call_fn, provider=provider,
            max_tok=max_tok, retry_tok=retry_tok, expected_provider=provider,
            score_acceptance=score_acceptance,
        )
        call_ok = score is not None and err is None
        endpoint = attempts[-1] if call_ok and attempts else {}
        parse_ok = (call_ok and bool(endpoint.get("response_model"))
                    and bool(endpoint.get("provider")))
        if call_ok and not parse_ok:
            err = "missing_resolved_endpoint_identity"
        print(f"  {'OK  ' if parse_ok else 'FAIL'} {model}  "
              f"(score/identity={'yes' if parse_ok else 'no'}; attempts={len(attempts)}; "
              f"finish={fin!r})")
        if attempts:
            usage = attempts[-1].get("usage") or {}
            details = usage.get("completion_tokens_details") or {}
            print("       usage: "
                  f"prompt={usage.get('prompt_tokens')!r}; "
                  f"completion={usage.get('completion_tokens')!r}; "
                  f"reasoning={details.get('reasoning_tokens')!r}; "
                  f"cost={usage.get('cost')!r}")
        if not parse_ok and attempts:
            last = attempts[-1]
            print("       diagnostic: "
                  f"error={err!r}; call={last.get('call_error')!r}; "
                  f"parse={last.get('parse_error')!r}; "
                  f"identity={last.get('identity_error')!r}; "
                  f"transport={last.get('transport_errors')!r}")
        if parse_ok:
            ok.append(model)
        records.append({
            "model": model,
            "protocol": protocol,
            "provider_requested": provider,
            "validated": parse_ok,
            "score": score,
            "raw_response": raw,
            "finish_reason": fin,
            "error": err,
            "attempts": attempts,
            "resolved_endpoint": {
                "response_model": endpoint.get("response_model"),
                "provider": endpoint.get("provider"),
            } if parse_ok else None,
            "timestamp": time.time(),
        })
    print(f"validated {len(ok)}/{len(models)} aliases "
          "(score and endpoint identity must both validate)")
    return ok, records


# --- Schedule (per domain, rep-block deconflicted) --------------------------------------
def build_schedule(domain, items_ids, models, protocols, seed=SEED, reps=REPS):
    # Freeze the cell order independently of the model panel. Each model sees
    # the same relative item/condition/candidate schedule, while all models still
    # receive every cell. This makes adding a model unable to reshuffle another.
    base = [(iid, c, cand, p) for iid in items_ids
            for c in COND_IDS for cand in CANDIDATES for p in protocols]
    sched = []
    for rep in range(reps):
        block = list(base)
        random.Random(_stable_domain_seed(seed, domain) + rep).shuffle(block)
        for iid, cond, cand, proto in block:
            sched.extend((iid, model, cond, cand, proto, rep) for model in models)
    return sched


def select_pilot_items(domain, item_ids, count, seed=SEED):
    """Select a stable, order-independent item subset for compatibility pilots."""
    if count <= 0 or count >= len(item_ids):
        return list(item_ids)
    ranked = sorted(
        item_ids,
        key=lambda iid: _sha(f"pilot-items-v1|{seed}|{domain}|{iid}"),
    )
    return ranked[:count]


def cell_key(r):
    return (r["domain"], r["item_id"], r["model"], r["condition"], r["candidate_type"],
            r["repetition"], r["protocol"])


def load_successful(path, run_id=None):
    done = {}
    if os.path.exists(path):
        for line_no, line in enumerate(open(path, encoding="utf-8"), start=1):
            line = line.strip()
            if line:
                r = json.loads(line)
                if run_id is not None and r.get("run_id") != run_id:
                    raise RuntimeError(
                        f"{path}:{line_no} belongs to run_id={r.get('run_id')!r}, "
                        f"expected {run_id!r}; refusing to mix evidence"
                    )
                if r.get("score") is not None and r.get("error") is None:
                    key = cell_key(r)
                    if key in done:
                        raise RuntimeError(f"duplicate successful cell in {path}: {key}")
                    done[key] = r["score"]
    return done


def _normalise_call_result(result):
    if isinstance(result, dict):
        return {
            "raw_response": result.get("text") or "",
            "finish_reason": result.get("finish_reason"),
            "response_id": result.get("response_id"),
            "response_model": result.get("response_model"),
            "provider": result.get("provider"),
            "usage": result.get("usage"),
            "transport_attempt_count": result.get("transport_attempt_count"),
            "transport_errors": result.get("transport_errors") or [],
        }
    if isinstance(result, tuple) and len(result) == 2:
        return {"raw_response": result[0] or "", "finish_reason": result[1]}
    return {"raw_response": result or "", "finish_reason": None}


def _strict_score_json(text):
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return False
    return (
        isinstance(value, dict)
        and set(value) == {"score"}
        and isinstance(value["score"], (int, float))
        and not isinstance(value["score"], bool)
        and 0 <= value["score"] <= 100
    )


def _terminal_score_json(text):
    """Accept one-field score JSON only when it is the final response object."""
    if not isinstance(text, str):
        return False
    match = re.search(r"(\{[^{}]*\})\s*$", text, re.S)
    return bool(match and _strict_score_json(match.group(1)))


def _score_output_accepted(text, finish_reason, contract):
    if contract == "parsed":
        return True
    if finish_reason != "stop":
        return False
    if contract == "strict":
        return _strict_score_json(text)
    if contract == "terminal":
        return _terminal_score_json(text)
    raise ValueError(f"unknown score acceptance contract: {contract}")


def judge_once(prompt, model, protocol, key, call_fn, provider=None,
               max_tok=MAX_TOK, retry_tok=RETRY_TOK, expected_provider=None,
               expected_response_model=None, score_acceptance="parsed"):
    """Call a judge with one larger-budget retry and preserve both attempts.

    The shared CCC parser raises on malformed output. Parse exceptions are an
    expected retry trigger, not worker failures.
    """
    attempts = []
    for attempt_index, budget in enumerate((max_tok[protocol], retry_tok[protocol]), start=1):
        attempt = {
            "attempt": attempt_index,
            "max_tokens": budget,
            "provider_requested": provider,
            "raw_response": "",
            "finish_reason": None,
            "response_id": None,
            "response_model": None,
            "provider": None,
            "usage": None,
            "transport_attempt_count": None,
            "transport_errors": [],
            "call_error": None,
            "parse_error": None,
            "parsed": False,
            "identity_error": None,
        }
        try:
            result = call_fn(
                prompt, model, key, max_tokens=budget,
                return_meta=True, provider=provider,
            )
            attempt.update(_normalise_call_result(result))
        except Exception as e:
            attempt["call_error"] = f"{type(e).__name__}: {str(e)[:300]}"
            attempt["transport_attempt_count"] = getattr(e, "transport_attempt_count", None)
            attempt["transport_errors"] = getattr(e, "transport_errors", [])
            attempts.append(attempt)
            continue

        try:
            score = parse_score(attempt["raw_response"])
        except Exception as e:
            attempt["parse_error"] = f"{type(e).__name__}: {str(e)[:300]}"
            attempts.append(attempt)
            continue
        attempt["parsed"] = score is not None
        if score is not None and not _score_output_accepted(
                attempt["raw_response"], attempt["finish_reason"], score_acceptance):
            attempt["parse_error"] = (
                f"ValueError: response violates {score_acceptance!r} score-output contract"
            )
            attempt["parsed"] = False
            attempts.append(attempt)
            continue
        identity_errors = []
        if expected_provider and not _provider_identity_matches(
                expected_provider, attempt.get("provider")):
            identity_errors.append(
                f"provider={attempt.get('provider')!r}, expected {expected_provider!r}"
            )
        if (expected_response_model and
                attempt.get("response_model") != expected_response_model):
            identity_errors.append(
                f"response_model={attempt.get('response_model')!r}, "
                f"expected {expected_response_model!r}"
            )
        if identity_errors:
            attempt["identity_error"] = "; ".join(identity_errors)
            attempts.append(attempt)
            continue
        attempts.append(attempt)
        if score is not None:
            return score, attempt["raw_response"], None, attempt["finish_reason"], attempts

    final = attempts[-1]
    if any(a.get("identity_error") for a in attempts):
        err = "endpoint_identity_mismatch"
    elif any(a.get("finish_reason") == "content_filter" for a in attempts):
        err = "content_filtered"
    elif any(a.get("finish_reason") == "length" for a in attempts):
        err = "truncated_no_score"
    elif all(a.get("call_error") for a in attempts):
        err = "request_error"
    else:
        err = "unparseable_no_score"
    return None, final["raw_response"], err, final["finish_reason"], attempts


def worker(cell, domain, dom, order_index, key, call_fn, run_id,
           provider=None, max_tok=MAX_TOK, retry_tok=RETRY_TOK,
           endpoint_identities=None, score_acceptance="parsed"):
    iid, model, cond, cand, proto, rep = cell
    try:
        item = dom["_byid"][iid]
        prompt = dom["build"](item, cond, cand, proto)
        sha = _sha(prompt)
        expected = (endpoint_identities or {}).get(model) or {}
        score, raw, err, fin, attempts = judge_once(
            prompt, model, proto, key, call_fn, provider=provider,
            max_tok=max_tok, retry_tok=retry_tok,
            expected_provider=expected.get("provider") or provider,
            expected_response_model=expected.get("response_model"),
            score_acceptance=score_acceptance,
        )
        return ({"run_id": run_id, "domain": domain, "item_id": iid, "model": model,
                 "condition": cond,
                 "candidate_type": cand, "protocol": proto, "repetition": rep,
                 "order_index": order_index, "prompt_sha256": sha, "raw_response": raw,
                 "finish_reason": fin, "attempt_count": len(attempts), "attempts": attempts,
                 "provider_requested": provider, "score": score, "error": err,
                 "timestamp": time.time()}, prompt, sha)
    except Exception as e:
        return ({"run_id": run_id, "domain": domain, "item_id": iid, "model": model,
                 "condition": cond,
                 "candidate_type": cand, "protocol": proto, "repetition": rep,
                 "order_index": order_index, "prompt_sha256": None, "raw_response": "",
                 "finish_reason": None, "attempt_count": 0, "attempts": [],
                 "provider_requested": provider, "score": None,
                 "error": f"worker:{type(e).__name__}: {e}",
                 "timestamp": time.time()}, None, None)


def obs_path(domain, evidence_dir=RES, output_prefix=DEFAULT_OUTPUT_PREFIX):
    return os.path.join(evidence_dir, f"{output_prefix}_{domain}_obs.jsonl")


def prompts_path(domain, evidence_dir=RES, output_prefix=DEFAULT_OUTPUT_PREFIX):
    return os.path.join(evidence_dir, f"{output_prefix}_{domain}_prompts.jsonl")


def metadata_path(evidence_dir=RES, output_prefix=DEFAULT_OUTPUT_PREFIX):
    return os.path.join(evidence_dir, f"{output_prefix}_meta.json")


def completion_metadata_path(evidence_dir=RES, output_prefix=DEFAULT_OUTPUT_PREFIX):
    return os.path.join(evidence_dir, f"{output_prefix}_completion_meta.json")


def run_domain(domain, dom, models, protocols, key, call_fn, workers, resume, progress_secs,
               *, evidence_dir=RES, output_prefix=DEFAULT_OUTPUT_PREFIX, seed=SEED,
               run_id=DEFAULT_RUN_ID, provider=None, max_tok=MAX_TOK, retry_tok=RETRY_TOK,
               endpoint_identities=None, reps=REPS, score_acceptance="parsed"):
    os.makedirs(evidence_dir, exist_ok=True)
    dom["_byid"] = {dom["id"](x): x for x in dom["items"]}
    ids = [dom["id"](x) for x in dom["items"]]
    schedule = list(enumerate(
        build_schedule(domain, ids, models, protocols, seed=seed, reps=reps)
    ))
    op = obs_path(domain, evidence_dir, output_prefix)
    pp = prompts_path(domain, evidence_dir, output_prefix)
    done = load_successful(op, run_id=run_id) if resume else {}
    seen = set()
    if resume and os.path.exists(pp):
        seen = {json.loads(l)["sha256"] for l in open(pp, encoding="utf-8") if l.strip()}
    pending = [(oi, c) for oi, c in schedule
               if (domain, c[0], c[1], c[2], c[3], c[5], c[4]) not in done]
    mode = "a" if resume else "x"
    total = len(schedule)
    n_new = n_fail = 0
    start = last = time.time()
    print(f"[{domain}] {len(pending)} cells to do ({len(done)} done) of {total}, {workers} workers")
    with open(op, mode, encoding="utf-8") as osink, open(pp, mode, encoding="utf-8") as psink:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [
                ex.submit(
                    worker, c, domain, dom, oi, key, call_fn, run_id,
                    provider, max_tok, retry_tok, endpoint_identities, score_acceptance,
                )
                for oi, c in pending
            ]
            for fut in as_completed(futs):
                row, prompt, sha = fut.result()
                if sha is not None and sha not in seen:
                    psink.write(json.dumps({
                        "prompt_instrument": PROMPT_INSTRUMENT,
                        "sha256": sha,
                        "prompt": prompt,
                    }) + "\n"); psink.flush()
                    seen.add(sha)
                osink.write(json.dumps(row) + "\n"); osink.flush()
                n_fail += row["score"] is None
                n_new += row["score"] is not None
                now = time.time()
                if now - last >= progress_secs:
                    dc = len(done) + n_new + n_fail
                    rate = (n_new + n_fail) / (now - start) * 60
                    print(f"[{domain}] {(now-start)/60:5.1f}m | {dc}/{total} | +{n_new}/{n_fail}f "
                          f"| {rate:4.1f}/min | ETA ~{(total-dc)/max(rate,1e-9)/60:4.1f}h", flush=True)
                    last = now
    print(f"[{domain}] done: +{n_new} ok, {n_fail} failed this pass")


# --- Analysis (fail-closed; paired bare-conclusion harm + mechanism increments) ---------
def _disc(obs, domain, model, cond, ids, proto="score_only"):
    import statistics
    out = {}
    for iid in ids:
        cor = [obs.get((domain, iid, model, cond, "correct", rp, proto)) for rp in range(REPS)]
        wro = [obs.get((domain, iid, model, cond, "wrong_matching", rp, proto)) for rp in range(REPS)]
        if all(x is not None for x in cor) and all(x is not None for x in wro):
            out[iid] = statistics.mean(cor) - statistics.mean(wro)
    return out


def _ci(per, n=6000, seed=0):
    import statistics
    # Stable ordering makes the seeded bootstrap reproducible across processes.
    it = sorted(per)
    if not it:
        return float("nan"), float("nan"), float("nan"), 0
    r = random.Random(seed)
    ms = sorted(sum(per[r.choice(it)] for _ in it) / len(it) for _ in range(n))
    return statistics.mean(per.values()), ms[int(.025 * n)], ms[int(.975 * n)], len(it)


def _row_truncated(row):
    if row.get("finish_reason") == "length":
        return True
    return any(a.get("finish_reason") == "length" for a in row.get("attempts") or [])


def _row_content_filtered(row):
    if row.get("error") == "content_filtered" or row.get("finish_reason") == "content_filter":
        return True
    return any(a.get("finish_reason") == "content_filter"
               for a in row.get("attempts") or [])


def _collapse_rows(rows, run_id=None):
    row_run_ids = {row.get("run_id") for row in rows}
    non_null_run_ids = {value for value in row_run_ids if value is not None}
    has_legacy_rows = None in row_run_ids
    if has_legacy_rows and non_null_run_ids:
        raise RuntimeError(
            "evidence mixes legacy rows without run_id and namespaced rows; "
            "refusing to pool runs"
        )
    if len(non_null_run_ids) > 1:
        raise RuntimeError(
            f"evidence contains multiple run_ids={sorted(non_null_run_ids)!r}; "
            "refusing to pool runs"
        )
    if run_id is not None and non_null_run_ids and non_null_run_ids != {run_id}:
        observed = next(iter(non_null_run_ids))
        raise RuntimeError(
            f"evidence contains run_id={observed!r}; expected {run_id!r}"
        )

    grouped = {}
    for row in rows:
        grouped.setdefault(cell_key(row), []).append(row)
    final = {}
    for key, versions in grouped.items():
        successes = [r for r in versions if r.get("score") is not None and r.get("error") is None]
        if len(successes) > 1:
            raise RuntimeError(f"duplicate successful cell: {key}")
        final[key] = successes[0] if successes else max(versions, key=lambda r: r.get("timestamp", 0))
    return final


def analyse(domains, floor_frac=0.75, *, evidence_dir=RES,
            output_prefix=DEFAULT_OUTPUT_PREFIX, run_id=None,
            expected_models=None, expected_items=None,
            balance_gap=DEFAULT_BALANCE_GAP, protocol="score_only"):
    if protocol not in MAX_TOK:
        raise ValueError(f"unknown analysis protocol: {protocol}")
    for domain in domains:
        op = obs_path(domain, evidence_dir, output_prefix)
        if not os.path.exists(op):
            print(f"[{domain}] no evidence"); continue
        with open(op, encoding="utf-8") as source:
            rows = [json.loads(line) for line in source if line.strip()]
        final = _collapse_rows(rows, run_id=run_id)
        obs = {key: r["score"] for key, r in final.items()
               if r.get("score") is not None and r.get("error") is None}
        ids = list((expected_items or {}).get(domain) or sorted({r["item_id"] for r in rows}))
        models = list(expected_models or sorted({r["model"] for r in rows}))
        floor = math.ceil(len(ids) * floor_frac)
        total_per_stratum = len(ids) * REPS
        balance = {}
        print(f"\n=== {domain} ({len(ids)} items, floor {floor}, protocol={protocol}) ===")
        print("  completion before estimates (successful unique cells / expected):")
        for model in models:
            rates, length_rates, filter_rates = {}, {}, {}
            for cond in COND_IDS:
                bits = []
                for cand in CANDIDATES:
                    selected = [
                        final.get((domain, iid, model, cond, cand, rep, protocol))
                        for iid in ids for rep in range(REPS)
                    ]
                    success = sum(r is not None and r.get("score") is not None
                                  and r.get("error") is None for r in selected)
                    truncated = sum(r is not None and r.get("score") is None
                                    and _row_truncated(r) for r in selected)
                    content_filtered = sum(r is not None and r.get("score") is None
                                           and _row_content_filtered(r) for r in selected)
                    rates[(cond, cand)] = success / total_per_stratum if total_per_stratum else 0
                    length_rates[(cond, cand)] = (
                        truncated / total_per_stratum if total_per_stratum else 0
                    )
                    filter_rates[(cond, cand)] = (
                        content_filtered / total_per_stratum if total_per_stratum else 0
                    )
                    filter_note = f",cf={content_filtered}" if content_filtered else ""
                    bits.append(f"{cand}={success}/{total_per_stratum}{filter_note}")
                print(f"    {model:36s} {cond:18s} " + " ".join(bits))
            primary_rates = [rates[(cond, cand)]
                             for cond in ("no_injection", "answer_only")
                             for cand in CANDIDATES]
            completion_gap = max(primary_rates) - min(primary_rates)
            base_length = sum(length_rates[("no_injection", cand)] for cand in CANDIDATES) / 2
            injected_length = sum(length_rates[("answer_only", cand)] for cand in CANDIDATES) / 2
            length_delta = injected_length - base_length
            base_filter = sum(filter_rates[("no_injection", cand)] for cand in CANDIDATES) / 2
            injected_filter = sum(filter_rates[("answer_only", cand)] for cand in CANDIDATES) / 2
            filter_delta = injected_filter - base_filter
            balance[model] = (completion_gap <= balance_gap
                              and abs(length_delta) <= balance_gap
                              and abs(filter_delta) <= balance_gap)
            print(f"      primary balance: completion_gap={completion_gap:.1%}, "
                  f"length_delta={length_delta:+.1%}, "
                  f"content_filter_delta={filter_delta:+.1%} -> "
                  f"{'OK' if balance[model] else 'FAIL (unmeasurable)'}")

        print(f"  {'model':36s} {'bare-harm [95% CI]':>26s}  {'prov+':>8s} {'rat+':>8s}")
        for m in models:
            base = _disc(obs, domain, m, "no_injection", ids, proto=protocol)
            bare = _disc(obs, domain, m, "answer_only", ids, proto=protocol)
            full = _disc(obs, domain, m, "full_rationale", ids, proto=protocol)
            solv = _disc(obs, domain, m, "solver_rationale", ids, proto=protocol)
            harm = {i: base[i] - bare[i] for i in set(base) & set(bare)}
            mn, lo, hi, n = _ci(harm)
            prov = {i: (base[i]-solv[i]) - (base[i]-full[i]) for i in set(solv) & set(full) & set(base)}
            rat = {i: (base[i]-full[i]) - (base[i]-bare[i]) for i in set(full) & set(bare) & set(base)}
            measurable = n >= floor and balance.get(m, False)
            if not measurable:
                print(f"  {m:36s} {'NA (balance/completeness gate)':>26s} n={n:2d} "
                      f"{'unmeasurable':12s} {'NA':>7s} {'NA':>7s}")
                continue
            tag = "SUPPORTED" if lo > 0 else "ns"
            pm = _ci(prov)[0] if prov else float("nan")
            rm = _ci(rat)[0] if rat else float("nan")
            print(f"  {m:36s} {mn:+7.2f} [{lo:+7.2f},{hi:+7.2f}] n={n:2d} "
                  f"{tag:12s} {pm:+7.1f} {rm:+7.1f}")


def _stub(prompt, model, key, max_tokens=64, return_finish=False,
          return_meta=False, provider=None):
    h = int(hashlib.sha256((prompt + model).encode()).hexdigest(), 16)
    injected = any(s in prompt for s in ("Reference note:", "External", "Additional analysis:",
                                         "Solver", "reference answer", "Reference answer"))
    base = 80 if h % 2 else 70
    out = json.dumps({"score": max(0, min(100, base - (25 if injected else 0) + h % 12))})
    if return_meta:
        return {
            "text": out,
            "finish_reason": "stop",
            "response_id": "stub",
            "response_model": model,
            "provider": provider or "stub",
            "usage": None,
            "transport_attempt_count": 1,
            "transport_errors": [],
        }
    return (out, "stop") if return_finish else out


def _instrument_hashes():
    names = [
        "run_ccc_frontier.py", "judge_integrity_real.py",
        "PREREG_ccc_frontier_v3.md", "PREREG_ccc_openrouter_panel.md",
        "PREREG_ccc_openrouter_pilot_v2.md", "run_ccc_openweight_pilot.ps1",
        "PREREG_ccc_openrouter_kimi_native_pilot_v1.md",
        "PREREG_ccc_openrouter_kimi_native_v1.md", "run_ccc_kimi_native.ps1",
        "PREREG_ccc_openrouter_openweight_full_v2.md", "run_ccc_openweight_full_v2.ps1",
        "provenance_injection_harness.py",
        "run_provenance_injection.py", "ccc_code_items.py", "ccc_code_runner.py",
        "run_ccc_codedomain.py", "ccc_sql_items.py", "run_ccc_sql.py",
    ]
    return {name: _sha_file(os.path.join(HERE, name)) for name in names}


def _write_json_new(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "x", encoding="utf-8") as sink:
        json.dump(value, sink, indent=1, sort_keys=True)


def build_completion_metadata(domains, *, study, evidence_dir, output_prefix, run_id,
                              expected_models, expected_items, protocols,
                              balance_gap=DEFAULT_BALANCE_GAP, reps=REPS):
    """Build a content-addressed, offline audit summary for a completed run."""
    if len(protocols) != 1 or protocols[0] not in MAX_TOK:
        raise ValueError("completion metadata requires exactly one known protocol per namespace")
    protocol = protocols[0]
    report = {
        "study": study,
        "runner_version": RUNNER_VERSION,
        "run_id": run_id,
        "created_at": _utc_now(),
        "phase_2_executed": any(p != "score_only" for p in protocols),
        "analysis_protocol": protocol,
        "balance_gap": balance_gap,
        "domains": {},
    }
    overall_ok = True
    required_attempt_keys = {
        "attempt", "max_tokens", "raw_response", "finish_reason", "parsed",
        "call_error", "parse_error", "identity_error",
    }
    for domain in domains:
        op = obs_path(domain, evidence_dir, output_prefix)
        pp = prompts_path(domain, evidence_dir, output_prefix)
        with open(op, encoding="utf-8") as source:
            rows = [json.loads(line) for line in source if line.strip()]
        with open(pp, encoding="utf-8") as source:
            prompt_rows = [json.loads(line) for line in source if line.strip()]
        final = _collapse_rows(rows, run_id=run_id)
        ids = list(expected_items[domain])
        expected_cells = (len(ids) * len(expected_models) * len(COND_IDS)
                          * len(CANDIDATES) * len(protocols) * reps)
        expected_prompts = len(ids) * len(COND_IDS) * len(CANDIDATES) * len(protocols)
        successes = sum(r.get("score") is not None and r.get("error") is None
                        for r in final.values())
        attempt_histogram = {}
        error_counts = {}
        total_judge_attempts = 0
        total_transport_attempts = 0
        reasoning_usage_records = 0
        provider_response_attempts = 0
        max_reasoning_tokens = 0
        attempt_cost = 0.0
        attempt_schema_ok = True
        for row in rows:
            attempts = row.get("attempts") or []
            count = len(attempts)
            attempt_histogram[str(count)] = attempt_histogram.get(str(count), 0) + 1
            total_judge_attempts += count
            if row.get("error"):
                error_counts[row["error"]] = error_counts.get(row["error"], 0) + 1
            for attempt in attempts:
                attempt_schema_ok &= required_attempt_keys <= set(attempt)
                total_transport_attempts += int(attempt.get("transport_attempt_count") or 0)
                if not attempt.get("call_error"):
                    provider_response_attempts += 1
                usage = attempt.get("usage") or {}
                details = usage.get("completion_tokens_details") or {}
                reasoning_tokens = details.get("reasoning_tokens")
                if reasoning_tokens is not None:
                    reasoning_usage_records += 1
                    max_reasoning_tokens = max(max_reasoning_tokens, int(reasoning_tokens))
                if usage.get("cost") is not None:
                    attempt_cost += float(usage["cost"])

        prompt_map = {}
        prompt_manifest_ok = True
        for record in prompt_rows:
            sha = record.get("sha256")
            prompt = record.get("prompt")
            if not sha or not isinstance(prompt, str) or _sha(prompt) != sha or sha in prompt_map:
                prompt_manifest_ok = False
            if sha:
                prompt_map[sha] = prompt
        referenced = {r.get("prompt_sha256") for r in final.values()
                      if r.get("prompt_sha256")}
        prompt_manifest_ok &= referenced <= set(prompt_map)

        strata = {}
        total_per_stratum = len(ids) * reps
        primary_rates = {}
        primary_truncation = {}
        for model in expected_models:
            strata[model] = {}
            for condition in COND_IDS:
                strata[model][condition] = {}
                for candidate in CANDIDATES:
                    selected = [
                        final.get((domain, iid, model, condition, candidate, rep,
                                   protocol))
                        for iid in ids for rep in range(reps)
                    ]
                    success = sum(r is not None and r.get("score") is not None
                                  and r.get("error") is None for r in selected)
                    truncated = sum(r is not None and r.get("score") is None
                                    and _row_truncated(r) for r in selected)
                    content_filtered = sum(r is not None and r.get("score") is None
                                           and _row_content_filtered(r) for r in selected)
                    strata[model][condition][candidate] = {
                        "successful": success,
                        "expected": total_per_stratum,
                        "truncated": truncated,
                        "content_filtered": content_filtered,
                    }
                    if condition in ("no_injection", "answer_only"):
                        primary_rates[(model, condition, candidate)] = (
                            success / total_per_stratum if total_per_stratum else 0
                        )
                        primary_truncation[(model, condition, candidate)] = (
                            truncated / total_per_stratum if total_per_stratum else 0
                        )
        primary_filters = {
            (model, condition, candidate):
                strata[model][condition][candidate]["content_filtered"] / total_per_stratum
                if total_per_stratum else 0
            for model in expected_models
            for condition in ("no_injection", "answer_only")
            for candidate in CANDIDATES
        }
        for model in expected_models:
            rates = [primary_rates[(model, condition, candidate)]
                     for condition in ("no_injection", "answer_only")
                     for candidate in CANDIDATES]
            completion_gap = max(rates) - min(rates)
            base_truncation = sum(primary_truncation[(model, "no_injection", candidate)]
                                  for candidate in CANDIDATES) / 2
            injected_truncation = sum(primary_truncation[(model, "answer_only", candidate)]
                                      for candidate in CANDIDATES) / 2
            base_filter = sum(primary_filters[(model, "no_injection", candidate)]
                              for candidate in CANDIDATES) / 2
            injected_filter = sum(primary_filters[(model, "answer_only", candidate)]
                                  for candidate in CANDIDATES) / 2
            strata[model]["primary_balance"] = {
                "completion_gap": completion_gap,
                "truncation_delta": injected_truncation - base_truncation,
                "content_filter_delta": injected_filter - base_filter,
                "passed": (completion_gap <= balance_gap and
                           abs(injected_truncation - base_truncation) <= balance_gap and
                           abs(injected_filter - base_filter) <= balance_gap),
            }

        domain_ok = (len(final) == expected_cells and len(prompt_map) == expected_prompts
                     and prompt_manifest_ok and attempt_schema_ok)
        strict_score_cells = sum(
            r.get("score") is not None and r.get("error") is None
            and _strict_score_json(r.get("raw_response"))
            for r in final.values()
        )
        terminal_score_cells = sum(
            r.get("score") is not None and r.get("error") is None
            and r.get("finish_reason") == "stop"
            and _terminal_score_json(r.get("raw_response"))
            for r in final.values()
        )
        overall_ok &= domain_ok
        report["domains"][domain] = {
            "expected_cells": expected_cells,
            "raw_rows": len(rows),
            "unique_cells": len(final),
            "successful_cells": successes,
            "failed_cells": len(final) - successes,
            "expected_unique_prompts": expected_prompts,
            "unique_prompts": len(prompt_map),
            "prompt_manifest_ok": prompt_manifest_ok,
            "attempt_schema_ok": bool(attempt_schema_ok),
            "attempt_count_histogram": attempt_histogram,
            "total_judge_attempts": total_judge_attempts,
            "total_transport_attempts": total_transport_attempts,
            "reasoning_usage_records": reasoning_usage_records,
            "provider_response_attempts": provider_response_attempts,
            "max_reasoning_tokens": max_reasoning_tokens,
            "attempt_cost": attempt_cost,
            "strict_score_cells": strict_score_cells,
            "terminal_score_cells": terminal_score_cells,
            "error_counts": error_counts,
            "strata": strata,
            "observation_sha256": _sha_file(op),
            "prompt_manifest_sha256": _sha_file(pp),
            "complete": domain_ok,
        }
    report["evidence_complete"] = bool(overall_ok)
    return report


def add_pilot_eligibility(report, reasoning_ceiling=None, score_acceptance="strict"):
    """Add a strict score-output compatibility gate without inferential claims."""
    eligible = True
    for domain_report in report["domains"].values():
        if score_acceptance == "parsed":
            accepted_cells = domain_report["successful_cells"]
        elif score_acceptance == "strict":
            accepted_cells = domain_report["strict_score_cells"]
        elif score_acceptance == "terminal":
            accepted_cells = domain_report["terminal_score_cells"]
        else:
            raise ValueError(f"unknown pilot score acceptance: {score_acceptance}")
        domain_eligible = (
            domain_report["complete"]
            and domain_report["successful_cells"] == domain_report["expected_cells"]
            and accepted_cells == domain_report["expected_cells"]
            and not domain_report["error_counts"]
        )
        if reasoning_ceiling is not None:
            domain_eligible &= (
                domain_report["reasoning_usage_records"]
                == domain_report["provider_response_attempts"]
                and domain_report["max_reasoning_tokens"] <= reasoning_ceiling
            )
        domain_report["pilot_eligible"] = bool(domain_eligible)
        eligible &= domain_eligible
    report["compatibility_pilot"] = True
    report["pilot_reasoning_ceiling"] = reasoning_ceiling
    report["pilot_score_acceptance"] = score_acceptance
    report["pilot_eligible"] = bool(eligible)
    return report


def print_pilot_report(report):
    print("\n=== compatibility pilot (completion only; no effect estimates) ===")
    for domain, domain_report in report["domains"].items():
        print(
            f"  {domain:5s}: {domain_report['successful_cells']}/"
            f"{domain_report['expected_cells']} parsed; "
            f"strict={domain_report['strict_score_cells']}/"
            f"{domain_report['expected_cells']}; "
            f"terminal={domain_report['terminal_score_cells']}/"
            f"{domain_report['expected_cells']}; "
            f"reasoning_max={domain_report['max_reasoning_tokens']}; "
            f"cost=${domain_report['attempt_cost']:.6f}; "
            f"errors={domain_report['error_counts'] or '{}'}; "
            f"{'PASS' if domain_report.get('pilot_eligible') else 'FAIL'}"
        )
    print(
        "  graduation: "
        + ("PASS - eligible for a separately frozen full run"
           if report.get("pilot_eligible")
           else "FAIL - do not launch a full run under this configuration")
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="", help="comma-separated OpenRouter aliases")
    ap.add_argument("--domains", default="arith,code,sql")
    ap.add_argument("--protocols", default="score_only")
    modes = ap.add_mutually_exclusive_group()
    modes.add_argument("--check-models", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--wiring-check", action="store_true")
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--resume", action="store_true")
    modes.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--stub", action="store_true")
    ap.add_argument("--approve-api-calls", action="store_true",
                    help="explicit operator approval required before any live model call")
    ap.add_argument("--study", default=DEFAULT_STUDY)
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID)
    ap.add_argument("--evidence-dir", default=RES)
    ap.add_argument("--output-prefix", default=DEFAULT_OUTPUT_PREFIX)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--provider", default="",
                    help="fixed OpenRouter provider slug; fallbacks are disabled")
    ap.add_argument("--score-max-tokens", type=int, default=MAX_TOK["score_only"])
    ap.add_argument("--score-retry-tokens", type=int, default=RETRY_TOK["score_only"])
    reasoning = ap.add_mutually_exclusive_group()
    reasoning.add_argument("--reasoning-max-tokens", type=int, default=0,
                           help="fixed OpenRouter reasoning-token ceiling; 0 uses provider default")
    reasoning.add_argument("--reasoning-effort", default="",
                           choices=("none", "minimal", "low", "medium", "high", "xhigh", "max"),
                           help="fixed OpenRouter reasoning effort for effort-only models")
    ap.add_argument("--structured-score-output", action="store_true",
                    help="require strict JSON-schema score output from the pinned provider")
    ap.add_argument("--score-acceptance", default="parsed",
                    choices=("parsed", "strict", "terminal"),
                    help="accepted response contract; terminal requires final score JSON and stop")
    ap.add_argument("--allow-unadvertised-provider-parameters", action="store_true",
                    help="pin the provider but do not require its capability advertisement")
    ap.add_argument("--balance-gap", type=float, default=DEFAULT_BALANCE_GAP)
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    ap.add_argument("--progress-secs", type=int, default=600)
    ap.add_argument("--transport-retries", type=int, default=5,
                    help="bounded HTTP attempts inside each judge attempt")
    ap.add_argument("--repetitions", type=int, default=REPS,
                    help="repetitions per item/condition/candidate (pilot: 1; full: 3)")
    ap.add_argument("--pilot-items-per-domain", type=int, default=0,
                    help="stable item subset size; nonzero marks a compatibility pilot")
    ap.add_argument("--pilot-reasoning-ceiling", type=int, default=-1,
                    help="graduation ceiling for observed reasoning usage; -1 disables")
    a = ap.parse_args()
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    domains = [d.strip() for d in a.domains.split(",") if d.strip()]
    protocols = [p.strip() for p in a.protocols.split(",") if p.strip()]
    evidence_dir = os.path.abspath(a.evidence_dir)
    provider = a.provider.strip() or None
    max_tok = dict(MAX_TOK)
    max_tok["score_only"] = a.score_max_tokens
    retry_tok = dict(RETRY_TOK)
    retry_tok["score_only"] = a.score_retry_tokens
    reasoning_policy = None
    if a.reasoning_max_tokens:
        reasoning_policy = {"max_tokens": a.reasoning_max_tokens, "exclude": True}
    elif a.reasoning_effort:
        reasoning_policy = {"effort": a.reasoning_effort, "exclude": True}
    response_format = SCORE_RESPONSE_FORMAT if a.structured_score_output else None

    if len(models) != len(set(models)):
        print("ERROR: duplicate model aliases are not allowed."); sys.exit(2)
    unknown_domains = [d for d in domains if d not in DOMAINS]
    unknown_protocols = [p for p in protocols if p not in MAX_TOK]
    if unknown_domains or unknown_protocols:
        print(f"ERROR: unknown domains={unknown_domains} protocols={unknown_protocols}."); sys.exit(2)
    if len(protocols) != 1:
        print("ERROR: use exactly one protocol per evidence namespace."); sys.exit(2)
    analysis_protocol = protocols[0]
    if a.study.startswith("openweight") and protocols != ["score_only"]:
        print("ERROR: the open-weight Phase-1 run is score_only only."); sys.exit(2)
    if a.score_max_tokens <= 0 or a.score_retry_tokens < a.score_max_tokens:
        print("ERROR: token budgets require 0 < primary <= retry."); sys.exit(2)
    if a.reasoning_max_tokens < 0:
        print("ERROR: --reasoning-max-tokens must be non-negative."); sys.exit(2)
    if not 0 <= a.balance_gap <= 1:
        print("ERROR: --balance-gap must be in [0, 1]."); sys.exit(2)
    if a.workers < 1:
        print("ERROR: --workers must be positive."); sys.exit(2)
    if not 1 <= a.transport_retries <= 5:
        print("ERROR: --transport-retries must be in [1, 5]."); sys.exit(2)
    if not 1 <= a.repetitions <= REPS:
        print(f"ERROR: --repetitions must be in [1, {REPS}]."); sys.exit(2)
    if a.pilot_items_per_domain < 0:
        print("ERROR: --pilot-items-per-domain must be non-negative."); sys.exit(2)
    if a.pilot_reasoning_ceiling < -1:
        print("ERROR: --pilot-reasoning-ceiling must be -1 or non-negative."); sys.exit(2)

    doms = {d: DOMAINS[d]() for d in domains}
    compatibility_pilot = bool(a.pilot_items_per_domain or a.repetitions != REPS)
    selected_item_ids = {}
    for domain, dom in doms.items():
        all_ids = [dom["id"](x) for x in dom["items"]]
        chosen = select_pilot_items(
            domain, all_ids, a.pilot_items_per_domain, seed=a.seed,
        )
        selected_item_ids[domain] = chosen
        chosen_set = set(chosen)
        dom["items"] = [x for x in dom["items"] if dom["id"](x) in chosen_set]
    expected_items = {d: [doms[d]["id"](x) for x in doms[d]["items"]] for d in domains}
    mp = metadata_path(evidence_dir, a.output_prefix)
    cp = completion_metadata_path(evidence_dir, a.output_prefix)

    if a.analyse_only:
        meta = {}
        if os.path.exists(mp):
            with open(mp, encoding="utf-8") as source:
                meta = json.load(source)
        legacy_metadata = bool(meta) and "run_id" not in meta
        meta_protocols = meta.get("protocols") or protocols
        if len(meta_protocols) != 1 or meta_protocols[0] not in MAX_TOK:
            print("ERROR: metadata must identify exactly one known analysis protocol."); sys.exit(2)
        if meta.get("compatibility_pilot"):
            if not os.path.exists(cp):
                print(f"ERROR: pilot completion metadata does not exist: {cp}"); sys.exit(5)
            with open(cp, encoding="utf-8") as source:
                print_pilot_report(json.load(source))
        else:
            if legacy_metadata:
                print(
                    "legacy evidence metadata: requiring an all-null run_id namespace "
                    "and inferring models/items independently per domain"
                )
            analyse(
                domains, evidence_dir=evidence_dir, output_prefix=a.output_prefix,
                run_id=None if legacy_metadata else meta.get("run_id", a.run_id),
                expected_models=(None if legacy_metadata
                                 else meta.get("models") or models or None),
                expected_items=None if legacy_metadata else expected_items,
                balance_gap=meta.get("balance_gap", a.balance_gap),
                protocol=meta_protocols[0],
            )
        return

    for d in domains:
        doms[d]["gate"]()
    total = sum(len(doms[d]["items"]) * len(models) * len(COND_IDS) * len(CANDIDATES) * len(protocols) * a.repetitions
                for d in domains)
    print(f"{a.study} plan: domains={domains} models={len(models)} protocols={protocols} "
          f"seed={a.seed} schedule={SCHEDULE_VERSION} -> {total} judge cells")

    live_mode = a.check_models or a.run or a.resume
    if live_mode and not a.stub and not a.approve_api_calls:
        print("ERROR: no API call made. Pass --approve-api-calls only after reviewing the "
              "panel, provider, budgets, evidence paths, and cost.")
        sys.exit(4)
    if live_mode and not a.stub and a.study.startswith("openweight") and not provider:
        print("ERROR: open-weight confirmatory calls require a fixed --provider route.")
        sys.exit(2)

    if a.check_models:
        if not models:
            print("ERROR: --models is required."); sys.exit(2)
        call_fn, key = _stub, "STUB"
        if not a.stub:
            loaded = load_env(); key = os.environ.get("OPENROUTER_API_KEY")
            if loaded: print("loaded from .env:", ", ".join(loaded))
            if not key:
                print("ERROR: OPENROUTER_API_KEY not found. No API call made."); sys.exit(2)
            from judge_integrity_real import call_openrouter
            call_fn = functools.partial(
                call_openrouter, reasoning=reasoning_policy,
                response_format=response_format,
                provider_require_parameters=not a.allow_unadvertised_provider_parameters,
                retries=a.transport_retries,
            )
        validated, _ = check_models(
            models, key, call_fn=call_fn, provider=provider,
            max_tok=max_tok, retry_tok=retry_tok, protocol=analysis_protocol,
            score_acceptance=a.score_acceptance,
        )
        if validated != models:
            sys.exit(3)
        return

    if a.dry_run:
        for d in domains:
            dom = doms[d]; it0 = dom["items"][0]
            print(f"\n--- {d} sample bare-conclusion {analysis_protocol} prompt ---")
            print(dom["build"](it0, "answer_only", "wrong_matching", analysis_protocol)[:700])
        return

    if a.wiring_check:
        wiring_models = models or ["stub/a", "stub/b"]
        wiring_prefix = f"{a.output_prefix}_wiring_{os.getpid()}"
        for d in domains:
            run_domain(
                d, doms[d], wiring_models, protocols, "STUB", _stub, a.workers,
                resume=False, progress_secs=a.progress_secs,
                evidence_dir=evidence_dir, output_prefix=wiring_prefix, seed=a.seed,
                run_id=f"{a.run_id}_wiring", provider="stub",
                max_tok=max_tok, retry_tok=retry_tok, reps=a.repetitions,
                score_acceptance=a.score_acceptance,
            )
        if compatibility_pilot:
            expected_domain_cells = {
                domain: (len(expected_items[domain]) * len(wiring_models)
                         * len(COND_IDS) * len(CANDIDATES) * len(protocols)
                         * a.repetitions)
                for domain in domains
            }
            for domain in domains:
                with open(obs_path(domain, evidence_dir, wiring_prefix), encoding="utf-8") as source:
                    rows = [json.loads(line) for line in source if line.strip()]
                if (len(rows) != expected_domain_cells[domain]
                        or any(row.get("score") is None for row in rows)):
                    raise RuntimeError(f"pilot wiring check failed for {domain}")
                print(f"[{domain}] pilot wiring OK: {len(rows)} balanced stub cells")
        else:
            analyse(
                domains, evidence_dir=evidence_dir, output_prefix=wiring_prefix,
                run_id=f"{a.run_id}_wiring", expected_models=wiring_models,
                expected_items=expected_items, balance_gap=a.balance_gap,
                protocol=analysis_protocol,
            )
        for d in domains:
            for path in (obs_path(d, evidence_dir, wiring_prefix),
                         prompts_path(d, evidence_dir, wiring_prefix)):
                try: os.remove(path)
                except OSError: pass
        print("\nwiring-check complete (stub; throwaway evidence removed)")
        return

    if a.run or a.resume:
        if not models:
            print("ERROR: --models is required for a run."); sys.exit(2)

        git_commit, git_dirty = _git_state()
        config = {
            "study": a.study,
            "runner_version": RUNNER_VERSION,
            "run_id": a.run_id,
            "prompt_instrument": PROMPT_INSTRUMENT,
            "schedule_version": SCHEDULE_VERSION,
            "seed": a.seed,
            "reps": a.repetitions,
            "compatibility_pilot": compatibility_pilot,
            "pilot_items_per_domain": a.pilot_items_per_domain,
            "pilot_reasoning_ceiling": a.pilot_reasoning_ceiling,
            "selected_item_ids": selected_item_ids,
            "models": models,
            "domains": domains,
            "protocols": protocols,
            "conditions": COND_IDS,
            "candidates": CANDIDATES,
            "frozen_items": True,
            "workers": a.workers,
            "transport_retries": a.transport_retries,
            "stub": bool(a.stub),
            "temperature": 0,
            "reasoning_policy": reasoning_policy or "provider_default",
            "structured_score_output": bool(a.structured_score_output),
            "score_acceptance": a.score_acceptance,
            "provider_route": provider,
            "provider_fallbacks": False if provider else None,
            "provider_require_parameters": not a.allow_unadvertised_provider_parameters,
            "max_tok": max_tok,
            "retry_tok": retry_tok,
            "balance_gap": a.balance_gap,
            "python": sys.version.split()[0],
            "instrument_sha256": _instrument_hashes(),
            "completion_metadata": os.path.basename(cp),
        }
        config_sha = _sha(json.dumps(config, sort_keys=True, separators=(",", ":")))
        targets = [mp, cp]
        for d in domains:
            targets.extend((obs_path(d, evidence_dir, a.output_prefix),
                            prompts_path(d, evidence_dir, a.output_prefix)))

        prior_meta = None
        if a.run:
            existing = [path for path in targets if os.path.exists(path)]
            if existing:
                print("ERROR: --run will not overwrite existing evidence. Use a fresh namespace "
                      f"or --resume after verifying metadata. Existing: {existing}")
                sys.exit(5)
        else:
            if not os.path.exists(mp):
                print(f"ERROR: resume metadata does not exist: {mp}"); sys.exit(5)
            if os.path.exists(cp):
                print(f"ERROR: completion metadata already exists; this run is finalized: {cp}")
                sys.exit(5)
            with open(mp, encoding="utf-8") as source:
                prior_meta = json.load(source)
            if prior_meta.get("config_sha256") != config_sha:
                print("ERROR: resume configuration does not match the frozen run metadata; "
                      "start a new evidence namespace instead.")
                sys.exit(5)

        call_fn, key = _stub, "STUB"
        if not a.stub:
            loaded = load_env(); key = os.environ.get("OPENROUTER_API_KEY")
            if loaded: print("loaded from .env:", ", ".join(loaded))
            if not key:
                print("ERROR: OPENROUTER_API_KEY not found. No API call made."); sys.exit(2)
            from judge_integrity_real import call_openrouter
            call_fn = functools.partial(
                call_openrouter, reasoning=reasoning_policy,
                response_format=response_format,
                provider_require_parameters=not a.allow_unadvertised_provider_parameters,
                retries=a.transport_retries,
            )
        validated, preflight = check_models(
            models, key, call_fn=call_fn, provider=provider,
            max_tok=max_tok, retry_tok=retry_tok, protocol=analysis_protocol,
            score_acceptance=a.score_acceptance,
        )
        missing = [model for model in models if model not in validated]
        if missing:
            print(f"ERROR: preflight score parsing failed for {missing}. Aborting before any "
                  "scored cell. Amend budgets/provider and use a new run namespace.")
            sys.exit(3)
        endpoint_identities = {
            record["model"]: {
                "response_model": record["resolved_endpoint"]["response_model"],
                # v3 freezes the provider observed in preflight even when the
                # caller did not supply a single provider route for the panel.
                "provider": record["resolved_endpoint"]["provider"],
            }
            for record in preflight
        }
        if a.resume and prior_meta.get("endpoint_identities") != endpoint_identities:
            print("ERROR: the resolved model/provider identity differs from the frozen run "
                  "metadata. No scored cell was called; use a new evidence namespace.")
            sys.exit(3)

        if a.run:
            metadata = dict(config)
            metadata.update({
                "config_sha256": config_sha,
                "runner_commit": git_commit,
                "runner_git_dirty": git_dirty,
                "created_at": _utc_now(),
                "evidence_dir": evidence_dir,
                "output_prefix": a.output_prefix,
                "preflight": preflight,
                "endpoint_identities": endpoint_identities,
            })
            _write_json_new(mp, metadata)
        else:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            resume_preflight = os.path.join(
                evidence_dir, f"{a.output_prefix}_resume_preflight_{stamp}.json",
            )
            _write_json_new(resume_preflight, {
                "run_id": a.run_id,
                "config_sha256": config_sha,
                "created_at": _utc_now(),
                "preflight": preflight,
                "endpoint_identities": endpoint_identities,
            })

        for d in domains:
            run_domain(
                d, doms[d], models, protocols, key, call_fn, a.workers,
                resume=a.resume, progress_secs=a.progress_secs,
                evidence_dir=evidence_dir, output_prefix=a.output_prefix, seed=a.seed,
                run_id=a.run_id, provider=provider, max_tok=max_tok, retry_tok=retry_tok,
                endpoint_identities=endpoint_identities, reps=a.repetitions,
                score_acceptance=a.score_acceptance,
            )
        completion = build_completion_metadata(
            domains, study=a.study, evidence_dir=evidence_dir,
            output_prefix=a.output_prefix, run_id=a.run_id,
            expected_models=models, expected_items=expected_items,
            protocols=protocols, balance_gap=a.balance_gap, reps=a.repetitions,
        )
        if compatibility_pilot:
            add_pilot_eligibility(
                completion,
                reasoning_ceiling=(a.pilot_reasoning_ceiling
                                   if a.pilot_reasoning_ceiling >= 0 else None),
                score_acceptance=a.score_acceptance,
            )
        completion["config_sha256"] = config_sha
        completion["initial_metadata_sha256"] = _sha_file(mp)
        _write_json_new(cp, completion)
        if compatibility_pilot:
            print_pilot_report(completion)
        else:
            analyse(
                domains, evidence_dir=evidence_dir, output_prefix=a.output_prefix,
                run_id=a.run_id, expected_models=models, expected_items=expected_items,
                balance_gap=a.balance_gap, protocol=analysis_protocol,
            )
        return

    ap.print_help()


if __name__ == "__main__":
    main()
