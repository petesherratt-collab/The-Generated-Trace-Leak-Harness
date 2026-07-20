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
import hashlib
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _load_env import load_env
from provenance_injection_harness import parse_score

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

# v3 (confirmatory instrument). History: runs 1-2 (2026-07-19) VOID for 60/240 truncation;
# v2 (seed 811529437) EXPLORATORY ONLY -- valid scores for the three measurable judges but not
# confirmatory: its retry path was dead (never exercised) and its schedule used a per-process
# salted hash(domain), so the recorded seed did not reproduce ordering. v3 fixes both (working
# retry; stable schedule hash) and uses a fresh seed + namespace. See PREREG Amendment 3.
SEED = 305774821                     # v3 fresh seed (v2 used 811529437; void runs 619273400)
STUDY_TAG = "ccc_frontier_v3"        # fresh evidence filenames
REPS = 3
DEFAULT_WORKERS = 4                  # conservative (frontier endpoints, tighter rate limits)
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


# --- OpenRouter model preflight (validates aliases + reports pricing) --------------------
def check_models(models, key):
    from judge_integrity_real import call_openrouter
    print("preflight: validating model aliases (one trivial call each)")
    ok = []
    for m in models:
        try:
            # give the reasoning models room to reach the verdict, matching the real run
            r = call_openrouter('Reply with only: {"score": 100}', m, key,
                                max_tokens=MAX_TOK["score_only"])
            parse_ok = parse_score(r) is not None
            print(f"  {'OK  ' if parse_ok else 'FAIL'} {m}  "
                  f"(responded; score-parse={'yes' if parse_ok else 'no'})")
            if parse_ok:                      # a resolved-but-unparseable alias does NOT count
                ok.append(m)
        except Exception as e:
            print(f"  FAIL {m}  -> {type(e).__name__}: {str(e)[:140]}")
    print(f"validated {len(ok)}/{len(models)} aliases (score-parse must be 'yes' to count)")
    return ok


# --- Schedule (per domain, rep-block deconflicted) --------------------------------------
def _stable_hash(s):
    # deterministic across processes (Python's builtin hash() of a str is salted by
    # PYTHONHASHSEED, so it does NOT reproduce ordering from the recorded seed).
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def _git_commit():
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def build_schedule(domain, items_ids, models, protocols, seed=SEED):
    base = [(iid, m, c, cand, p) for iid in items_ids for m in models
            for c in COND_IDS for cand in CANDIDATES for p in protocols]
    sched = []
    for rep in range(REPS):
        block = list(base)
        random.Random(seed + rep + _stable_hash(domain) % 1000).shuffle(block)
        sched += [cell + (rep,) for cell in block]
    return sched


def cell_key(r):
    return (r["domain"], r["item_id"], r["model"], r["condition"], r["candidate_type"],
            r["repetition"], r["protocol"])


def load_successful(path):
    done = {}
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("score") is not None and r.get("error") is None:
                    done[cell_key(r)] = r["score"]
    return done


def _safe_parse(raw):
    # provenance_injection_harness.parse_score RAISES on a missing/invalid score (it does not
    # return None). Normalise both behaviours to "None == no score" so the retry logic below
    # is correct regardless of which parser is imported.
    try:
        return parse_score(raw)
    except Exception:
        return None


def judge_once(prompt, model, protocol, key, call_fn):
    # A cell fails to parse when the judge emits no valid score object -- usually because the
    # output was TRUNCATED before the verdict, or EMPTY (a soft refusal). Retry once with a
    # larger budget; only then record the cell as missing, tagged by an error taxonomy and the
    # provider finish_reason. BOTH attempts are logged (budget, finish_reason, parsed, raw).
    attempts = []
    raw, fin = call_fn(prompt, model, key, max_tokens=MAX_TOK[protocol], return_finish=True)
    s = _safe_parse(raw)
    attempts.append({"max_tokens": MAX_TOK[protocol], "finish_reason": fin,
                     "parsed": s is not None, "raw": raw})
    if s is not None:
        return s, raw, None, fin, attempts
    raw2, fin2 = call_fn(prompt, model, key, max_tokens=RETRY_TOK[protocol], return_finish=True)
    s2 = _safe_parse(raw2)
    attempts.append({"max_tokens": RETRY_TOK[protocol], "finish_reason": fin2,
                     "parsed": s2 is not None, "raw": raw2})
    if s2 is not None:
        return s2, raw2, None, fin2, attempts
    if "content_filter" in (fin, fin2):
        err = "content_filtered"                      # provider blocked the response (not truncation)
    elif not (raw2 or "").strip() and not (raw or "").strip():
        err = "empty_no_score"                        # soft refusal / empty completion
    elif "length" in (fin, fin2):
        err = "truncated_no_score"
    else:
        err = "unparseable_no_score"
    return None, raw2, err, fin2, attempts


def worker(cell, domain, dom, order_index, key, call_fn):
    iid, model, cond, cand, proto, rep = cell
    try:
        item = dom["_byid"][iid]
        prompt = dom["build"](item, cond, cand, proto)
        sha = _sha(prompt)
        score, raw, err, fin, attempts = judge_once(prompt, model, proto, key, call_fn)
        return ({"domain": domain, "item_id": iid, "model": model, "condition": cond,
                 "candidate_type": cand, "protocol": proto, "repetition": rep,
                 "order_index": order_index, "prompt_sha256": sha, "raw_response": raw,
                 "finish_reason": fin, "attempts": attempts, "score": score, "error": err,
                 "timestamp": time.time()}, prompt, sha)
    except Exception as e:
        return ({"domain": domain, "item_id": iid, "model": model, "condition": cond,
                 "candidate_type": cand, "protocol": proto, "repetition": rep,
                 "order_index": order_index, "prompt_sha256": None, "raw_response": "",
                 "finish_reason": None, "attempts": [], "score": None,
                 "error": f"worker:{type(e).__name__}: {e}", "timestamp": time.time()}, None, None)


# wiring-check writes throwaway stub evidence; it MUST NOT use the real STUDY_TAG filenames
# (a "w"-mode open would truncate real evidence, and its cleanup would delete it). _ACTIVE_TAG
# is overridden to a throwaway tag inside --wiring-check only.
_ACTIVE_TAG = STUDY_TAG


def obs_path(domain):
    return os.path.join(RES, f"{_ACTIVE_TAG}_{domain}_obs.jsonl")


def prompts_path(domain):
    return os.path.join(RES, f"{_ACTIVE_TAG}_{domain}_prompts.jsonl")


def meta_path():
    return os.path.join(RES, f"{_ACTIVE_TAG}_meta.json")


def run_domain(domain, dom, models, protocols, key, call_fn, workers, resume, progress_secs):
    dom["_byid"] = {dom["id"](x): x for x in dom["items"]}
    ids = [dom["id"](x) for x in dom["items"]]
    schedule = list(enumerate(build_schedule(domain, ids, models, protocols)))
    op, pp = obs_path(domain), prompts_path(domain)
    done = load_successful(op) if resume else {}
    seen = set()
    if resume and os.path.exists(pp):
        seen = {json.loads(l)["sha256"] for l in open(pp) if l.strip()}
    pending = [(oi, c) for oi, c in schedule
               if (domain, c[0], c[1], c[2], c[3], c[5], c[4]) not in done]
    mode = "a" if resume else "w"
    total = len(schedule)
    n_new = n_fail = 0
    start = last = time.time()
    print(f"[{domain}] {len(pending)} cells to do ({len(done)} done) of {total}, {workers} workers")
    with open(op, mode) as osink, open(pp, mode) as psink:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(worker, c, domain, dom, oi, key, call_fn) for oi, c in pending]
            for fut in as_completed(futs):
                row, prompt, sha = fut.result()
                if sha is not None and sha not in seen:
                    psink.write(json.dumps({"sha256": sha, "prompt": prompt}) + "\n"); psink.flush()
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
    it = list(per)
    if not it:
        return float("nan"), float("nan"), float("nan"), 0
    r = random.Random(seed)
    ms = sorted(sum(per[r.choice(it)] for _ in it) / len(it) for _ in range(n))
    return statistics.mean(per.values()), ms[int(.025 * n)], ms[int(.975 * n)], len(it)


def analyse(domains, floor_frac=0.75):
    for domain in domains:
        op = obs_path(domain)
        if not os.path.exists(op):
            print(f"[{domain}] no evidence"); continue
        rows = [json.loads(l) for l in open(op) if l.strip()]
        obs = {}
        for r in rows:
            if r.get("score") is not None and r.get("error") is None:
                obs[cell_key(r)] = r["score"]
        ids = sorted({r["item_id"] for r in rows})
        models = sorted({r["model"] for r in rows})
        floor = int(len(ids) * floor_frac)
        import collections
        miss = [r for r in rows if r.get("score") is None or r.get("error")]
        fail = collections.Counter(r["model"] for r in miss)
        print(f"\n=== {domain} ({len(ids)} items, floor {floor}) ===  missingness by model: {dict(fail)}")
        # condition-balanced completeness: missingness concentrated in the injected conditions
        # biases the contrast rather than only shrinking n -> such a model is unmeasurable.
        for m in models:
            if fail.get(m):
                by_cc = collections.Counter((r["condition"], r["candidate_type"]) for r in miss
                                            if r["model"] == m)
                base_f = sum(v for (c, _), v in by_cc.items() if c == "no_injection")
                inj_f = sum(v for (c, _), v in by_cc.items() if c != "no_injection")
                skew = " *INJECTION-SKEWED (treat as unmeasurable)" if inj_f > 6 and inj_f > 3 * max(base_f, 1) else ""
                cells = "  ".join(f"{c[:4]}/{cd[:3]}:{v}" for (c, cd), v in sorted(by_cc.items()))
                print(f"    miss[{m.split('/')[-1]:26s}] base={base_f} inj={inj_f}{skew}\n        {cells}")
        print(f"  {'model':32s} {'bare-harm [95% CI]':>26s}  {'prov+':>8s} {'rat+':>8s}")
        for m in models:
            base = _disc(obs, domain, m, "no_injection", ids)
            bare = _disc(obs, domain, m, "answer_only", ids)
            full = _disc(obs, domain, m, "full_rationale", ids)
            solv = _disc(obs, domain, m, "solver_rationale", ids)
            harm = {i: base[i] - bare[i] for i in set(base) & set(bare)}
            mn, lo, hi, n = _ci(harm)
            prov = {i: (base[i]-solv[i]) - (base[i]-full[i]) for i in set(solv) & set(full) & set(base)}
            rat = {i: (base[i]-full[i]) - (base[i]-bare[i]) for i in set(full) & set(bare) & set(base)}
            tag = "SUPPORTED" if (n >= floor and lo > 0) else ("unmeasurable" if n < floor else "ns")
            pm = _ci(prov)[0] if prov else float("nan")
            rm = _ci(rat)[0] if rat else float("nan")
            print(f"  {m:32s} {mn:+7.2f} [{lo:+7.2f},{hi:+7.2f}] n={n:2d} {tag:12s} {pm:+7.1f} {rm:+7.1f}")


def _stub(prompt, model, key, max_tokens=64, return_finish=False):
    h = int(hashlib.sha256((prompt + model).encode()).hexdigest(), 16)
    injected = any(s in prompt for s in ("Reference note:", "External", "Additional analysis:",
                                         "Solver", "reference answer", "Reference answer"))
    base = 80 if h % 2 else 70
    out = json.dumps({"score": max(0, min(100, base - (25 if injected else 0) + h % 12))})
    return (out, "stop") if return_finish else out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="", help="comma-separated OpenRouter aliases")
    ap.add_argument("--domains", default="arith,code,sql")
    ap.add_argument("--protocols", default="score_only")
    ap.add_argument("--check-models", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--wiring-check", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--stub", action="store_true")
    ap.add_argument("--force-models", action="store_true",
                    help="skip the --run self-preflight abort (use only to override a known-good alias)")
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    ap.add_argument("--progress-secs", type=int, default=600)
    ap.add_argument("--tag", default=None,
                    help="override evidence file tag for an isolated re-run (e.g. a single-model "
                         "re-run into fresh files, later merged for analysis); keeps original evidence pristine")
    a = ap.parse_args()
    global _ACTIVE_TAG
    if a.tag:
        _ACTIVE_TAG = a.tag
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    domains = [d.strip() for d in a.domains.split(",") if d.strip()]
    protocols = [p.strip() for p in a.protocols.split(",") if p.strip()]

    if a.analyse_only:
        analyse(domains); return

    doms = {d: DOMAINS[d]() for d in domains}     # builds + validates each domain offline
    for d in domains:
        doms[d]["gate"]()
    total = sum(len(doms[d]["items"]) * len(models) * len(COND_IDS) * len(CANDIDATES) * len(protocols) * REPS
                for d in domains)
    print(f"frontier plan: domains={domains} models={len(models)} protocols={protocols} "
          f"seed={SEED} -> {total} judge cells")

    if a.check_models:
        loaded = load_env(); key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            print("ERROR: OPENROUTER_API_KEY not found (needed to validate aliases)."); sys.exit(2)
        check_models(models, key); return

    if a.dry_run:
        for d in domains:
            dom = doms[d]; it0 = dom["items"][0]
            print(f"\n--- {d} sample bare-conclusion score_only prompt ---")
            print(dom["build"](it0, "answer_only", "wrong_matching", "score_only")[:700])
        return

    if a.wiring_check:
        _ACTIVE_TAG = STUDY_TAG + "_wiring"      # never touch real evidence filenames
        for d in domains:
            run_domain(d, doms[d], models or ["stub/a", "stub/b"], protocols, "STUB", _stub,
                       a.workers, resume=False, progress_secs=a.progress_secs)
        analyse(domains)
        for d in domains:
            for p in (obs_path(d), prompts_path(d)):
                try: os.remove(p)
                except OSError: pass
        print("\nwiring-check complete (stub; throwaway evidence removed)")
        return

    if a.run or a.resume:
        call_fn = _stub; key = "STUB"
        validated = list(models)
        if not a.stub:
            loaded = load_env(); key = os.environ.get("OPENROUTER_API_KEY")
            if loaded: print("loaded from .env:", ", ".join(loaded))
            if not key:
                print("ERROR: OPENROUTER_API_KEY not found. No API call made."); sys.exit(2)
            if not models:
                print("ERROR: --models required for a real run."); sys.exit(2)
            from judge_integrity_real import call_openrouter
            call_fn = call_openrouter
            validated = check_models(models, key)          # self-preflight before any real cell
            missing = [m for m in models if m not in validated]
            if missing and not a.force_models:
                print(f"ERROR: preflight score-parse failed for {missing}. Aborting before any "
                      f"scored cell — a model that cannot emit a parseable score would fail-closed "
                      f"to missing and read as false 'no capture'. Fix the alias or budget, or pass "
                      f"--force-models to override.")
                sys.exit(3)
        json.dump({"study": "frontier_v3", "study_tag": _ACTIVE_TAG,
                   "supersedes": "ccc_frontier_v2 (exploratory; dead retry + non-reproducible "
                                 "hash schedule) and ccc_frontier void runs 1-2 (60/240 truncation)",
                   "seed": SEED, "reps": REPS, "models": models,
                   "validated_models": validated, "force_models": bool(a.force_models),
                   "domains": domains, "protocols": protocols, "conditions": COND_IDS,
                   "candidates": CANDIDATES, "frozen_items": True, "workers": a.workers,
                   "stub": bool(a.stub), "max_tok": MAX_TOK, "retry_tok": RETRY_TOK,
                   "git_commit": _git_commit(), "schedule_hash": "sha256(domain) (reproducible)",
                   "run_date": time.strftime("%Y-%m-%d"), "python": sys.version.split()[0]},
                  open(meta_path(), "w"), indent=1)
        for d in domains:
            run_domain(d, doms[d], models, protocols, key, call_fn, a.workers,
                       resume=a.resume, progress_secs=a.progress_secs)
        analyse(domains)
        return

    ap.print_help()


if __name__ == "__main__":
    main()
