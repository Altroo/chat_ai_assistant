"""Category rehearsal selects real training coverage without altering frozen audits."""
import ast
import copy
import json
import os
from types import SimpleNamespace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import audit_training_inputs as old
import audit_training_inputs_v2 as current
import rehearse_cpu_v2 as previous_runner
import rehearse_cpu_v3 as runner


class CategoryRehearsalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = ROOT / "training/datasets/shared-v5r10-en-fr"
        cls.rows = list(map(json.loads, (cls.data / "train.jsonl").read_text().splitlines()))
        cls.categories = sorted(json.loads((cls.data / "manifest.json").read_text())["counts"]["added_categories"])
        cls.base = old.audit(cls.data)
        cls.extended = current.audit(cls.data, categories=cls.categories)

    def test_default_audit_and_capture_order_unchanged(self):
        self.assertEqual(current.audit(self.data), self.base)
        self.assertEqual(runner.prepare_inputs(self.data, "shared", None),
                         previous_runner.prepare_inputs(self.data, "shared", None))

    def test_each_added_category_and_language_is_rehearsed_and_captured(self):
        audit, rows, captures, lineage = runner.prepare_inputs(self.data, "shared", None, categories=self.categories)
        plan = audit["rehearsal"]
        self.assertTrue(set(self.base["rehearsal"]["row_indices"]) <= set(plan["row_indices"]))
        self.assertEqual(plan, self.extended["rehearsal"])
        actual = {(r["category"], r["language"]) for r in plan["category_coverage"]}
        self.assertEqual(actual, {(c, lang) for c in self.categories for lang in ("en", "fr")})
        for item in plan["category_coverage"]:
            self.assertGreaterEqual(item["row_index"], 2339)
            self.assertIn(item["row_index"], captures["train"])
            self.assertIn(item["row_index"], plan["row_indices"])
        self.assertEqual(len(plan["row_indices"]), len(set(plan["row_indices"])))
        self.assertIsNone(lineage)

    def test_absent_duplicate_or_monolingual_category_rejects(self):
        for categories in (["absent_category"], ["custom_receipts", "custom_receipts"]):
            with self.assertRaises(ValueError):
                current.extend_rehearsal(self.rows, self.base["rehearsal"], categories)
        rows = [r for r in self.rows if r.get("curriculum_category") == "custom_receipts" and r["language"] == "en"]
        with self.assertRaisesRegex(ValueError, "both languages"):
            current.extend_rehearsal(rows, old.rehearsal(rows, 96), ["custom_receipts"])

    def test_budget_does_not_silently_drop_coverage(self):
        with self.assertRaisesRegex(ValueError, "budget"):
            current.extend_rehearsal(self.rows, self.base["rehearsal"], self.categories, maximum=48)

    def test_previous_and_current_rehearsals_block_concurrent_start(self):
        class Missing(Exception):
            pass
        for script in ("rehearse_cpu.py", "rehearse_cpu_v2.py", "rehearse_cpu_v3.py"):
            process = SimpleNamespace(info={"pid": os.getpid()+10000,
                "cmdline": ["python", "-B", "/synthetic/" + script]})
            fake = SimpleNamespace(NoSuchProcess=Missing, AccessDenied=Missing,
                process_iter=lambda fields: [process])
            with self.subTest(script=script), self.assertRaisesRegex(RuntimeError, "Another trainer"):
                runner.no_other_optimizer(fake)

    def test_numerical_and_resource_functions_are_unchanged(self):
        def functions(name):
            tree = ast.parse((ROOT / "training/scripts" / name).read_text())
            return {node.name: ast.dump(node, include_attributes=False) for node in tree.body if isinstance(node, ast.FunctionDef)}
        before, after = functions("rehearse_cpu_v2.py"), functions("rehearse_cpu_v3.py")
        self.assertEqual(set(before), set(after))
        changed = {name for name in before if before[name] != after[name]}
        self.assertEqual(changed, {"prepare_inputs", "run", "main", "no_other_optimizer"})
        self.assertIn("audit_training_inputs_v2.py", runner.DEPENDENCY_NAMES)


if __name__ == "__main__":
    unittest.main()
