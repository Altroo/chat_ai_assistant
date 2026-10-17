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
import replay_facturation_replay_v1 as current
from training.tests import test_replay_supervisor as inherited


def fixture(root):
    data, evidence, exports = (root / name for name in ("data", "evidence", "exports"))
    for folder in (data, evidence, exports):
        folder.mkdir()
    base = exports / "step-600/merged"
    base.mkdir(parents=True)
    (base / "chat_ai_export.json").write_text('{"synthetic_export": true}')
    cats = ["category_" + str(i) for i in range(10)]
    manifest = {"applications": ["facturation", "management_projet", "design_workflow"], "languages": ["en", "fr"]}
    artifacts = {"weights": "synthetic", "runtime": "synthetic", "tokenizer": "synthetic", "config": "synthetic"}
    fp32 = {"weights": "synthetic-fp32"}
    proof = {"step": 600, "artifacts": artifacts}
    app_gates = {"facturation": False, "management_projet": False, "design_workflow": False}
    terminal = {"phase": "finished", "selected_step": 600, "accepted": False,
                "facturation_accepted": False, "production_activation": False,
                "next_application_training_started": False, "by_application": app_gates}
    report = {
        "version": "facturation-focus-v1-en-fr-evaluation", "selected_step": 600,
        "training_complete": True, "training_updates": 1047, "training_application": "facturation",
        "languages": ["en", "fr"], "model_family": "Qwen3.5-0.8B", "runtime": "Colibri",
        "development_cases_per_candidate": 133, "shared_development_regression_cases": 275,
        "regression_cases": 438, "additional_control_cases": 48, "regression_rerun": True,
        "production_activation": False, "next_application_training_started": False,
        "model_acceptance_passed": False, "facturation_model_acceptance_passed": False,
        "selection": {"selected_step": 600},
        "candidate_development": [{"step": step, "metrics": {"count": 133}} for step in (0, 300, 600, 900, 1047)],
        "by_application": {app: {"model_planning_acceptance_passed": value} for app, value in app_gates.items()},
        "evidence_sha256": {},
    }
    audit, captures, lineage = {"synthetic_audit": True}, {"train": [2], "valid": [1]}, {"application": "facturation"}
    plan = {"stage": "facturation", "retained_dataset": deepcopy(lineage),
            "audit": deepcopy(audit), "captures": deepcopy(captures),
            "rehearsal_categories": cats, "base_artifacts": deepcopy(fp32)}
    binding = {
        "base": str(base), "data": str(data), "runtime": str(root / "runtime"),
        "exporter": str(root / "export_adapter.py"), "converter": str(root / "convert_colibri.py"),
        "source_sha256": {str(root / "export_adapter.py"): "synthetic-exporter",
                          str(root / "convert_colibri.py"): "synthetic-converter"},
        "predecessor": {"report": str(evidence / "report.json"), "exports_root": str(exports),
            "base_artifacts": deepcopy(fp32), "terminal_state": str(evidence / "terminal.json"),
            "before": str(evidence / "before.json"), "after": str(evidence / "after.json"),
            "selected_fp32_identity": str(evidence / "fp32-identity.json")},
    }
    def persist():
        (data / "manifest.json").write_text(json.dumps(manifest))
        (evidence / "terminal.json").write_text(json.dumps(terminal))
        report["evidence_sha256"]["evaluation-state.json"] = current.file_sha(evidence / "terminal.json")
        for when in ("before", "after"):
            raw = json.dumps(proof, indent=2).encode()
            (evidence / (when + ".json")).write_bytes(raw)
            report["evidence_sha256"][f"fresh-600-{when}.json"] = hashlib.sha256(raw).hexdigest()
        (evidence / "report.json").write_text(json.dumps(report))
        binding["predecessor"]["report_sha256"] = current.file_sha(evidence / "report.json")
        manifest.setdefault("starting_model", {
            "required_predecessor_selected_step": 600,
            "required_predecessor_report_sha256": binding["predecessor"]["report_sha256"],
        })
        (data / "manifest.json").write_text(json.dumps(manifest))
        identity = {
            "version": "facturation-focus-v1-selected-fp32-binding", "selected_step": 600,
            "evaluation_report_sha256": binding["predecessor"]["report_sha256"],
            "terminal_state_sha256": current.file_sha(evidence / "terminal.json"),
            "selected_fp32_artifacts": deepcopy(fp32), "selected_serving_artifacts": deepcopy(artifacts),
            "fp32_tensor_count": 473, "weight_dtypes": ["F32"],
            "exporter_sha256": "synthetic-exporter", "converter_sha256": "synthetic-converter",
            "export_metadata_sha256": current.file_sha(base / "chat_ai_export.json"),
        }
        (evidence / "fp32-identity.json").write_text(json.dumps(identity))
        binding["predecessor"]["selected_fp32_identity_sha256"] = current.file_sha(evidence / "fp32-identity.json")
    persist()
    prepare = lambda *args, **kwargs: (audit, {}, captures, lineage)
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
            self.assertEqual(result["step"], 600)
            self.assertFalse(result["model_acceptance_established"])

    def test_wrong_starting_checkpoint_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            values = fixture(Path(folder))
            values[2]["starting_model"]["required_predecessor_selected_step"] = 300
            values[-1]()
            values[6].FOCUS_MANIFEST_SHA256 = current.file_sha(Path(values[0]["data"]) / "manifest.json")
            with self.assertRaisesRegex(ValueError, "Starting predecessor differs"):
                self.evaluate(values)

    def test_other_consistent_report_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            values = fixture(Path(folder))
            original = values[2]["starting_model"]["required_predecessor_report_sha256"]
            values[3]["synthetic_additional_metadata"] = "different internally consistent report"
            values[-1]()
            self.assertNotEqual(values[0]["predecessor"]["report_sha256"], original)
            with self.assertRaisesRegex(ValueError, "Starting predecessor differs"):
                self.evaluate(values)

    def test_incomplete_or_wrong_round_rejects(self):
        for key, bad in (
                ("version", "other"), ("training_updates", 1046), ("training_complete", False),
                ("training_application", "contrat"), ("languages", ["en"]), ("runtime", "other"),
                ("shared_development_regression_cases", 274), ("regression_cases", 437),
                ("additional_control_cases", 47), ("regression_rerun", False),
                ("production_activation", True), ("next_application_training_started", True),
                ("selected_step", 0), ("model_acceptance_passed", None)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                values = fixture(Path(folder))
                values[3][key] = bad
                values[-1]()
                with self.assertRaisesRegex(ValueError, "incomplete"):
                    self.evaluate(values)


    def test_other_app_and_changed_lineage_reject(self):
        for mutation in ("stage", "scope", "lineage"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                v = fixture(Path(folder))
                if mutation == "stage": v[1]["stage"] = "contrat"
                elif mutation == "scope": v[2]["applications"].append("contrat")
                else: v[1]["retained_dataset"] = None
                v[-1]()
                with self.assertRaises(ValueError): self.evaluate(v)

    def test_other_fp32_path_or_identity_rejects(self):
        for mutation in ("path", "plan", "identity", "served"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                values = fixture(Path(folder))
                if mutation == "path":
                    values[0]["base"] = values[0]["base"].replace("600", "300")
                elif mutation == "plan":
                    values[1]["base_artifacts"] = {"weights": "different"}
                elif mutation == "identity":
                    path = Path(values[0]["predecessor"]["selected_fp32_identity"])
                    identity = json.loads(path.read_text())
                    identity["selected_fp32_artifacts"] = {"weights": "different"}
                    path.write_text(json.dumps(identity))
                    values[0]["predecessor"]["selected_fp32_identity_sha256"] = current.file_sha(path)
                else:
                    values[5]["weights"] = "changed-after-proof"
                with self.assertRaises(ValueError):
                    self.evaluate(values)

    def test_nonterminal_or_rewritten_terminal_rejects(self):
        for mutation in ("running", "step", "overall", "app", "rewrite"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                values = fixture(Path(folder))
                path = Path(values[0]["predecessor"]["terminal_state"])
                terminal = json.loads(path.read_text())
                if mutation == "running": terminal["phase"] = "evaluating_regression"
                if mutation == "step": terminal["selected_step"] = 300
                if mutation == "overall": terminal["accepted"] = True
                if mutation == "app": terminal["by_application"]["facturation"] = True
                path.write_text(json.dumps(terminal) + ("\n" if mutation == "rewrite" else ""))
                if mutation != "rewrite":
                    values[3]["evidence_sha256"]["evaluation-state.json"] = current.file_sha(path)
                    report_path = Path(values[0]["predecessor"]["report"])
                    report_path.write_text(json.dumps(values[3]))
                    values[0]["predecessor"]["report_sha256"] = current.file_sha(report_path)
                with self.assertRaises(ValueError):
                    self.evaluate(values)

    def test_fp32_observation_requires_exact_report_and_metadata_binding(self):
        mutations = (
            ("version", "other"), ("selected_step", 300),
            ("evaluation_report_sha256", "other"), ("terminal_state_sha256", "other"),
            ("selected_serving_artifacts", {}), ("fp32_tensor_count", 472),
            ("weight_dtypes", ["BF16"]), ("exporter_sha256", "other"),
            ("converter_sha256", "other"), ("export_metadata_sha256", "other"),
        )
        for key, bad in mutations:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                values = fixture(Path(folder))
                path = Path(values[0]["predecessor"]["selected_fp32_identity"])
                identity = json.loads(path.read_text())
                identity[key] = bad
                path.write_text(json.dumps(identity))
                values[0]["predecessor"]["selected_fp32_identity_sha256"] = current.file_sha(path)
                with self.assertRaisesRegex(ValueError, "FP32 export"):
                    self.evaluate(values)

    def test_incomplete_selection_or_application_gates_reject(self):
        for mutation in ("selection", "candidate", "count", "apps"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                values = fixture(Path(folder))
                report = values[3]
                if mutation == "selection": report["selection"]["selected_step"] = 300
                if mutation == "candidate": report["candidate_development"].pop()
                if mutation == "count": report["candidate_development"][0]["metrics"]["count"] = 132
                if mutation == "apps": report["by_application"].pop("design_workflow")
                values[-1]()
                with self.assertRaises(ValueError):
                    self.evaluate(values)


    def test_remote_proof_newline_matches_controller_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            v = fixture(Path(folder))
            for when in ("before", "after"):
                path = Path(v[0]["predecessor"][when])
                path.write_bytes(path.read_bytes() + b"\n")
            self.assertEqual(self.evaluate(v)["step"], 600)

    def test_proof_content_and_noncanonical_serialization_reject(self):
        for mutation in ("extra_newline", "changed", "compact"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                v = fixture(Path(folder)); path = Path(v[0]["predecessor"]["after"])
                raw = path.read_bytes()
                if mutation == "extra_newline": path.write_bytes(raw + b"\n\n")
                elif mutation == "compact": path.write_bytes(json.dumps(json.loads(raw)).encode())
                else: path.write_bytes(raw.replace(b"600", b"300"))
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
            self.assertEqual(self.evaluate(values)["step"], 600)
            values[1]["rehearsal_categories"].append(values[1]["rehearsal_categories"][0])
            with self.assertRaisesRegex(ValueError, "category coverage"):
                self.evaluate(values)

    def test_export_cleanup_and_resource_functions_are_unchanged(self):
        def functions(name):
            return {n.name: ast.dump(n, include_attributes=False)
                    for n in ast.parse((ROOT / "training/scripts" / name).read_text()).body
                    if isinstance(n, ast.FunctionDef)}
        old, new = functions("replay_facturation_rehearsal_v1.py"), functions("replay_facturation_replay_v1.py")
        self.assertEqual(set(old), set(new))
        self.assertEqual({n for n in old if old[n] != new[n]},
                         {"bootstrap", "check_predecessor", "completed_unit", "verify_inputs"})
        self.assertIn("rehearse_facturation_replay_v1.py", current.HELPER_NAMES)


class FocusHarness:
    def setUp(self):
        binding = patch.object(inherited, "supervisor", current)
        binding.start()
        self.addCleanup(binding.stop)


class FocusNumericalTests(FocusHarness, inherited.NumericalTests):
    def test_running_failed_or_wrong_numerical_invocation_is_rejected(self):
        command = ["/synthetic/python", "/synthetic/rehearse_facturation_replay_v1.py",
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
