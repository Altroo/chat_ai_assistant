"""Focused rehearsal admission must reject other apps and retain trainer mechanics."""
import ast
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import rehearse_facturation_v1 as m

DATA = ROOT / "training/datasets/facturation-focus-v1-en-fr"


class FacturationRehearsalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checked, cls.rows, cls.captures, cls.lineage = m.prepare_inputs(
            DATA, "facturation", None)

    def test_real_focused_data_and_bilingual_categories_admitted(self):
        self.assertEqual(self.checked["rows_checked"], {"train": 1047, "valid": 133})
        self.assertEqual(self.lineage["retained_training_rows_byte_identical"], 931)
        self.assertFalse(self.lineage["model_acceptance_verified"])
        self.assertEqual({r["application"] for values in self.rows.values() for r in values}, {"facturation"})
        selected = self.checked["rehearsal"]["row_indices"]
        self.assertTrue(set(self.captures["train"]) <= set(selected))
        categories = {(self.rows["train"][i].get("curriculum_category"),
                       self.rows["train"][i].get("language")) for i in self.captures["train"]}
        self.assertTrue({(c, lang) for c in m.FOCUS_CATEGORIES for lang in ("en", "fr")} <= categories)
        self.assertEqual(len(self.captures["valid"]), 2)

    def test_wrong_stage_and_lineage_options_reject_before_reading_data(self):
        for stage, retained, corrections in (("shared", None, None), ("contrat", None, None),
                                            ("facturation", Path("other"), None),
                                            ("facturation", None, Path("other"))):
            with self.subTest(stage=stage, retained=retained, corrections=corrections):
                with self.assertRaisesRegex(ValueError, "Facturation only"):
                    m.prepare_inputs(Path("missing"), stage, retained, corrections)

    def test_category_omission_rejects(self):
        with self.assertRaisesRegex(ValueError, "Every published focus category"):
            m.prepare_inputs(DATA, "facturation", None, categories=m.FOCUS_CATEGORIES[:-1])

    def test_default_cli_records_the_effective_categories(self):
        arguments = ["rehearse_facturation_v1.py", "--stage", "facturation",
                     "--model", "model", "--data", "data", "--runtime", "runtime",
                     "--trainer", "train_cpu.py", "--output", "output",
                     "--trainer-sha256", "pinned", "--threads", "14",
                     "--max-seq-length", "8192", "--learning-rate", "0.00001",
                     "--semantic-loss-weight", "4", "--lora-layers", "24",
                     "--lora-rank", "16", "--lora-alpha", "32"]
        with mock.patch.object(sys, "argv", arguments), mock.patch.object(m, "run") as run:
            m.main()
        self.assertEqual(run.call_args.args[0].rehearsal_categories, list(m.FOCUS_CATEGORIES))
        with self.assertRaisesRegex(ValueError, "Every published focus category"):
            m.prepare_inputs(DATA, "facturation", None,
                             categories=(*m.FOCUS_CATEGORIES, m.FOCUS_CATEGORIES[0]))

    def test_changed_manifest_cannot_admit_arbitrary_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "manifest.json").write_text('{"applications":["facturation"]}')
            with self.assertRaisesRegex(ValueError, "manifest changed"):
                m.prepare_inputs(path, "facturation", None)

    def test_other_rehearsals_and_capacity_probe_block_numerical_work(self):
        for filename in ("rehearse_cpu_v2.py", "rehearse_cpu_v3.py",
                         "rehearse_facturation_v1.py", "probe_cpu_selective.py"):
            with self.subTest(filename=filename):
                process = SimpleNamespace(info={"pid": m.os.getpid() + 100000,
                                                "cmdline": ["python", "/isolated/" + filename]})
                psutil = SimpleNamespace(process_iter=lambda fields: [process],
                                         NoSuchProcess=type("NoSuchProcess", (Exception,), {}),
                                         AccessDenied=type("AccessDenied", (Exception,), {}))
                with self.assertRaisesRegex(RuntimeError, "Another trainer or rehearsal"):
                    m.no_other_optimizer(psutil)

    def test_numerical_capture_and_resource_functions_are_unchanged(self):
        def functions(path):
            return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body
                    if isinstance(n, ast.FunctionDef)}
        before = functions(ROOT / "training/scripts/rehearse_cpu_v3.py")
        after = functions(ROOT / "training/scripts/rehearse_facturation_v1.py")
        for name in ("run", "capture", "trainer_functions", "frozen_parameter_digest",
                     "no_other_jobs", "assert_idle_units", "verify_sources", "capture_indices"):
            self.assertEqual(before[name], after[name], name)


if __name__ == "__main__":
    unittest.main()
