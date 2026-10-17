"""Numerical parity and fail-closed admission for the replay-preserving pilot."""
import ast
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import prepare_facturation_replay_v2 as preparation
import rehearse_facturation_replay_v2 as current


class FacturationReplayRunnerTests(unittest.TestCase):
    def test_numerical_capture_and_resource_functions_remain_identical(self):
        def functions(name):
            return {node.name: ast.dump(node, include_attributes=False)
                    for node in ast.parse((ROOT / "training/scripts" / name).read_text()).body
                    if isinstance(node, ast.FunctionDef)}
        old = functions("rehearse_facturation_replay_v1.py")
        new = functions("rehearse_facturation_replay_v2.py")
        self.assertEqual(set(old), set(new))
        self.assertEqual({name for name in old if old[name] != new[name]},
                         {"prepare_inputs", "no_other_optimizer"})
        for name in ("run", "capture", "trainer_functions", "frozen_parameter_digest",
                     "validate_options", "verify_sources", "no_other_jobs", "assert_idle_units"):
            self.assertEqual(old[name], new[name], name)

    def test_only_pinned_preparation_is_delegated(self):
        expected = object()
        with mock.patch.object(preparation, "admit_prepared", return_value=expected) as admit:
            self.assertIs(current.prepare_inputs(Path("prepared"), "facturation", None), expected)
            admit.assert_called_once_with(Path("prepared"), current.FOCUS_MANIFEST_SHA256)

    def test_foreign_scope_or_partial_categories_reject_before_admission(self):
        with mock.patch.object(preparation, "admit_prepared") as admit:
            for stage, retained, correction, categories in (
                    ("contrat", None, None, ()),
                    ("shared", None, None, ()),
                    ("facturation", Path("other"), None, ()),
                    ("facturation", None, Path("other"), ()),
                    ("facturation", None, None, current.FOCUS_CATEGORIES[:-1]),
                    ("facturation", None, None, (*current.FOCUS_CATEGORIES, current.FOCUS_CATEGORIES[0]))):
                with self.subTest(stage=stage), self.assertRaises(ValueError):
                    current.prepare_inputs(Path("absent"), stage, retained, correction, categories=categories)
            admit.assert_not_called()

    def test_real_preparation_matches_runner_pin_and_shared_replay_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "data"
            report = preparation.prepare(data)
            self.assertEqual(report["manifest_sha256"], current.FOCUS_MANIFEST_SHA256)
            audit, rows, captures, lineage = current.prepare_inputs(data, "facturation", None)
            self.assertEqual(audit["rehearsal"]["count"], 1171)
            self.assertEqual({r["application"] for r in rows["train"]},
                             {"facturation", "management_projet", "design_workflow"})
            self.assertEqual({name: len(values) for name, values in captures.items()}, {"train": 8, "valid": 6})
            self.assertFalse(lineage["model_acceptance_verified"])
            self.assertFalse(lineage["longer_training_admitted"])

    def test_other_new_old_and_serial_optimizer_processes_block(self):
        for filename in ("rehearse_facturation_v2.py", "rehearse_facturation_replay_v1.py", "rehearse_facturation_replay_v2.py",
                         "train_cpu_serial_v4.py", "train_cpu.py"):
            process = SimpleNamespace(info={"pid": current.os.getpid() + 100000,
                                            "cmdline": ["python", "/isolated/" + filename]})
            psutil = SimpleNamespace(process_iter=lambda fields: [process],
                NoSuchProcess=type("NoSuchProcess", (Exception,), {}),
                AccessDenied=type("AccessDenied", (Exception,), {}))
            with self.subTest(filename=filename), self.assertRaisesRegex(RuntimeError, "Another trainer"):
                current.no_other_optimizer(psutil)

    def test_local_numerical_execution_is_rejected(self):
        with mock.patch.object(current.platform, "system", return_value="Darwin"), \
             mock.patch.dict(current.os.environ, {"CHAT_AI_TRAINING_SERVER": "1"}):
            with self.assertRaisesRegex(ValueError, "approved Linux server"):
                current.validate_options(SimpleNamespace())

    def test_new_metadata_helper_is_in_numerical_source_inventory(self):
        self.assertIn("prepare_facturation_replay_v2.py", current.DEPENDENCY_NAMES)
        self.assertIn("facturation_focus_v2_admission.py", current.DEPENDENCY_NAMES)
        self.assertIn("prepare_facturation_replay_v2.py", current.SOURCE_SHA256)


if __name__ == "__main__":
    unittest.main()
