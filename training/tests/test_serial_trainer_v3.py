"""Exercise real serial trainer startup gates without importing model libraries."""
import builtins
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))


class BeforeWeights(Exception):
    pass


class SerialTrainerStartupTests(unittest.TestCase):
    def start(self, stage, retained, extra=None):
        original_import = builtins.__import__
        def bounded_import(name, *args, **kwargs):
            if name == "torch":
                raise BeforeWeights
            return original_import(name, *args, **kwargs)
        with tempfile.TemporaryDirectory() as directory:
            args = ["train_cpu_serial_v3.py", "--stage", stage,
                    "--retained-data", str(ROOT / "training/datasets" / retained),
                    "--data", str(ROOT / "training/datasets/shared-v6r5-en-fr"),
                    "--model", str(Path(directory) / "unused-model"),
                    "--output", str(Path(directory) / "unused-output"),
                    *(extra if extra is not None else ["--complete-epochs", "1"])]
            with patch.object(sys, "argv", args), patch("platform.system", return_value="Linux"), \
                    patch.dict("os.environ", {"CHAT_AI_TRAINING_SERVER": "1"}), \
                    patch("builtins.__import__", side_effect=bounded_import):
                runpy.run_path(str(ROOT / "training/scripts/train_cpu_serial_v3.py"), run_name="__main__")

    def test_correct_retained_stage_reaches_weight_boundary(self):
        with self.assertRaises(BeforeWeights):
            self.start("contrat", "shared-v5r5-en-fr")

    def test_skipped_stage_and_wrong_retained_manifest_reject_before_weights(self):
        for stage, retained in (("reservation", "shared-v5r5-en-fr"), ("contrat", "shared-v5r4-en-fr")):
            with self.subTest(stage=stage, retained=retained), self.assertRaises(SystemExit):
                self.start(stage, retained)

    def test_partial_or_oversampled_epoch_reject_before_weights(self):
        for extra in (["--steps", "2"], ["--complete-epochs", "1", "--balanced-applications"]):
            with self.subTest(arguments=extra), self.assertRaises(SystemExit):
                self.start("contrat", "shared-v5r5-en-fr", extra)
