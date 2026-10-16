"""Focused replay must preserve model identity, isolation and export checks."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import replay_facturation_rehearsal_v1 as current
from training.tests import test_replay_supervisor as inherited


def fixture(root):
    data, evidence, exports = (root / n for n in ("data", "evidence", "exports"))
    for folder in (data, evidence, exports):
        folder.mkdir()
    cats = ["category_" + str(i) for i in range(6)]
    manifest = {"applications": ["facturation"], "languages": ["en", "fr"]}
    artifacts = {"weights": "synthetic", "runtime": "synthetic", "tokenizer": "synthetic", "config": "synthetic"}
    fp32 = {"weights": "synthetic-fp32"}
    proof = {"step": 2400, "artifacts": artifacts}
    report = {"version": "shared-v5r11-en-fr-evaluation-v1", "selected_step": 2400,
              "training_updates_completed": 2419, "cases": 438, "fresh": {"cases": 48},
              "complete_identity_and_scoring_verified": True, "fresh_controls_verified": True,
              "production_activation": False, "accepted": False,
              "selected_fp32_artifacts": fp32, "evidence_sha256": {}}
    audit, captures, lineage = {"synthetic_audit": True}, {"train": [2], "valid": [1]}, {"application": "facturation"}
    plan = {"stage": "facturation", "retained_dataset": deepcopy(lineage),
            "audit": deepcopy(audit), "captures": deepcopy(captures),
            "rehearsal_categories": cats, "base_artifacts": deepcopy(fp32)}
    binding = {"base": str(exports / "step-2400/merged"), "data": str(data), "runtime": str(root / "runtime"),
               "predecessor": {"report": str(evidence / "report.json"), "exports_root": str(exports),
                               "base_artifacts": deepcopy(fp32), "before": str(evidence / "before.json"),
                               "after": str(evidence / "after.json")}}
    def persist():
        (data / "manifest.json").write_text(json.dumps(manifest))
        for when in ("before", "after"):
            raw = json.dumps(proof, indent=2).encode()
            # R11 controller saves exact pretty JSON without a trailing newline.
            (evidence / (when + ".json")).write_bytes(raw)
            report["evidence_sha256"][f"fresh-2400-{when}.json"] = hashlib.sha256(raw).hexdigest()
        (evidence / "report.json").write_text(json.dumps(report))
        binding["predecessor"]["report_sha256"] = current.file_sha(evidence / "report.json")
    persist()
    prepare = lambda *a, **kw: (audit, {}, captures, lineage)
    module = SimpleNamespace(prepare_inputs=prepare, FOCUS_CATEGORIES=tuple(cats),
                             FOCUS_MANIFEST_SHA256=current.file_sha(data / "manifest.json"))
    return binding, plan, manifest, report, proof, artifacts, module, persist


class FocusedPredecessorTests(unittest.TestCase):
    def evaluate(self, values):
        binding, plan, _, _, _, artifacts, module, _ = values
        with patch.object(current.importlib, "import_module", return_value=module), \
             patch.object(current, "served_artifacts", return_value=artifacts):
            return current.check_predecessor(binding, plan)

    def test_completed_failed_candidate_can_be_refined_without_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.evaluate(fixture(Path(folder)))
            self.assertEqual(result["step"], 2400)
            self.assertFalse(result["model_acceptance_established"])

    def test_incomplete_or_wrong_round_rejects(self):
        for key, bad in (("version", "other"), ("training_updates_completed", 2400), ("cases", 437),
                         ("fresh", {"cases": 47}), ("complete_identity_and_scoring_verified", False),
                         ("fresh_controls_verified", False), ("production_activation", True),
                         ("selected_step", 0), ("accepted", None)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                v = fixture(Path(folder)); v[3][key] = bad; v[-1]()
                with self.assertRaisesRegex(ValueError, "incomplete"):
                    self.evaluate(v)

    def test_other_app_and_changed_lineage_reject(self):
        for mutation in ("stage", "scope", "lineage"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                v = fixture(Path(folder))
                if mutation == "stage": v[1]["stage"] = "contrat"
                elif mutation == "scope": v[2]["applications"].append("contrat")
                else: v[1]["retained_dataset"] = None
                v[-1]()
                with self.assertRaises(ValueError): self.evaluate(v)

    def test_other_fp32_path_or_report_artifact_rejects(self):
        for mutation in ("path", "plan", "report", "served"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                v = fixture(Path(folder))
                if mutation == "path": v[0]["base"] = v[0]["base"].replace("2400", "1200")
                elif mutation == "plan": v[1]["base_artifacts"] = {"weights": "different"}
                elif mutation == "report": v[3]["selected_fp32_artifacts"] = {"weights": "different"}; v[-1]()
                else: v[5]["weights"] = "changed-after-proof"
                with self.assertRaises(ValueError): self.evaluate(v)

    def test_raw_proof_bytes_cannot_be_reserialized_or_replaced(self):
        for mutation in ("newline", "changed"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                v = fixture(Path(folder)); path = Path(v[0]["predecessor"]["after"])
                raw = path.read_bytes()
                path.write_bytes(raw + b"\n" if mutation == "newline" else raw.replace(b"2400", b"1200"))
                with self.assertRaisesRegex(ValueError, "serving evidence"):
                    self.evaluate(v)

    def test_changed_report_selection_or_categories_reject(self):
        for mutation in ("report", "audit", "captures", "categories"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                v = fixture(Path(folder))
                if mutation == "report": Path(v[0]["predecessor"]["report"]).write_text("{}")
                elif mutation == "audit": v[1]["audit"] = {}
                elif mutation == "captures": v[1]["captures"]["train"].append(3)
                else: v[1]["rehearsal_categories"] = []
                with self.assertRaises(ValueError): self.evaluate(v)

    def test_rehearsal_category_permutation_replays_but_duplicates_reject(self):
        with tempfile.TemporaryDirectory() as folder:
            values = fixture(Path(folder))
            values[1]["rehearsal_categories"].reverse()
            self.assertEqual(self.evaluate(values)["step"], 2400)
            values[1]["rehearsal_categories"].append(values[1]["rehearsal_categories"][0])
            with self.assertRaisesRegex(ValueError, "category coverage"):
                self.evaluate(values)

    def test_export_cleanup_and_resource_functions_are_unchanged(self):
        def functions(name):
            return {n.name: ast.dump(n, include_attributes=False)
                    for n in ast.parse((ROOT / "training/scripts" / name).read_text()).body
                    if isinstance(n, ast.FunctionDef)}
        old, new = functions("replay_shared_rehearsal_v1.py"), functions("replay_facturation_rehearsal_v1.py")
        self.assertEqual(set(old), set(new))
        self.assertEqual({n for n in old if old[n] != new[n]},
                         {"bootstrap", "check_predecessor", "completed_unit", "verify_inputs"})
        self.assertIn("rehearse_facturation_v1.py", current.HELPER_NAMES)


class FocusHarness:
    def setUp(self):
        binding = patch.object(inherited, "supervisor", current)
        binding.start()
        self.addCleanup(binding.stop)


class FocusNumericalTests(FocusHarness, inherited.NumericalTests):
    def test_running_failed_or_wrong_numerical_invocation_is_rejected(self):
        command = ["/synthetic/python", "/synthetic/rehearse_facturation_v1.py",
                   "--output", "/synthetic/rehearsal", "--data", "/synthetic/data",
                   "--model", "/synthetic/base", "--trainer", "/synthetic/train_cpu.py"]
        properties = {"SubState": "exited", "MainPID": "0", "Result": "success", "ExecMainStatus": "0",
                      "InvocationID": "a" * 32,
                      "ExecStart": "{ path=/synthetic/python ; argv[]=" + " ".join(command) + " ; ignore_errors=no ; status=0 }"}
        binding = {"rehearsal_unit": "chat-ai-synthetic-rehearsal.service",
                   "rehearsal_unit_properties": properties, "rehearsal_command": command,
                   "trainer": "/synthetic/train_cpu.py", "rehearsal": "/synthetic/rehearsal",
                   "data": "/synthetic/data", "base": "/synthetic/base"}
        for mutation in ("none", "running", "failure", "invocation", "output", "command"):
            actual, modified = deepcopy(properties), deepcopy(binding)
            if mutation == "running": actual["SubState"] = "running"
            if mutation == "failure": actual["Result"] = "exit-code"
            if mutation == "invocation": actual["InvocationID"] = "b" * 32
            if mutation == "output": modified["rehearsal"] = "/synthetic/other"
            if mutation == "command": modified["rehearsal_command"][0] = "/synthetic/other-python"
            listing = "\n".join(k + "=" + v for k, v in actual.items())
            with patch.object(current.subprocess, "check_output", return_value=listing):
                if mutation == "none": self.assertEqual(current.completed_unit(modified), properties)
                else:
                    with self.assertRaises(ValueError): current.completed_unit(modified)


class FocusIsolationTests(FocusHarness, inherited.IsolationTests): pass
class FocusFlowTests(FocusHarness, inherited.SupervisorFlowTests): pass
class FocusSourceTests(FocusHarness, inherited.SourceAdmissionTests): pass


if __name__ == "__main__":
    unittest.main()
