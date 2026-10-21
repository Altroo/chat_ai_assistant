"""Execute frozen consumer startup guards without importing any model framework."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "training/scripts"
PINS = {"probe_cpu_capacity.py":"e0a280fe0415ccf5df5cb2e9e738286c5bb1fdee74ffadfdbbe3463b03d9e46b",
        "train_cpu.py":"eb95582e72fee62e7e593cbc166712ae0755ef94c97de027041e035d5b083fd4"}
APPS = ["facturation","management_projet","design_workflow"]


def startup_code(name):
    raw = (SCRIPTS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PINS[name]:
        raise ValueError("Frozen startup consumer changed")
    tree = ast.parse(raw)
    if name == "probe_cpu_capacity.py":
        body = next(n.body for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        variable = "manifest"
    else:
        body = tree.body
        variable = "dataset_manifest"
    start = next(i for i,n in enumerate(body) if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == variable for t in n.targets))
    end = next(i for i in range(start,len(body)) if isinstance(body[i],(ast.Import,ast.ImportFrom)))
    selected = body[start:end]
    if not selected or any(isinstance(n,(ast.Import,ast.ImportFrom)) for n in selected):
        raise ValueError("Unexpected model-import boundary")
    return compile(ast.Module(body=selected,type_ignores=[]), "frozen_manifest_startup", "exec")


def validate_actual_consumers(data):
    """Read only manifest and synthetic JSONL. Never execute framework imports."""
    args = SimpleNamespace(data=Path(data), complete_epochs=1, balanced_applications=False, steps=256)
    results = {}
    for name in PINS:
        namespace = {"args":args,"a":args,"json":json,"hashlib":hashlib}
        exec(startup_code(name),namespace)
        results[name] = True
    return results


class ManifestStartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data = Path(self.temp.name)
        self.train = b"".join((json.dumps({"application":app})+"\n").encode() for app in APPS)
        self.valid = self.train
        self.manifest = {"applications":APPS[:],"languages":["en","fr"],"files":{
            "train.jsonl":hashlib.sha256(self.train).hexdigest(),
            "valid.jsonl":hashlib.sha256(self.valid).hexdigest()}}
        (self.data/"train.jsonl").write_bytes(self.train)
        (self.data/"valid.jsonl").write_bytes(self.valid)

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self):
        (self.data/"manifest.json").write_text(json.dumps(self.manifest))

    def test_complete_manifest_passes_both_actual_startup_guards(self):
        self.write_manifest()
        self.assertEqual(validate_actual_consumers(self.data),{name:True for name in PINS})

    def test_missing_applications_reproduces_original_failure_before_any_model_import(self):
        del self.manifest["applications"]
        self.write_manifest()
        for name in PINS:
            args=SimpleNamespace(data=self.data,complete_epochs=1,balanced_applications=False,steps=256)
            with self.subTest(consumer=name), self.assertRaises((KeyError,SystemExit)):
                exec(startup_code(name),{"args":args,"a":args,"json":json,"hashlib":hashlib})

    def test_wrong_language_and_scope_rejected_by_both_consumers(self):
        for field,value in (("languages",["en","ar"]),("applications",["other_app"])):
            original=deepcopy(self.manifest)
            self.manifest[field]=value;self.write_manifest()
            for name in PINS:
                args=SimpleNamespace(data=self.data,complete_epochs=1,balanced_applications=False,steps=256)
                with self.subTest(field=field,consumer=name), self.assertRaises(SystemExit):
                    exec(startup_code(name),{"args":args,"a":args,"json":json,"hashlib":hashlib})
            self.manifest=original

    def test_mismatched_application_coverage_in_either_split_rejected_by_actual_trainer(self):
        for split in ("train.jsonl", "valid.jsonl"):
            with self.subTest(split=split):
                (self.data/"train.jsonl").write_bytes(self.train)
                (self.data/"valid.jsonl").write_bytes(self.valid)
                payload=json.dumps({"application":"facturation"}).encode()+bytes([10])
                (self.data/split).write_bytes(payload)
                self.manifest["files"]={name:hashlib.sha256((self.data/name).read_bytes()).hexdigest()
                                        for name in ("train.jsonl","valid.jsonl")}
                self.write_manifest()
                args=SimpleNamespace(data=self.data,complete_epochs=1,balanced_applications=False,steps=256)
                with self.assertRaisesRegex(SystemExit,"metadata"):
                    exec(startup_code("train_cpu.py"),{"a":args,"json":json,"hashlib":hashlib})

    def test_wrong_train_or_validation_hash_fails_before_model_import(self):
        self.write_manifest()
        (self.data/"train.jsonl").write_bytes(self.train+b"\n")
        with self.assertRaises(SystemExit):validate_actual_consumers(self.data)
        (self.data/"train.jsonl").write_bytes(self.train)
        (self.data/"valid.jsonl").write_bytes(self.valid+b"\n")
        with self.assertRaises(SystemExit):validate_actual_consumers(self.data)


if __name__=="__main__":
    unittest.main()
