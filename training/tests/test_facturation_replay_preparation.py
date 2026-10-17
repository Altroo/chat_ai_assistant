"""Regression checks for coherent training contrasts and explicit replay."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import audit_training_inputs as base
import prepare_facturation_replay_v1 as m


class FacturationReplayPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared, cls.focus, cls.rows, cls.train, cls.valid, cls.indices = m.combined()
        cls.selected = m.selection(cls.rows, cls.indices)

    def test_all_source_inputs_and_targets_are_retained(self):
        original = ROOT / "training/datasets" / m.SHARED
        self.assertTrue(self.train.startswith((original / "train.jsonl").read_bytes()))
        self.assertEqual(self.valid, (original / "valid.jsonl").read_bytes())
        focus = ROOT / "training/datasets" / m.FOCUS
        source = [json.loads(line) for line in (focus / "train.jsonl").read_bytes().splitlines()]
        self.assertEqual(len(self.rows), 2975)
        for row, index in zip(source, self.indices):
            self.assertEqual(self.rows[index], row)
        self.assertEqual(Counter(r["application"] for r in self.rows),
                         Counter(facturation=1487, management_projet=1012, design_workflow=476))

    def test_selected_matrix_families_keep_every_optional_state(self):
        selected = set(self.selected["new_training_rows"])
        blocks = m.contrast_blocks(self.rows, self.indices[1047:])
        used = [block for block in blocks if selected & set(block)]
        for block in used:
            self.assertTrue(set(block) <= selected)
        matrix = [block for block in used if self.rows[block[0]]["curriculum_category"] in m.MATRIX]
        self.assertEqual(len(matrix), 20)
        self.assertEqual(sum(map(len, matrix)), 80)
        for block in matrix:
            self.assertEqual({self.rows[i]["contrast"]["optional_state"] for i in block}, m.STATES)

    def test_all_existing_declared_contrast_axes_survive(self):
        expected = set().union(*(m.prior.axis_features(self.rows[i]) for i in self.indices[1047:]))
        actual = set().union(*(m.prior.axis_features(self.rows[i]) for i in self.selected["new_training_rows"]))
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 154)

    def test_replay_covers_old_tools_arguments_and_intents_independently(self):
        expected = set().union(*(m.retention_features(r) for r in self.rows[:2419]))
        actual = set().union(*(m.retention_features(self.rows[i]) for i in self.selected["retained_training_rows"]))
        self.assertEqual(actual, expected)
        self.assertTrue(all(i < 2419 for i in self.selected["retained_training_rows"]))
        for tool in ("search_invoices", "search_documents", "search_operations", "search_quotes", "search_payments"):
            self.assertTrue(any(self.rows[i]["application"] == "facturation" and base.target(self.rows[i])["name"] == tool
                                for i in self.selected["retained_training_rows"]), tool)

    def test_all_schedule_windows_and_tail_have_explicit_replay(self):
        buckets = {"new_facturation", "retained_facturation", "retained_management_projet", "retained_design_workflow"}
        for window in self.selected["schedule_windows"]:
            counts = window["by_source_bucket"]
            self.assertEqual(set(counts), buckets)
            self.assertGreaterEqual(sum(v for k, v in counts.items() if k.startswith("retained_")),
                                    counts["new_facturation"])
        self.assertEqual(self.selected["by_source_bucket"],
                         {"new_facturation": 126, "retained_facturation": 90,
                          "retained_management_projet": 57, "retained_design_workflow": 33})

    def test_selection_is_unique_deterministic_and_fails_small_budget(self):
        self.assertEqual(m.selection(self.rows, self.indices), self.selected)
        order = self.selected["row_indices"]
        self.assertEqual(len(order), len(set(order)))
        self.assertEqual(len({base.model_input_key(self.rows[i]) for i in order}), len(order))
        for budget in (True, 0, 305, 321):
            with self.subTest(budget=budget), self.assertRaisesRegex(ValueError, "budget"):
                m.selection(self.rows, self.indices, budget)

    def test_incomplete_contrast_group_is_rejected(self):
        candidates = list(self.indices[1047:])
        matrix_index = next(i for i in candidates if self.rows[i]["curriculum_category"] in m.MATRIX)
        candidates.remove(matrix_index)
        with self.assertRaisesRegex(ValueError, "all four optional states"):
            m.contrast_blocks(self.rows, candidates)

    def test_uncontrolled_contrast_target_change_is_rejected(self):
        rows = list(self.rows)
        index = next(i for i in self.indices[1047:] if self.rows[i]["curriculum_category"] in m.MATRIX
                     and self.rows[i]["contrast"]["optional_state"] == "first")
        rows[index] = deepcopy(rows[index])
        base.target(rows[index])["arguments"]["date_from"] = "2099-01-01"
        with self.assertRaisesRegex(ValueError, "more than its declared optional field"):
            m.contrast_blocks(rows, self.indices[1047:])

    def test_source_manifest_tampering_fails_before_split_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "training/datasets" / m.FOCUS
            path.mkdir(parents=True)
            (path / "manifest.json").write_text("{}")
            with mock.patch.object(m, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "manifest changed"):
                    m.source(m.FOCUS, m.FOCUS_SHA256)

    def test_source_label_conflicts_are_rejected(self):
        shared = m.source(m.SHARED, m.SHARED_SHA256)
        focus = list(m.source(m.FOCUS, m.FOCUS_SHA256))
        focus[2] = dict(focus[2])
        focus[2]["train"] = list(focus[2]["train"])
        focus[2]["train"][0] = deepcopy(focus[2]["train"][0])
        base.target(focus[2]["train"][0])["arguments"]["limit"] = 999
        with mock.patch.object(m, "source", side_effect=[shared, tuple(focus)]):
            with self.assertRaisesRegex(ValueError, "contradictory targets"):
                m.combined()

    def test_parent_fresh_controls_disagreement_is_rejected(self):
        focus = deepcopy(self.focus)
        focus["fresh_controls"]["scoring"] = "invalid changed scoring policy"
        with self.assertRaisesRegex(ValueError, "fresh-controls identities or scoring policies disagree"):
            m.control_metadata(self.shared, focus)

    def test_preparation_round_trip_is_metadata_only_and_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            seen = []
            read = Path.read_bytes
            def tracked(path):
                seen.append(str(path))
                return read(path)
            with mock.patch.object(Path, "read_bytes", new=tracked):
                result = m.prepare(output)
            self.assertFalse(any(path.endswith(".eval.jsonl") for path in seen))
            self.assertEqual(result["audit"]["rows_checked"], {"train": 2975, "valid": 275})
            self.assertEqual(result["audit"]["exact_input_label_conflicts"], 0)
            self.assertEqual(result["audit"]["exact_input_cross_split_overlap"], 0)
            self.assertFalse(result["training_executed"])
            self.assertFalse(result["accuracy_estimated"])
            self.assertFalse(result["model_accepted"])
            self.assertFalse(result["production_activation"])
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["fresh_controls"], self.shared["fresh_controls"])
            self.assertEqual(manifest["fresh_controls"], self.focus["fresh_controls"])
            for name in ("evaluation_manifest_sha256", "historical_evaluation_manifest_sha256", "held_out_count"):
                self.assertEqual(manifest[name], self.shared[name])
            for name in ("held_out", "historical_regression_held_out"):
                for key, identity in self.shared[name].items():
                    self.assertEqual(manifest[name][key], identity)
                for key, identity in self.focus[name].items():
                    self.assertEqual(manifest[name][key], identity)
            captures = result["captures"]
            self.assertEqual(len(captures["train"]), 8)
            self.assertEqual(len(captures["valid"]), 6)
            self.assertEqual(captures["total"], 14)
            self.assertTrue(set(captures["train"]) <= set(result["selection"]["row_indices"]))
            valid_rows = [json.loads(line) for line in self.valid.splitlines()]
            self.assertEqual(Counter(valid_rows[i]["application"] for i in captures["valid"]),
                             Counter(facturation=2, management_projet=2, design_workflow=2))
            audit, admitted, admitted_captures, lineage = m.admit_prepared(output, result["manifest_sha256"])
            self.assertEqual(audit["rehearsal"], result["selection"])
            self.assertEqual(len(admitted["train"]), 2975)
            self.assertEqual(admitted_captures["train"], captures["train"])
            self.assertEqual(admitted_captures["valid"], captures["valid"])
            self.assertTrue(lineage["actual_model_binding_required_before_numerical_work"])
            self.assertFalse(lineage["longer_training_admitted"])
            with self.assertRaisesRegex(ValueError, "Never overwrite"):
                m.prepare(output)
            with mock.patch.object(base, "audit") as audit_call:
                with self.assertRaisesRegex(ValueError, "preparation manifest changed"):
                    m.admit_prepared(output, "0" * 64)
                audit_call.assert_not_called()
            (output / "train.jsonl").write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "Dataset hash mismatch"):
                m.admit_prepared(output, result["manifest_sha256"])


if __name__ == "__main__":
    unittest.main()
