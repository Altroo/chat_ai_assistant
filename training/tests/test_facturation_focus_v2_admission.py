"""Coverage and fail-closed admission for the disposable Facturation V2 pilot."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import audit_training_inputs as base
import facturation_focus_v2_admission as m
import rehearse_facturation_v2 as runner

DATA = ROOT / "training/datasets/facturation-focus-v2-en-fr"
PARENT = DATA.parent / "facturation-focus-v1-en-fr"


class FacturationPilotV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit, cls.rows, cls.captures, cls.lineage = m.prepare_inputs(DATA, "facturation", None)
        cls.selected = cls.audit["rehearsal"]["row_indices"]

    def test_real_data_bounded_unique_and_retained(self):
        selected = self.audit["rehearsal"]
        self.assertEqual(self.audit["rows_checked"], {"train": 1487, "valid": 133})
        self.assertEqual(selected["count"], 92)
        self.assertEqual(len(selected["added_training_rows"]), 78)
        self.assertEqual(len(selected["retained_training_sentinels"]), 14)
        self.assertEqual(len(self.selected), len(set(self.selected)))
        self.assertTrue(all(i < 1047 for i in selected["retained_training_sentinels"]))
        self.assertTrue(all(i >= 1047 for i in selected["added_training_rows"]))
        self.assertTrue((DATA / "train.jsonl").read_bytes().startswith((PARENT / "train.jsonl").read_bytes()))
        self.assertEqual((DATA / "valid.jsonl").read_bytes(), (PARENT / "valid.jsonl").read_bytes())
        self.assertFalse(self.lineage["model_acceptance_verified"])
        self.assertFalse(self.lineage["longer_training_admitted"])

    def test_matrix_pairs_and_language_marginals_are_covered(self):
        for category, modes in (
                ("date_optional_document", {"none", "lower", "upper", "month"}),
                ("date_optional_operation", {"none", "lower", "upper", "day"})):
            values = [self.rows["train"][i] for i in self.selected
                      if self.rows["train"][i].get("curriculum_category") == category]
            self.assertEqual({(r["contrast"]["mode"], r["contrast"]["optional_state"]) for r in values},
                             {(mode, state) for mode in modes for state in ("none", "first", "second", "limit")})
            self.assertEqual({(r["contrast"]["mode"], r["language"]) for r in values},
                             {(mode, lang) for mode in modes for lang in ("en", "fr")})
            self.assertEqual({(r["contrast"]["optional_state"], r["language"]) for r in values},
                             {(state, lang) for state in ("none", "first", "second", "limit") for lang in ("en", "fr")})
            resource = lambda r: base.target(r)["arguments"].get("resource", base.target(r)["name"])
            self.assertEqual(len({(resource(r), r["language"]) for r in values}), 10)

    def test_all_declared_axes_and_existing_tool_groups(self):
        rows = self.rows["train"]
        added = self.audit["rehearsal"]["added_training_rows"]
        required_axes = set().union(*(m.axis_features(row) for row in rows[1047:]))
        actual_axes = set().union(*(m.axis_features(rows[i]) for i in added))
        self.assertEqual(actual_axes, required_axes)
        self.assertEqual(len(actual_axes), 154)
        expected = set().union(*(base.features(row) for row in rows))
        actual = set().union(*(base.features(rows[i]) for i in self.selected))
        self.assertEqual(actual, expected)
        self.assertEqual({(rows[i]["curriculum_category"], rows[i]["language"]) for i in added},
                         {(category, lang) for category in m.FOCUS_CATEGORIES for lang in ("en", "fr")})

    def test_deterministic_and_budget_cannot_drop_axes(self):
        self.assertEqual(m.balanced_selection(self.rows["train"]), self.audit["rehearsal"])
        for budget in (True, 0, 91, 97):
            with self.subTest(budget=budget), self.assertRaisesRegex(ValueError, "budget"):
                m.balanced_selection(self.rows["train"], budget)

    def test_captures_are_bounded_selected_and_have_each_category(self):
        self.assertEqual(len(self.captures["train"]), 12)
        self.assertEqual(len(self.captures["valid"]), 2)
        self.assertTrue(set(self.captures["train"]) <= set(self.selected))
        selected_categories = {self.rows["train"][i].get("curriculum_category")
                               for i in self.captures["train"] if i >= 1047}
        self.assertEqual(selected_categories, set(m.FOCUS_CATEGORIES))
        expected_valid = m.ordered_indices(self.rows["valid"], range(133))[:2]
        self.assertEqual(self.captures["valid"], expected_valid)

    def test_other_stage_or_lineage_options_reject_before_reading(self):
        for stage, retained, correction in (
                ("shared", None, None), ("contrat", None, None),
                ("facturation", PARENT, None), ("facturation", None, Path("correction"))):
            with self.subTest(stage=stage), self.assertRaisesRegex(ValueError, "Facturation only"):
                m.prepare_inputs(Path("absent"), stage, retained, correction)

    def test_missing_or_duplicate_categories_reject(self):
        for categories in (m.FOCUS_CATEGORIES[:-1], (*m.FOCUS_CATEGORIES, m.FOCUS_CATEGORIES[0])):
            with self.assertRaisesRegex(ValueError, "Every published pilot category"):
                m.prepare_inputs(DATA, "facturation", None, categories=categories)

    def test_changed_manifest_rejects_before_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            (data / "manifest.json").write_text("{}")
            with mock.patch.object(base, "audit") as audit:
                with self.assertRaisesRegex(ValueError, "pilot manifest changed"):
                    m.prepare_inputs(data, "facturation", None)
                audit.assert_not_called()

    def test_parent_substitution_rejects_before_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / PARENT.name
            data = Path(directory) / DATA.name
            parent.mkdir()
            data.mkdir()
            shutil.copyfile(DATA / "manifest.json", data / "manifest.json")
            (parent / "manifest.json").write_text("{}")
            with mock.patch.object(base, "audit") as audit:
                with self.assertRaisesRegex(ValueError, "parent manifest changed"):
                    m.prepare_inputs(data, "facturation", None)
                audit.assert_not_called()

    def test_retained_bytes_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / PARENT.name
            data = Path(directory) / DATA.name
            shutil.copytree(PARENT, parent)
            shutil.copytree(DATA, data)
            raw = (data / "train.jsonl").read_bytes()
            (data / "train.jsonl").write_bytes(raw[raw.index(b"\n") + 1:])
            with mock.patch.object(base, "audit") as audit:
                with self.assertRaisesRegex(ValueError, "every parent training"):
                    m.prepare_inputs(data, "facturation", None)
                audit.assert_not_called()

    def test_numerical_capture_resource_code_unchanged(self):
        def functions(name):
            tree = ast.parse((ROOT / "training/scripts" / name).read_text())
            return {n.name: ast.dump(n, include_attributes=False) for n in tree.body
                    if isinstance(n, ast.FunctionDef)}
        before = functions("rehearse_facturation_v1.py")
        after = functions("rehearse_facturation_v2.py")
        for name in ("run", "capture", "trainer_functions", "frozen_parameter_digest",
                     "no_other_jobs", "assert_idle_units", "verify_sources", "validate_options"):
            self.assertEqual(before[name], after[name], name)
        self.assertEqual(runner.FOCUS_CATEGORIES, m.FOCUS_CATEGORIES)
        self.assertEqual(runner.FOCUS_MANIFEST_SHA256, m.FOCUS_MANIFEST_SHA256)
        self.assertIn("facturation_focus_v2_admission.py", runner.DEPENDENCY_NAMES)

    def test_other_optimizer_or_evaluation_blocks(self):
        for filename in ("rehearse_facturation_v1.py", "rehearse_facturation_v2.py",
                         "train_cpu.py", "probe_cpu_selective.py"):
            process = SimpleNamespace(info={"pid": runner.os.getpid() + 100000,
                                            "cmdline": ["python", "/isolated/" + filename]})
            psutil = SimpleNamespace(process_iter=lambda fields: [process],
                NoSuchProcess=type("NoSuchProcess", (Exception,), {}),
                AccessDenied=type("AccessDenied", (Exception,), {}))
            with self.subTest(filename=filename), self.assertRaisesRegex(RuntimeError, "Another trainer"):
                runner.no_other_optimizer(psutil)
        with self.assertRaisesRegex(RuntimeError, "Another training, export or evaluation"):
            runner.assert_idle_units("chat-ai-fact-focus-v1-eval-acceptance-600-0.service loaded active running", "")


if __name__ == "__main__":
    unittest.main()
