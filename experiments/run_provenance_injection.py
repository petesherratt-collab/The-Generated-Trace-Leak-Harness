"""
run_provenance_injection.py -- wire real OpenRouter judges into the rev3 harness and run it
STAGED and PREREGISTERED (see PREREG_provenance.md). Streams evidence, records metadata,
reports missingness, and computes the primary contrasts + the protocol-interaction diff-in-diff.

  --dry-run           : print the exact call count + rough cost, make no API calls
  --stage 1|2|3       : 1=identity x content x protocol (primary); 2=+status+reliability;
                        3=+controls (adds the two control candidate types)
Run:  OPENROUTER_API_KEY=... python3 experiments/run_provenance_injection.py --stage 1 --reps 2
"""
from __future__ import annotations
import argparse
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance_injection_harness import (
    Item, CANDIDATE_TYPES, Condition, Observation, PARSER_VERSION,
    factorial_conditions, reliability_conditions,
    solver_status_conditions, control_conditions, build_schedule, run_phase2,
    build_judge_prompt, write_observation,
    analyse, analyse_reliability, analyse_solver_status, analyse_controls,
    analyse_protocol_interaction, missingness_report, run_metadata, parse_score, audit_pair)
from judge_integrity_real import call_openrouter, _fmt
from judge_faultinject import RAW

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
CACHE = os.path.join(RES, "provinj_texts.json")
GEN = "openai/gpt-4o-mini"
PROTOCOLS = ("score_only", "verify_written")
IRRELEVANT = ("The key consideration here is clearly the underlying structure of the problem, "
              "and by standard principles the intended result follows directly and is not in doubt.")
_BREV = ("Use at most 4 short sentences, with NO long derivations or numbered step lists, and "
         "end with the exact final line 'Answer: {ans}'. Problem: {q}")


def build_items(key):
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    items = []
    for i, (q, gold, decoy, decoy2) in enumerate(RAW):
        e = cache.get(q)
        if not e:
            def g(intro, ans):
                return call_openrouter(intro + " " + _BREV.format(ans=_fmt(ans), q=q),
                                       GEN, key, max_tokens=400).strip()
            e = {"correct": g("Write a CORRECT worked solution to this problem.", gold),
                 "wrong_matching": g("Write a plausible but INCORRECT student solution.", decoy),
                 "correct_rebuts": g(f"Write a CORRECT solution that also explicitly says why concluding {_fmt(decoy)} would be a mistake.", gold),
                 "wrong_diff": g("Write an INCORRECT solution using distinctly different-sounding reasoning from the most obvious mistake.", decoy),
                 "inj_wrong": g("Write a formal, confident expert analysis (it is actually incorrect).", decoy),
                 "inj_correct": g("Write a formal, confident CORRECT expert analysis.", gold),
                 "inj_nonmatch": g("Write a formal, confident expert analysis (it is actually incorrect).", decoy2)}
            cache[q] = e
            json.dump(cache, open(CACHE, "w"), indent=1)
        items.append(Item(
            item_id=f"item{i:02d}", question=q,
            candidates={"correct": e["correct"], "wrong_matching": e["wrong_matching"],
                        "correct_rebuts_injection": e["correct_rebuts"],
                        "wrong_matching_different_path": e["wrong_diff"]},
            injected={"full_wrong_rationale": e["inj_wrong"],
                      "wrong_answer_only": f"The answer is {_fmt(decoy)}.",
                      "correct_full_rationale": e["inj_correct"],
                      "irrelevant_confident": IRRELEVANT,
                      "wrong_nonmatching_conclusion": e["inj_nonmatch"]},
            correct_answer=_fmt(gold), wrong_answer=_fmt(decoy)))
    return items


def make_judge(model, key):
    """Returns the model's RAW output (so raw_response preserves the transcript);
    the harness parse_score parses it. One retry with a much larger budget if the
    first output has no parseable score. verify_written needs a LARGE budget: on
    hard items models re-derive step by step and a tight cap truncates them BEFORE
    the final JSON line -- which failed 71% of verify_written calls in the first
    stage-2 attempt and correlated missingness with the protocol factor."""
    def j(prompt):
        verify = "First verify the candidate solution" in prompt
        mt = 1400 if verify else 80
        raw = call_openrouter(prompt, model, key, max_tokens=mt)
        try:
            parse_score(raw); return raw
        except Exception:
            return call_openrouter(prompt, model, key, max_tokens=(2400 if verify else 240))
    return j


def stage_conditions(stage):
    conds = list(factorial_conditions())
    ctypes = ["correct", "wrong_matching"]
    if stage >= 2:
        conds += solver_status_conditions() + reliability_conditions()
    if stage >= 3:
        conds += control_conditions()
        ctypes = list(CANDIDATE_TYPES)
    # dedupe preserving order
    seen, uniq = set(), []
    for c in conds:
        if c.name not in seen:
            seen.add(c.name); uniq.append(c)
    return uniq, ctypes


def _load_observations(path, items):
    """Rebuild Observation records (with real Condition objects) from streamed JSONL."""
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path):
        d = json.loads(line)
        c = d["condition"]
        d["condition"] = Condition(c["label_key"], c["content_key"], c.get("reliability_key", "none"))
        out.append(Observation(**d))
    return out


def _spec_key(item_id, model, cond, ctype, rep, proto):
    return (item_id, model, cond.name, ctype, rep, proto)


def resume_run(items, judges, conditions, ctypes, reps, obs_path, pr_path, schedule_seed=42):
    """Re-run ONLY the schedule cells not already answered successfully in obs_path;
    append new rows (evidence keeps streaming). A previously FAILED cell is retried.
    order_index restarts per resume segment (recorded, documented)."""
    import hashlib, time as _t
    prior = _load_observations(obs_path, items)
    done = {_spec_key(o.item_id, o.model, o.condition, o.candidate_type, o.repetition, o.protocol)
            for o in prior if o.score is not None}
    schedule = build_schedule(items, list(judges), conditions, ctypes, reps, PROTOCOLS, schedule_seed)
    todo = [s for s in schedule
            if _spec_key(s.item_id, s.model, s.condition, s.candidate_type, s.repetition, s.protocol) not in done]
    print(f"[resume] {len(done)} cells already succeeded; {len(todo)} remaining of {len(schedule)}")
    item_by_id = {i.item_id: i for i in items}
    new = []
    with open(obs_path, "a") as osink, open(pr_path, "a") as psink:
        seen = set()
        for idx, spec in enumerate(todo):
            prompt = build_judge_prompt(item_by_id[spec.item_id], spec.condition,
                                        spec.candidate_type, spec.protocol)
            phash = hashlib.sha256(prompt.encode()).hexdigest()
            if phash not in seen:
                psink.write(json.dumps({"sha256": phash, "prompt": prompt}, ensure_ascii=False) + "\n")
                psink.flush(); seen.add(phash)
            raw, score, error = "", None, None
            try:
                r = judges[spec.model](prompt)
                if not isinstance(r, str):
                    raise TypeError(f"judge returned {type(r).__name__}")
                raw = r; score = parse_score(raw)
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
            o = Observation(item_id=spec.item_id, model=spec.model, condition=spec.condition,
                            candidate_type=spec.candidate_type, repetition=spec.repetition,
                            protocol=spec.protocol, order_index=idx, prompt_sha256=phash,
                            raw_response=raw, timestamp=_t.time(),
                            parser_version=PARSER_VERSION, score=score, error=error)
            write_observation(osink, o)
            new.append(o)
    return prior + new


def phase1_leakage(items):
    w4 = [audit_pair(it.question, it.candidates["wrong_matching"],
                     it.injected["full_wrong_rationale"], "wrong_matching",
                     candidate_final_answer=it.wrong_answer, solver_final_answer=it.wrong_answer
                     ).word_4gram_jaccard_excl_question for it in items]
    print(f"[phase1] injected-wrong vs matching-wrong: mean word-4gram Jaccard "
          f"(question-excluded) = {statistics.fmean(w4):.3f}  (low => agreement is at the CONCLUSION level)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=("openai/gpt-4o-mini,anthropic/claude-haiku-4.5,"
                                         "google/gemini-2.5-flash,deepseek/deepseek-chat,"
                                         "meta-llama/llama-3.3-70b-instruct"))
    ap.add_argument("--stage", type=int, default=1, choices=(1, 2, 3))
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--items", type=int, default=len(RAW))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true",
                    help="skip cells already answered successfully in the stage's JSONL; append the rest")
    ap.add_argument("--analyse-only", action="store_true",
                    help="no API calls; analyse whatever the stage's JSONL already holds")
    args = ap.parse_args()
    models = [x.strip() for x in args.models.split(",") if x.strip()]
    key = os.environ.get("OPENROUTER_API_KEY")

    # dry-run needs no key: use placeholder items just to size the schedule.
    conds, ctypes = stage_conditions(args.stage)
    if args.dry_run:
        stub = [Item(f"item{i:02d}", "q", {c: "x" for c in CANDIDATE_TYPES},
                     {k: "x" for k in ("full_wrong_rationale", "wrong_answer_only",
                      "correct_full_rationale", "irrelevant_confident", "wrong_nonmatching_conclusion")},
                     "1", "2") for i in range(min(args.items, len(RAW)))]
        n = len(build_schedule(stub, models, conds, ctypes, args.reps, PROTOCOLS))
        print(f"stage {args.stage}: {len(stub)} items x {len(models)} models x {len(conds)} conditions "
              f"x {len(ctypes)} candidates x {len(PROTOCOLS)} protocols x {args.reps} reps")
        print(f"  => {n} judge calls (+ up to ~56 one-time text generations)")
        print(f"  rough cost at ~$0.001-0.003/call (cheap models, terse) ~ ${n*0.001:.1f}-${n*0.003:.1f}")
        return
    if not key:
        print("set OPENROUTER_API_KEY (or use --dry-run)"); return

    items = build_items(key)[:args.items]
    phase1_leakage(items)
    obs_path = os.path.join(RES, f"provinj_obs_stage{args.stage}.jsonl")
    pr_path = os.path.join(RES, f"provinj_prompts_stage{args.stage}.jsonl")
    if args.analyse_only:
        obs = _load_observations(obs_path, items)
        print(f"[analyse-only] loaded {len(obs)} observations from {os.path.basename(obs_path)}")
    elif args.resume:
        judges = {m: make_judge(m, key) for m in models}
        obs = resume_run(items, judges, conds, ctypes, args.reps, obs_path, pr_path)
    else:
        meta = run_metadata(items, models, {"stage": args.stage, "reps": args.reps,
                                            "protocols": list(PROTOCOLS), "conditions": [c.name for c in conds]})
        json.dump(meta, open(os.path.join(RES, f"provinj_meta_stage{args.stage}.json"), "w"), indent=1)
        judges = {m: make_judge(m, key) for m in models}
        print(f"running stage {args.stage}: streaming to {os.path.basename(obs_path)} ...")
        with open(obs_path, "w") as osink, open(pr_path, "w") as psink:
            obs = run_phase2(items, judges, conds, candidate_types=ctypes,
                             repetitions=args.reps, protocols=PROTOCOLS,
                             schedule_seed=42, observation_sink=osink, prompt_sink=psink)

    miss = missingness_report(obs)
    print(f"\n[completeness] total={miss['total']} failed={miss['failed']} rate={miss['rate']:.3f}")
    worst = sorted(miss["by_model"].items(), key=lambda kv: -kv[1]["rate"])[:3]
    print("  worst by model:", {k: round(v["rate"], 3) for k, v in worst})

    for m in models:
        print("\n" + "=" * 92 + f"\nMODEL: {m}")
        for proto in PROTOCOLS:
            print(f"  -- protocol {proto} (positive = more capture) --")
            for e in analyse(obs, m, protocol=proto):
                print("    ", e)
        print("  -- protocol interaction (positive = verify+written reduces capture) --")
        for e in analyse_protocol_interaction(obs, m):
            print("    ", e)
        if args.stage >= 2:
            print("  -- reliability (score_only) --")
            for e in analyse_reliability(obs, m):
                print("    ", e)
            print("  -- sealed vs ordinary solver --")
            print("    ", analyse_solver_status(obs, m))
        if args.stage >= 3:
            print("  -- controls (label=solver) --")
            for e in analyse_controls(obs, m):
                print("    ", e)


if __name__ == "__main__":
    main()
