import io
import hashlib
import json
import os
import sys
import tempfile
import unittest
import warnings
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import judge_integrity_real as client
import run_ccc_frontier as runner


class FrontierInstrumentTests(unittest.TestCase):
    def test_frontier_v3_defaults_are_fresh(self):
        self.assertEqual(runner.RUNNER_VERSION, "frontier-v3")
        self.assertEqual(runner.SEED, 305774821)
        self.assertEqual(runner.DEFAULT_OUTPUT_PREFIX, "ccc_frontier_v3")
        self.assertEqual(runner.DEFAULT_RUN_ID, "ccc_frontier_v3_305774821")

    def test_all_frozen_prompt_hashes_match_the_shared_instrument(self):
        expected = {
            "arith": (128, "48500df626b1bf730be6f4c075c43e20373372580c1cd603bb926d08a5f535cf"),
            "code": (128, "d1b47696b8dc9d72629ef75849ecd12b87a68c251c70f1cde15156e900b2738d"),
            "sql": (192, "d9b1a27169749d3b1072d3bd7d41275d4230cff74a1efaa8e8a18504ddd298fd"),
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            for domain, (expected_count, expected_hash) in expected.items():
                spec = runner.DOMAINS[domain]()
                digest = hashlib.sha256()
                count = 0
                for item in spec["items"]:
                    item_id = spec["id"](item)
                    for condition in runner.COND_IDS:
                        for candidate in runner.CANDIDATES:
                            prompt = spec["build"](
                                item, condition, candidate, "score_only",
                            )
                            record = json.dumps(
                                [domain, item_id, condition, candidate, prompt],
                                ensure_ascii=False, separators=(",", ":"),
                            )
                            digest.update(record.encode())
                            count += 1
                self.assertEqual(count, expected_count)
                self.assertEqual(digest.hexdigest(), expected_hash)

    def test_schedule_is_deterministic_and_model_relative_order_matches(self):
        args = ("arith", ["i1", "i2", "i3"], ["m1", "m2"], ["score_only"])
        first = runner.build_schedule(*args, seed=123456)
        second = runner.build_schedule(*args, seed=123456)
        self.assertEqual(first, second)

        def relative(model):
            return [(iid, cond, cand, proto, rep)
                    for iid, m, cond, cand, proto, rep in first if m == model]

        self.assertEqual(relative("m1"), relative("m2"))

    def test_compatibility_pilot_is_balanced_and_selects_items_stably(self):
        ids = [f"item-{i}" for i in range(12)]
        selected = runner.select_pilot_items("arith", ids, 2, seed=824663051)
        self.assertEqual(len(selected), 2)
        self.assertEqual(
            selected,
            runner.select_pilot_items("arith", list(reversed(ids)), 2, seed=824663051),
        )
        schedule = runner.build_schedule(
            "arith", selected, ["model-1"], ["score_only"],
            seed=824663051, reps=1,
        )
        self.assertEqual(len(schedule), 16)
        strata = {(condition, candidate) for _, _, condition, candidate, _, _ in schedule}
        self.assertEqual(
            strata,
            {(condition, candidate)
             for condition in runner.COND_IDS for candidate in runner.CANDIDATES},
        )
        self.assertTrue(all(rep == 0 for *_, rep in schedule))

    def test_pilot_eligibility_requires_every_score(self):
        report = {
            "domains": {
                "arith": {
                    "complete": True,
                    "successful_cells": 16,
                    "expected_cells": 16,
                    "error_counts": {},
                    "strict_score_cells": 16,
                    "reasoning_usage_records": 16,
                    "provider_response_attempts": 16,
                    "total_judge_attempts": 16,
                    "max_reasoning_tokens": 0,
                },
                "code": {
                    "complete": True,
                    "successful_cells": 15,
                    "expected_cells": 16,
                    "error_counts": {"truncated_no_score": 1},
                    "strict_score_cells": 15,
                    "reasoning_usage_records": 16,
                    "provider_response_attempts": 16,
                    "total_judge_attempts": 16,
                    "max_reasoning_tokens": 0,
                },
            },
        }
        runner.add_pilot_eligibility(report, reasoning_ceiling=0)
        self.assertTrue(report["domains"]["arith"]["pilot_eligible"])
        self.assertFalse(report["domains"]["code"]["pilot_eligible"])
        self.assertFalse(report["pilot_eligible"])

    def test_strict_score_json_rejects_extra_text_and_keys(self):
        self.assertTrue(runner._strict_score_json('{"score": 42}'))
        self.assertFalse(runner._strict_score_json('Score: {"score": 42}'))
        self.assertFalse(runner._strict_score_json('{"score": 42, "note": "x"}'))

    def test_terminal_score_json_allows_reasoning_but_no_trailing_text(self):
        self.assertTrue(runner._terminal_score_json('Reasoning first.\n{"score": 42}'))
        self.assertTrue(runner._terminal_score_json('{"score": 42}\n'))
        self.assertFalse(runner._terminal_score_json('{"score": 42}\nmore text'))
        self.assertFalse(runner._terminal_score_json('{"score": 42, "note": "x"}'))

    def test_terminal_contract_retries_a_truncated_parseable_response(self):
        calls = []

        def fake_call(prompt, model, key, max_tokens, return_meta, provider):
            calls.append(max_tokens)
            if len(calls) == 1:
                return {"text": 'early {"score": 10}', "finish_reason": "length",
                        "response_model": model, "provider": provider}
            return {"text": 'reasoning\n{"score": 20}', "finish_reason": "stop",
                    "response_model": model, "provider": provider}

        score, raw, error, finish, attempts = runner.judge_once(
            "prompt", "model", "score_only", "key", fake_call,
            provider="together", score_acceptance="terminal",
        )
        self.assertEqual(score, 20)
        self.assertEqual(raw, 'reasoning\n{"score": 20}')
        self.assertIsNone(error)
        self.assertEqual(finish, "stop")
        self.assertEqual(calls, [1024, 2048])
        self.assertFalse(attempts[0]["parsed"])
        self.assertIn("terminal", attempts[0]["parse_error"])

    def test_native_pilot_gate_uses_terminal_contract(self):
        report = {"domains": {"arith": {
            "complete": True, "successful_cells": 16, "expected_cells": 16,
            "error_counts": {}, "strict_score_cells": 14,
            "terminal_score_cells": 16, "reasoning_usage_records": 16,
            "provider_response_attempts": 16, "max_reasoning_tokens": 8001,
        }}}
        runner.add_pilot_eligibility(
            report, reasoning_ceiling=None, score_acceptance="terminal",
        )
        self.assertTrue(report["pilot_eligible"])
        self.assertEqual(report["pilot_score_acceptance"], "terminal")

    def test_parse_failure_retries_and_preserves_both_attempts(self):
        calls = []

        def fake_call(prompt, model, key, max_tokens, return_meta, provider):
            calls.append(max_tokens)
            if len(calls) == 1:
                return {"text": "unfinished reasoning", "finish_reason": "length",
                        "response_model": model, "provider": provider}
            return {"text": '{"score": 100}', "finish_reason": "stop",
                    "response_model": model, "provider": provider}

        score, raw, error, finish, attempts = runner.judge_once(
            "prompt", "model", "score_only", "key", fake_call, provider="deepinfra",
        )
        self.assertEqual(score, 100)
        self.assertEqual(raw, '{"score": 100}')
        self.assertIsNone(error)
        self.assertEqual(finish, "stop")
        self.assertEqual(calls, [1024, 2048])
        self.assertEqual(len(attempts), 2)
        self.assertIn("ValueError", attempts[0]["parse_error"])
        self.assertEqual(attempts[0]["finish_reason"], "length")
        self.assertFalse(attempts[0]["parsed"])
        self.assertTrue(attempts[1]["parsed"])

    def test_two_parse_failures_preserve_both_raw_attempts(self):
        calls = []

        def fake_call(prompt, model, key, max_tokens, return_meta, provider):
            calls.append(max_tokens)
            return {"text": f"unfinished-{max_tokens}", "finish_reason": "length",
                    "response_model": model, "provider": "provider-a"}

        score, raw, error, finish, attempts = runner.judge_once(
            "prompt", "model", "score_only", "key", fake_call,
            expected_provider="provider-a", expected_response_model="model",
        )
        self.assertIsNone(score)
        self.assertEqual(raw, "unfinished-2048")
        self.assertEqual(error, "truncated_no_score")
        self.assertEqual(finish, "length")
        self.assertEqual(calls, [1024, 2048])
        self.assertEqual([a["raw_response"] for a in attempts],
                         ["unfinished-1024", "unfinished-2048"])
        self.assertTrue(all(a["parse_error"] for a in attempts))
        self.assertTrue(all(not a["parsed"] for a in attempts))

    def test_content_filter_is_classified_after_both_attempts(self):
        calls = []

        def fake_call(prompt, model, key, max_tokens, return_meta, provider):
            calls.append(max_tokens)
            return {"text": "", "finish_reason": "content_filter",
                    "response_model": model, "provider": "provider-a"}

        score, raw, error, finish, attempts = runner.judge_once(
            "prompt", "model", "score_only", "key", fake_call,
            expected_provider="provider-a", expected_response_model="model",
        )
        self.assertIsNone(score)
        self.assertEqual(raw, "")
        self.assertEqual(error, "content_filtered")
        self.assertEqual(finish, "content_filter")
        self.assertEqual(calls, [1024, 2048])
        self.assertEqual(len(attempts), 2)
        self.assertTrue(all(a["finish_reason"] == "content_filter" for a in attempts))
        self.assertTrue(all(a["parse_error"] for a in attempts))

    def test_request_failure_retries_and_is_auditable(self):
        calls = []

        def fake_call(prompt, model, key, max_tokens, return_meta, provider):
            calls.append(max_tokens)
            if len(calls) == 1:
                raise KeyError("choices")
            return {"text": '{"score": 80}', "finish_reason": "stop",
                    "response_model": model, "provider": provider}

        score, _, error, _, attempts = runner.judge_once(
            "prompt", "model", "score_only", "key", fake_call, provider="deepinfra",
        )
        self.assertEqual(score, 80)
        self.assertIsNone(error)
        self.assertEqual(calls, [1024, 2048])
        self.assertIn("KeyError", attempts[0]["call_error"])

    def test_verify_written_preflight_uses_verify_prompt_and_budget(self):
        calls = []

        def fake_call(prompt, model, key, max_tokens, return_meta, provider):
            calls.append((prompt, max_tokens))
            return {"text": 'Checked: 2 + 2 = 4. {"score": 100}',
                    "finish_reason": "stop", "response_model": model,
                    "provider": provider}

        validated, records = runner.check_models(
            ["model-1"], "key", call_fn=fake_call, provider="provider-a",
            protocol="verify_written",
        )
        self.assertEqual(validated, ["model-1"])
        self.assertEqual(records[0]["protocol"], "verify_written")
        self.assertIn("verify in writing", calls[0][0])
        self.assertEqual(calls[0][1], runner.MAX_TOK["verify_written"])

    def test_endpoint_identity_mismatch_retries_and_fails_closed(self):
        def fake_call(prompt, model, key, max_tokens, return_meta, provider):
            return {"text": '{"score": 100}', "finish_reason": "stop",
                    "response_model": "unexpected-model", "provider": "DeepInfra"}

        score, _, error, _, attempts = runner.judge_once(
            "prompt", "requested-model", "score_only", "key", fake_call,
            provider="deepinfra", expected_provider="deepinfra",
            expected_response_model="frozen-model",
        )
        self.assertIsNone(score)
        self.assertEqual(error, "endpoint_identity_mismatch")
        self.assertEqual(len(attempts), 2)
        self.assertTrue(all(a["identity_error"] for a in attempts))

    def test_provider_slug_can_match_openrouter_display_name(self):
        def fake_call(prompt, model, key, max_tokens, return_meta, provider):
            return {"text": '{"score": 100}', "finish_reason": "stop",
                    "response_model": model, "provider": "Alibaba Cloud Int."}

        score, _, error, _, attempts = runner.judge_once(
            "prompt", "qwen/qwen3.7-plus", "score_only", "key", fake_call,
            provider="alibaba", expected_provider="alibaba",
        )
        self.assertEqual(score, 100)
        self.assertIsNone(error)
        self.assertIsNone(attempts[0]["identity_error"])

    def test_openrouter_request_pins_provider_without_fallbacks(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["payload"] = json.loads(request.data.decode())
            response = {
                "id": "response-id",
                "model": "resolved-model",
                "provider": "DeepInfra",
                "choices": [{
                    "finish_reason": "stop",
                    "message": {"content": '{"score": 100}'},
                }],
                "usage": {"completion_tokens": 7},
            }
            return io.BytesIO(json.dumps(response).encode())

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            meta = client.call_openrouter(
                "prompt", "requested-model", "secret-not-printed", retries=1,
                return_meta=True, provider="deepinfra",
                reasoning={"max_tokens": 2048, "exclude": True},
                response_format=runner.SCORE_RESPONSE_FORMAT,
            )

        self.assertEqual(captured["payload"]["provider"], {
            "only": ["deepinfra"],
            "allow_fallbacks": False,
            "require_parameters": True,
        })
        self.assertEqual(captured["payload"]["reasoning"], {
            "max_tokens": 2048,
            "exclude": True,
        })
        self.assertEqual(captured["payload"]["response_format"],
                         runner.SCORE_RESPONSE_FORMAT)
        self.assertEqual(meta["provider"], "DeepInfra")
        self.assertEqual(meta["response_model"], "resolved-model")

    def test_provider_can_be_pinned_without_capability_filtering(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["payload"] = json.loads(request.data.decode())
            response = {
                "id": "response-id", "model": "resolved-model", "provider": "MiniMax",
                "choices": [{"finish_reason": "stop",
                             "message": {"content": '{"score": 100}'}}],
            }
            return io.BytesIO(json.dumps(response).encode())

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            client.call_openrouter(
                "prompt", "requested-model", "secret", retries=1,
                return_meta=True, provider="minimax",
                provider_require_parameters=False,
            )
        self.assertEqual(captured["payload"]["provider"], {
            "only": ["minimax"],
            "allow_fallbacks": False,
            "require_parameters": False,
        })

    def test_evidence_paths_are_namespaced(self):
        path = runner.obs_path("sql", "X:/evidence", "ccc_openweight_v1")
        self.assertTrue(path.endswith("ccc_openweight_v1_sql_obs.jsonl"))

    def test_seeded_bootstrap_is_independent_of_mapping_order(self):
        forward = {"item-a": 10.0, "item-b": 20.0, "item-c": -5.0}
        reverse = dict(reversed(list(forward.items())))
        self.assertEqual(runner._ci(forward, n=200, seed=7331),
                         runner._ci(reverse, n=200, seed=7331))

    def test_completion_metadata_audits_attempts_prompts_and_balance(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefix = "ccc_frontier_v3"
            run_id = "run-v3"
            obs = runner.obs_path("arith", tmp, prefix)
            prompts = runner.prompts_path("arith", tmp, prefix)
            prompt_records = {}
            rows = []
            order = 0
            for condition in runner.COND_IDS:
                for candidate in runner.CANDIDATES:
                    prompt = f"{condition}|{candidate}"
                    sha = runner._sha(prompt)
                    prompt_records[sha] = prompt
                    for rep in range(runner.REPS):
                        rows.append({
                            "run_id": run_id,
                            "domain": "arith",
                            "item_id": "item-1",
                            "model": "model-1",
                            "condition": condition,
                            "candidate_type": candidate,
                            "protocol": "score_only",
                            "repetition": rep,
                            "order_index": order,
                            "prompt_sha256": sha,
                            "score": 100 if candidate == "correct" else 0,
                            "error": None,
                            "attempts": [{
                                "attempt": 1,
                                "max_tokens": 1024,
                                "raw_response": '{"score": 100}',
                                "finish_reason": "stop",
                                "parsed": True,
                                "call_error": None,
                                "parse_error": None,
                                "identity_error": None,
                                "transport_attempt_count": 1,
                            }],
                            "timestamp": float(order),
                        })
                        order += 1
            with open(obs, "w", encoding="utf-8") as sink:
                for row in rows:
                    sink.write(json.dumps(row) + "\n")
            with open(prompts, "w", encoding="utf-8") as sink:
                for sha, prompt in prompt_records.items():
                    sink.write(json.dumps({"sha256": sha, "prompt": prompt}) + "\n")

            report = runner.build_completion_metadata(
                ["arith"], study="frontier_v3", evidence_dir=tmp,
                output_prefix=prefix, run_id=run_id,
                expected_models=["model-1"], expected_items={"arith": ["item-1"]},
                protocols=["score_only"], balance_gap=0.05,
            )
            domain = report["domains"]["arith"]
            self.assertTrue(report["evidence_complete"])
            self.assertEqual(domain["unique_cells"], 24)
            self.assertEqual(domain["total_judge_attempts"], 24)
            self.assertEqual(domain["attempt_count_histogram"], {"1": 24})
            self.assertTrue(domain["prompt_manifest_ok"])
            self.assertTrue(domain["strata"]["model-1"]["primary_balance"]["passed"])
            self.assertEqual(
                domain["strata"]["model-1"]["primary_balance"]["content_filter_delta"],
                0,
            )

    def test_verify_written_analysis_and_completion_are_protocol_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefix = "ccc_frontier_p2_arith_fable"
            run_id = "frontier-p2-arith-fable"
            obs = runner.obs_path("arith", tmp, prefix)
            prompts = runner.prompts_path("arith", tmp, prefix)
            prompt_records = {}
            rows = []
            order = 0
            for condition in runner.COND_IDS:
                for candidate in runner.CANDIDATES:
                    prompt = f"verify_written|{condition}|{candidate}"
                    sha = runner._sha(prompt)
                    prompt_records[sha] = prompt
                    for rep in range(runner.REPS):
                        if condition == "answer_only":
                            score = 0 if candidate == "correct" else 100
                        else:
                            score = 100 if candidate == "correct" else 0
                        rows.append({
                            "run_id": run_id,
                            "domain": "arith",
                            "item_id": "item-1",
                            "model": "model-1",
                            "condition": condition,
                            "candidate_type": candidate,
                            "protocol": "verify_written",
                            "repetition": rep,
                            "order_index": order,
                            "prompt_sha256": sha,
                            "score": score,
                            "error": None,
                            "attempts": [{
                                "attempt": 1,
                                "max_tokens": 2048,
                                "raw_response": json.dumps({"score": score}),
                                "finish_reason": "stop",
                                "parsed": True,
                                "call_error": None,
                                "parse_error": None,
                                "identity_error": None,
                                "transport_attempt_count": 1,
                            }],
                            "timestamp": float(order),
                        })
                        order += 1
            with open(obs, "w", encoding="utf-8") as sink:
                for row in rows:
                    sink.write(json.dumps(row) + "\n")
            with open(prompts, "w", encoding="utf-8") as sink:
                for sha, prompt in prompt_records.items():
                    sink.write(json.dumps({"sha256": sha, "prompt": prompt}) + "\n")

            report = runner.build_completion_metadata(
                ["arith"], study="frontier_p2", evidence_dir=tmp,
                output_prefix=prefix, run_id=run_id,
                expected_models=["model-1"], expected_items={"arith": ["item-1"]},
                protocols=["verify_written"], balance_gap=0.05,
            )
            self.assertTrue(report["phase_2_executed"])
            self.assertEqual(report["analysis_protocol"], "verify_written")
            self.assertTrue(
                report["domains"]["arith"]["strata"]["model-1"]["primary_balance"]["passed"]
            )

            output = io.StringIO()
            with mock.patch("sys.stdout", output):
                runner.analyse(
                    ["arith"], evidence_dir=tmp, output_prefix=prefix,
                    run_id=run_id, expected_models=["model-1"],
                    expected_items={"arith": ["item-1"]},
                    balance_gap=0.05, protocol="verify_written",
                )
            rendered = output.getvalue()
            self.assertIn("protocol=verify_written", rendered)
            self.assertIn("+200.00", rendered)
            self.assertIn("SUPPORTED", rendered)


if __name__ == "__main__":
    unittest.main()
