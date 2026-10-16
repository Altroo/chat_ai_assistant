"""Admission tests for the future diagnostic; no model weights or inference."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import probe_cpu_selective as probe
from training.tests.test_replay_after_r11 import fixture as predecessor_fixture
import replay_contracts_after_r11 as predecessor


def options(root):
    names = ("base", "data", "runtime", "trainer", "exporter", "converter")
    values = {}
    for name in names:
        path = root / ("train_cpu_serial_v4.py" if name == "trainer" else name)
        if name in ("trainer", "exporter", "converter"):
            path.touch()
        else:
            path.mkdir()
        values[name] = str(path)
    for name in ("evidence", "exports", "retained"):
        (root / name).mkdir()
    values["server_python"] = sys.executable
    values.update(version=1, stage="contrat", mask="full",
        settings=deepcopy(probe.SETTINGS), output=str(root / "output"),
        unit="chat-ai-test-capacity-full.service", predecessor={
            "evidence_root": str(root / "evidence"), "exports_root": str(root / "exports"),
            "retained_data": str(root / "retained")})
    return values


class DiagnosticAdmissionTests(unittest.TestCase):
    def basic(self, binding, platform="linux", server="1", offline="1"):
        with patch.object(probe.sys, "platform", platform), patch.dict(os.environ, {
            "CHAT_AI_TRAINING_SERVER": server, "HF_HUB_OFFLINE": offline, "TRANSFORMERS_OFFLINE": offline
        }), patch.object(probe.shutil, "disk_usage", return_value=SimpleNamespace(free=20*1024**3)):
            return probe.validate_basic(binding)

    def test_valid_full_and_alternate_plans(self):
        with tempfile.TemporaryDirectory() as temp:
            b = options(Path(temp))
            for mask in ("full", "alternate"):
                b["mask"] = mask
                b["unit"] = f"chat-ai-test-capacity-{mask}.service"
                self.assertEqual(self.basic(b), Path(b["output"]))

    def test_wrong_server_or_online_loading_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            b = options(Path(temp))
            for kwargs in ({"platform": "darwin"}, {"server": "0"}, {"offline": "0"}):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    self.basic(b, **kwargs)

    def test_wrong_scope_settings_unit_or_output_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            original = options(Path(temp))
            for key, value in (("stage", "shared"), ("mask", "none"),
                ("settings", {**probe.SETTINGS, "threads": 16}),
                ("unit", "chat-ai-test-training.service"),
                ("unit", "chat-ai-test-capacity-alternate.service"),
                ("output", "relative"), ("output", str(Path(temp)/"missing"/"new")),
                ("output", original["base"]), ("output", original["base"]+"/nested")):
                b = deepcopy(original); b[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.basic(b)

    def test_missing_source_binding_rejects_without_import(self):
        with self.assertRaisesRegex(ValueError, "Missing diagnostic source"):
            probe.bootstrap({"source_sha256": {}})

    def test_changed_bound_source_rejects_without_helper_execution(self):
        names = ("probe_cpu_selective.py", "selective_checkpointing.py", "compare_selective_checkpointing.py", "replay_contracts_after_r11.py")
        binding = {"source_sha256": {str(ROOT/"training/scripts"/name): "wrong" for name in names}}
        with patch.object(predecessor, "bootstrap", side_effect=AssertionError("must not execute")):
            with self.assertRaisesRegex(ValueError, "Bound diagnostic source changed"):
                probe.bootstrap(binding)

    def test_actual_predecessor_failures_reject_before_model_import(self):
        # Use real accepted-predecessor validation with synthetic proof files.
        for mutation in ("running", "failed_fresh", "different_base"):
            with tempfile.TemporaryDirectory() as temp:
                b, plan, proofs, persist, artifacts = predecessor_fixture(Path(temp))
                b["data"] = str(ROOT/"training/datasets/shared-v6r11-en-fr")
                b["data_manifest_sha256"] = probe.sha(Path(b["data"])/"manifest.json")
                b["trainer"] = str(ROOT/"training/scripts/train_cpu_serial_v4.py")
                b["source_sha256"] = {b["trainer"]: probe.sha(b["trainer"])}
                base = deepcopy(plan["base_artifacts"])
                if mutation == "running":
                    proofs["pipeline-state.json"]["phase"] = "waiting_for_training"
                elif mutation == "failed_fresh":
                    proofs["pipeline-state.json"]["fresh_passed"] = False
                else:
                    base = {"wrong": True}
                persist()
                fake_source = {"model_fingerprint": lambda _: base}
                with patch.object(predecessor, "trainer_functions", return_value=fake_source), \
                     patch.object(predecessor, "served_artifacts", return_value=artifacts):
                    with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                        probe.verify_predecessor(b, predecessor)

    def test_valid_predecessor_uses_actual_next_stage_curriculum(self):
        with tempfile.TemporaryDirectory() as temp:
            b, plan, _, _, artifacts = predecessor_fixture(Path(temp))
            b["data"] = str(ROOT/"training/datasets/shared-v6r11-en-fr")
            b["data_manifest_sha256"] = probe.sha(Path(b["data"])/"manifest.json")
            b["trainer"] = str(ROOT/"training/scripts/train_cpu_serial_v4.py")
            b["source_sha256"] = {b["trainer"]: probe.sha(b["trainer"])}
            with patch.object(predecessor, "trainer_functions",
                              return_value={"model_fingerprint": lambda _: plan["base_artifacts"]}), \
                 patch.object(predecessor, "served_artifacts", return_value=artifacts):
                _, checked, rows, retained, proof = probe.verify_predecessor(b, predecessor)
            self.assertEqual(len(rows["train"]), 2572)
            self.assertEqual(len(rows["valid"]), 319)
            self.assertEqual(checked["manifest_sha256"], b["data_manifest_sha256"])
            for key, value in plan["retained_dataset"].items():
                self.assertEqual(retained[key], value)
            self.assertEqual(proof["step"], 1200)


class ServiceAdmissionTests(unittest.TestCase):
    def state(self, *, changes=None, events="low 0\nhigh 0\nmax 0\noom 0\noom_kill 0\n",
              group="/system.slice/chat-ai-test-capacity-full.service"):
        unit = "chat-ai-test-capacity-full.service"
        values = {"MainPID": str(os.getpid()), "ActiveState": "active", "InvocationID": "a"*32,
                  "ControlGroup": group, "CPUQuotaPerSecUSec": "14s",
                  "MemoryMax": str(probe.MEMORY_LIMIT), "MemorySwapMax": "0", "KillMode": "control-group"}
        command = ["/usr/bin/python", "-B", "-u", "/test/probe.py", "--binding", "/test/binding.json", "--binding-sha256", "a"*64]
        values["ExecStart"] = "{ path=/usr/bin/python ; argv[]="+" ".join(command)+" ; ignore_errors=no ; start_time=n/a ; stop_time=n/a ; }"
        values.update(changes or {})
        def read(path, *args, **kwargs):
            if str(path) == "/proc/self/cgroup": return "0::" + group + "\n"
            if path.name == "memory.events": return events
            if path.name == "memory.peak": return str(7*1024**3)
            raise AssertionError(str(path))
        with patch.object(Path, "read_text", read), patch.object(probe.subprocess, "check_output",
            return_value="\n".join(key+"="+value for key,value in values.items())):
            return probe.service_state({"unit": unit}, command)

    def test_owned_limited_service(self):
        self.assertEqual(self.state()["memory_peak_bytes"], 7*1024**3)

    def test_wrong_identity_limits_and_memory_pressure_reject(self):
        for key, value in (("MainPID", "0"), ("MemoryMax", "max"), ("MemorySwapMax", "1"),
                           ("CPUQuotaPerSecUSec", "16s"), ("KillMode", "process"),
                           ("InvocationID", ""), ("ActiveState", "activating"), ("ExecStart", "argv[]=wrong ; ignore_errors=no")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.state(changes={key: value})
        with self.assertRaises(ValueError):
            self.state(group="/user.slice/example")
        with self.assertRaises(RuntimeError):
            self.state(events="oom_kill 1\n")


if __name__ == "__main__":
    unittest.main()
