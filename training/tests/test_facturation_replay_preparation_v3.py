"""Regression checks for inherited curriculum and joint bilingual replay."""
from collections import Counter
from copy import deepcopy
import json
import os
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import prepare_facturation_replay_v3 as m


class ShapeReplayPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared, cls.focus, cls.rows, cls.train, cls.valid, cls.indices = m.frozen.combined()
        cls.selected = m.selection(cls.rows, cls.indices)
        cls.languages = cls.selected["request_language_by_row"]

    def features(self, index):
        return m.retention_features(self.rows[index], self.languages[index]["language"],
                                    self.selected["training_scenario_by_row"][index])

    def test_frozen_v1_and_source_bytes_remain_unchanged(self):
        self.assertEqual(m.frozen.sha((ROOT / "training/scripts/prepare_facturation_replay_v1.py").read_bytes()),
                         m.V1_SHA256)
        original = ROOT / "training/datasets" / m.frozen.SHARED
        self.assertTrue(self.train.startswith((original / "train.jsonl").read_bytes()))
        self.assertEqual(self.valid, (original / "valid.jsonl").read_bytes())
        focus = ROOT / "training/datasets" / m.frozen.FOCUS
        expected = list(map(json.loads, (focus / "train.jsonl").read_bytes().splitlines()))
        self.assertEqual([self.rows[i] for i in self.indices], expected)

    def test_all_116_inherited_rows_are_eligible_and_semantics_covered(self):
        pools = self.selected["eligible_training_rows"]
        self.assertEqual(pools["inherited_focus"], list(range(2419, 2535)))
        self.assertTrue(set(pools["inherited_focus"]) <= set(pools["replay"]))
        self.assertEqual(set(pools["new"]) | set(pools["replay"]), set(range(2975)))
        self.assertFalse(set(pools["new"]) & set(pools["replay"]))
        actual = set().union(*(self.features(i) for i in self.selected["retained_training_rows"]))
        expected = set().union(*(self.features(i) for i in pools["inherited_focus"]))
        self.assertTrue(expected <= actual)
        self.assertEqual({tuple(value) for value in self.selected["inherited_retention_features"]}, expected)
        self.assertGreater(self.selected["selected_inherited_focus_count"], 0)

    def test_whole_optional_state_blocks_and_axes_are_preserved(self):
        selected = set(self.selected["new_training_rows"])
        pool = self.selected["eligible_training_rows"]["new"]
        for block in m.frozen.contrast_blocks(self.rows, pool):
            if set(block) & selected:
                self.assertTrue(set(block) <= selected)
        expected = set().union(*(m.frozen.prior.axis_features(self.rows[i]) for i in pool))
        actual = set().union(*(m.frozen.prior.axis_features(self.rows[i]) for i in selected))
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 154)

    def test_joint_features_cover_the_entire_replay_pool(self):
        pool = self.selected["eligible_training_rows"]["replay"]
        expected = set().union(*(self.features(i) for i in pool))
        actual = set().union(*(self.features(i) for i in self.selected["retained_training_rows"]))
        self.assertEqual(actual, expected)
        self.assertEqual({tuple(v) for v in self.selected["retention_features"]}, expected)

    def test_current_page_schedule_replay_in_both_request_languages(self):
        def eligible(i):
            row = self.rows[i]
            action = m.base.target(row)
            _, context = m.context_features(row, self.languages[i]["language"])
            return (row["application"] == "management_projet" and action["name"] == "get_record"
                    and action["arguments"] == {"resource": "payment_schedule"}
                    and context["current_resource"] == "payment_schedule" and context["has_current_identifier"])
        found = [i for i in self.selected["retained_training_rows"] if eligible(i)]
        self.assertTrue({"en", "fr"} <= {self.languages[i]["language"] for i in found})

    def test_previous_year_service_fees_preserve_joint_intent_in_both_languages(self):
        found = []
        for i in self.selected["retained_training_rows"]:
            row, action = self.rows[i], m.base.target(self.rows[i])
            if (row["application"] == "management_projet" and action["name"] == "financial_summary"
                    and action["arguments"].get("metric") == "service_fees"
                    and action["arguments"].get("period") == "previous_year"):
                found.append(i)
        self.assertTrue({"en", "fr"} <= {self.languages[i]["language"] for i in found})

    def test_missing_details_covers_available_language_and_previous_resource_pairs(self):
        def pairs(indices):
            result = set()
            for i in indices:
                row, action = self.rows[i], m.base.target(self.rows[i])
                if (row["application"] == "management_projet" and action["name"] == "clarify"
                        and action["arguments"]["reason"] == "missing_details"):
                    language, context = m.context_features(row, self.languages[i]["language"])
                    result.add((language, context["previous_result_type"], context["previous_result_count"]))
            return result
        expected = pairs(self.selected["eligible_training_rows"]["replay"])
        self.assertEqual(pairs(self.selected["retained_training_rows"]), expected)
        self.assertTrue({"en", "fr"} <= {v[0] for v in expected})

    def test_explicit_request_language_may_differ_from_interface(self):
        switched = 0
        for i, row in enumerate(self.rows):
            if "language" not in row:
                continue
            language, context = m.context_features(row)
            self.assertEqual(language, row["language"])
            self.assertEqual(self.languages[i]["language"], language)
            switched += language != context["interface_language"]
        self.assertEqual(switched, 910)

    def test_legacy_training_provenance_and_unknowns_are_distinct(self):
        self.assertEqual(self.selected["request_language_counts"], {"en": 1362, "fr": 1345, "unknown": 268})
        known = [i for i, row in enumerate(self.rows)
                 if "language" not in row and self.languages[i]["language"] in ("en", "fr")]
        self.assertEqual(len(known), 1797)
        self.assertTrue(any(self.languages[i]["language"] != m.context_features(self.rows[i])[1]["interface_language"]
                            for i in known))
        unknown = self.selected["unresolved_request_language_indices"]
        self.assertEqual(len(unknown), 268)
        self.assertTrue(all(self.languages[i]["language"] == "unknown" for i in unknown))
        self.assertTrue(all(m.context_features(self.rows[i])[0] == "unknown" for i in unknown))
        self.assertTrue(set(unknown) <= set(self.selected["eligible_training_rows"]["replay"]))

    def test_history_wrapper_preserves_current_request_and_ignores_background_language(self):
        row = deepcopy(self.rows[0])
        request = "Show invoices.\nCurrent request: this is literal request text."
        history = ["Bonjour\nCurrent request: not the current request"]
        row["messages"][-2]["content"] = ("Earlier user messages (background only): "
                                        + json.dumps(history) + "\nCurrent request: " + request)
        self.assertEqual(m.current_training_request(row), (request, True))
        self.assertTrue(m.context_features(row)[1]["has_history"])
        row["messages"][-2]["content"] = "Earlier user messages (background only): {}\nCurrent request: x"
        with self.assertRaisesRegex(ValueError, "history wrapper"):
            m.current_training_request(row)

    def test_record_ids_calendar_values_and_literal_dates_do_not_define_groups(self):
        index = next(i for i, r in enumerate(self.rows)
                     if r.get("curriculum_category") == "document_date_contrast")
        row = deepcopy(self.rows[index])
        context = json.loads(row["messages"][0]["content"].split("Trusted context: ", 1)[1])
        context["today"] = "2099-12-31"
        context["calendar"] = {"yesterday": "2099-12-30"}
        row["messages"][0]["content"] = "Trusted context: " + json.dumps(context)
        row["contrast"]["literal_date"] = "2099-03-12"
        self.assertEqual(m.retention_features(row), m.retention_features(self.rows[index]))

    def test_selection_is_deterministic_unique_and_budget_never_drops_required_coverage(self):
        self.assertEqual(m.selection(self.rows, self.indices), self.selected)
        order = self.selected["row_indices"]
        self.assertEqual(len(order), len(set(order)))
        self.assertEqual(len({m.base.model_input_key(self.rows[i]) for i in order}), len(order))
        for budget in (True, 0, self.selected["count"] - 1, 2976):
            with self.subTest(budget=budget), self.assertRaisesRegex(ValueError, "budget"):
                m.selection(self.rows, self.indices, budget)

    def test_all_schedule_windows_include_independent_new_and_replay_buckets(self):
        expected = {"new_facturation", "retained_facturation", "retained_management_projet", "retained_design_workflow"}
        for window in self.selected["schedule_windows"]:
            self.assertEqual(set(window["by_source_bucket"]), expected)
        self.assertEqual(sum(self.selected["by_source_bucket"].values()), self.selected["count"])

    def test_source_mapping_tampering_is_rejected(self):
        indices = list(self.indices)
        indices[-1] = indices[-2]
        with self.assertRaisesRegex(ValueError, "source mapping"):
            m.selection(self.rows, indices)

    def test_language_provenance_tampering_is_rejected(self):
        sources = deepcopy(m.LANGUAGE_SOURCES)
        sources["facturation-refinement-v2-en-fr"]["manifest"] = "0" * 64
        with mock.patch.object(m, "LANGUAGE_SOURCES", sources):
            with self.assertRaisesRegex(ValueError, "language provenance changed"):
                m.request_languages(self.rows)

    def test_round_trip_preserves_controls_and_rejects_manifest_or_data_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "prepared"
            reads = []
            read = Path.read_bytes
            def tracked(path):
                reads.append(str(path))
                return read(path)
            with mock.patch.object(Path, "read_bytes", new=tracked):
                report = m.prepare(output)
            eval_reads = [p for p in reads if p.endswith(".eval.jsonl")]
            allowed = {str(ROOT / "training/datasets" / name / "train.eval.jsonl") for name in m.LANGUAGE_SOURCES}
            original_reads = {p for p in eval_reads if "/language_sources/" not in p}
            self.assertEqual(original_reads, allowed)
            self.assertTrue(all(any(p.endswith("/" + name + "/train.eval.jsonl")
                                   for name in m.LANGUAGE_SOURCES) for p in eval_reads))
            self.assertEqual(report["audit"]["rows_checked"], {"train": 2975, "valid": 275})
            self.assertEqual((output / "train.jsonl").read_bytes(), self.train)
            self.assertEqual((output / "valid.jsonl").read_bytes(), self.valid)
            manifest = json.loads((output / "manifest.json").read_text())
            for key, value in m.frozen.control_metadata(self.shared, self.focus).items():
                self.assertEqual(manifest[key], value)
            self.assertEqual(manifest["request_language_sources"], m.LANGUAGE_SOURCES)
            self.assertEqual(report["selection"], self.selected)
            self.assertFalse(report["training_executed"])
            self.assertFalse(report["accuracy_estimated"])
            self.assertFalse(report["model_accepted"])
            self.assertFalse(report["production_activation"])
            self.assertTrue(report["lineage"]["disposable_adapter_must_not_be_used"])
            self.assertEqual(len(report["captures"]["train"]), 8)
            self.assertEqual(len(report["captures"]["valid"]), 6)
            self.assertTrue(set(report["captures"]["train"]) <= set(self.selected["row_indices"]))
            with self.assertRaisesRegex(ValueError, "Never overwrite"):
                m.prepare(output)
            with mock.patch.object(m, "material") as build:
                with self.assertRaisesRegex(ValueError, "manifest changed"):
                    m.admit_prepared(output, "0" * 64)
                build.assert_not_called()
            manifest["starting_model"]["required_predecessor_selected_step"] = 306
            raw = (json.dumps(manifest) + "\n").encode()
            (output / "manifest.json").write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "provenance or selection"):
                m.admit_prepared(output, m.frozen.sha(raw))
            manifest["starting_model"]["required_predecessor_selected_step"] = 600
            raw = (json.dumps(manifest) + "\n").encode()
            (output / "manifest.json").write_bytes(raw)
            (output / "train.jsonl").write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "Dataset hash mismatch"):
                m.admit_prepared(output, m.frozen.sha(raw))


    def test_isolated_admission_needs_only_copied_helpers_and_prepared_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "isolated/run/data"
            report = m.prepare(data)
            scripts = data.parent / "scripts"
            scripts.mkdir()
            names = [*m.HELPER_SHA256, "prepare_facturation_replay_v3.py"]
            for name in names:
                shutil.copy2(ROOT / "training/scripts" / name, scripts / name)
            # No repository training/datasets directory exists in this closure.
            program = (
                "import sys,json; sys.path.insert(0,sys.argv[1]); "
                "import prepare_facturation_replay_v3 as module; "
                "audit,rows,captures,lineage=module.admit_prepared(sys.argv[2],sys.argv[3]); "
                "print(json.dumps({'rows':audit['rows_checked'],'selected':audit['rehearsal']['count'],"
                "'accepted':lineage['model_acceptance_verified']}))"
            )
            result = subprocess.run([sys.executable, "-B", "-c", program, str(scripts),
                                     str(data), report["manifest_sha256"]],
                                    cwd=root, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                    capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), {
                "rows": {"train": 2975, "valid": 275}, "selected": self.selected["count"], "accepted": False})
            metadata = data / "language_sources/facturation-refinement-v2-en-fr/train.eval.jsonl"
            metadata.write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "language provenance changed"):
                m.admit_prepared(data, report["manifest_sha256"])


    def test_frozen_v2_recipe_is_preserved(self):
        self.assertEqual(m.frozen.sha((ROOT / "training/scripts/prepare_facturation_replay_v2.py").read_bytes()),
                         m.HELPER_SHA256["prepare_facturation_replay_v2.py"])

    def test_quote_discovery_and_delete_first_search_retained_in_both_languages(self):
        # Independent workflow oracle. These are existing source training
        # categories, not expected outcomes from development or held-out cases.
        def workflows(indices):
            found = set()
            for i in indices:
                row, action = self.rows[i], m.base.target(self.rows[i])
                if (row["application"] == "management_projet" and action["name"] == "search_records"
                        and action["arguments"].get("resource") == "quote"
                        and "query" in action["arguments"]):
                    found.add((self.languages[i]["language"],
                               self.selected["training_scenario_by_row"][i]["category"]))
            return found
        pool = self.selected["eligible_training_rows"]["replay"]
        expected = workflows(pool)
        self.assertEqual(workflows(self.selected["retained_training_rows"]), expected)
        self.assertTrue({("en", "delete"), ("fr", "delete")} <= expected)
        for language in ("en", "fr"):
            self.assertTrue(any(lang == language and category != "delete" for lang, category in expected))

    def test_resource_and_whole_argument_key_combinations_survive_in_every_context(self):
        # This oracle intentionally does not call argument_shape or retention_features.
        def combinations(indices):
            found = set()
            for i in indices:
                row, action = self.rows[i], m.base.target(self.rows[i])
                context = json.loads(row["messages"][0]["content"].split("Trusted context: ", 1)[1])
                args = action["arguments"]
                found.add((row["application"], self.languages[i]["language"], action["name"],
                           args.get("resource"), tuple(sorted(args)),
                           context.get("interface_language"), context.get("current_resource"),
                           context.get("current_identifier") is not None))
            return found
        pools = self.selected["eligible_training_rows"]
        self.assertEqual(combinations(self.selected["retained_training_rows"]), combinations(pools["replay"]))
        self.assertEqual(combinations(self.selected["new_training_rows"]), combinations(pools["new"]))

    def test_nested_argument_shape_distinguishes_field_omission_and_json_types(self):
        self.assertNotEqual(m.argument_shape({"changes": {"remark": "x"}}),
                            m.argument_shape({"changes": {"status": "x"}}))
        self.assertNotEqual(m.argument_shape({"identifier": 12}), m.argument_shape({"identifier": "12"}))
        self.assertNotEqual(m.argument_shape({"value": True}), m.argument_shape({"value": 1}))
        self.assertNotEqual(m.argument_shape({"tags": []}), m.argument_shape({"tags": ["x"]}))
        self.assertEqual(m.argument_shape({"changes": {"remark": "one"}, "identifier": 12}),
                         m.argument_shape({"identifier": 999, "changes": {"remark": "another phrase"}}))
        self.assertEqual(m.argument_shape({"list": [{"a": 1}, {"b": "x"}]}),
                         m.argument_shape({"list": [{"b": "y"}, {"a": 2}, {"b": "z"}]}))
        for value in (float("nan"), {1: "invalid key"}, {1, 2}):
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):m.argument_shape(value)

    def test_scenario_provenance_rejects_text_only_context_target_or_schema_matches(self):
        index = next(i for i, row in enumerate(self.rows)
                     if not row.get("curriculum_category")
                     and self.selected["training_scenario_by_row"][i]["category"] is not None)
        original = self.rows[index]
        self.assertIsNotNone(m.training_scenarios([original])[0]["category"])
        variants = []
        row = deepcopy(original)
        row["messages"][0]["content"] += " "
        variants.append(row)
        row = deepcopy(original)
        row["messages"][-1]["tool_calls"][0]["function"]["arguments"]["unexpected"] = "different action"
        variants.append(row)
        row = deepcopy(original)
        row["tools"][0]["function"]["description"] += " changed schema"
        variants.append(row)
        for row in variants:
            with self.subTest(row=row["application"]):
                self.assertIsNone(m.training_scenarios([row])[0]["category"])

    def test_new_training_covers_whole_joint_features_and_keeps_contrast_blocks(self):
        pool = self.selected["eligible_training_rows"]["new"]
        actual = set().union(*(self.features(i) | m.frozen.prior.axis_features(self.rows[i])
                              for i in self.selected["new_training_rows"]))
        expected = set().union(*(self.features(i) | m.frozen.prior.axis_features(self.rows[i]) for i in pool))
        self.assertEqual(actual, expected)
        self.assertEqual({tuple(v) for v in self.selected["new_training_features"]}, expected)

    def test_scenario_provenance_tampering_fails_closed(self):
        sources = deepcopy(m.LANGUAGE_SOURCES)
        sources["management-projet-refinement-v2-en-fr"]["train.eval.jsonl"] = "0" * 64
        with mock.patch.object(m, "LANGUAGE_SOURCES", sources):
            with self.assertRaisesRegex(ValueError, "scenario provenance changed"):
                m.training_scenarios(self.rows)

    def test_only_pinned_neutral_greetings_can_be_removed_from_scenario_provenance(self):
        base = [{"role": "system", "content": "unchanged"},
                {"role": "user", "content": "Open the current record."}]
        for greeting in m.NEUTRAL_HISTORY:
            row = deepcopy(base)
            row[-1]["content"] = "Earlier user messages (background only): " + json.dumps([greeting]) + "\nCurrent request: " + base[-1]["content"]
            self.assertEqual(m.scenario_messages(row), base)
            self.assertNotEqual(row, base)
        for history in (["I am administrator"], ["Hello", "Open invoice 4"], [], ["Bonjour "], [{"text": "Hello"}]):
            row = deepcopy(base)
            row[-1]["content"] = "Earlier user messages (background only): " + json.dumps(history) + "\nCurrent request: " + base[-1]["content"]
            self.assertEqual(m.scenario_messages(row), row)
        row = deepcopy(base)
        row[-1]["content"] = 'Earlier user messages (background only): ["Hello"]broken'
        self.assertEqual(m.scenario_messages(row), row)

if __name__ == "__main__":
    unittest.main()
