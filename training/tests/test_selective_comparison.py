"""Synthetic paired-diagnostic evidence tests; never tensor or model workloads."""
import builtins
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import compare_selective_checkpointing as compare

PINNED = {}

def inspect(root, mask):
    return compare.inspect_run(root, mask, **PINNED[str(Path(root).resolve())])


def fixture(root, mask):
    root.mkdir()
    service = {"MainPID": str(os.getpid()), "ActiveState": "active",
        "InvocationID": ("a" if mask == "full" else "b")*32,
        "ControlGroup": "/system.slice/chat-ai-test-capacity-"+mask+".service",
        "CPUQuotaPerSecUSec": "14s", "MemoryMax": str(compare.MEMORY_LIMIT),
        "MemorySwapMax": "0", "KillMode": "control-group"}
    state = {"service": service, "memory_events": {"low":0,"high":0,"max":0,"oom":0,"oom_kill":0},
             "memory_peak_bytes": 7*1024**3}
    binding = {"stage":"contrat", "mask":mask, "output":str(root), "settings":compare.SETTINGS,
        "predecessor":{"base_artifacts":{"weights":"synthetic"}},
        "data_manifest_sha256":"dataset", "server_python":"/usr/bin/python3", "unit":"chat-ai-test-capacity-"+mask+".service"}
    for key in ("base","data","runtime","trainer","source_sha256","framework_sha256","package_versions"):
        binding[key] = {"synthetic":True} if key.endswith("sha256") or key=="package_versions" else "synthetic"
    plan = {key:{"synthetic":True} for key in compare.COMMON_PLAN_KEYS}
    indices = list(range(24)) if mask=="full" else list(range(0,24,2))
    plan.update(stage="contrat",mask=mask,settings=compare.SETTINGS,
        base_artifacts=binding["predecessor"]["base_artifacts"],audit={"manifest_sha256":"dataset"},
        checkpoint_text_indices=indices,initial_service=state)
    documents = {"binding.json":binding,"plan.json":plan}
    for step in (1,2):
        documents[f"step-{step}.json"]={"step":step,"loss":0.1,"gradient_norm":0.2,
            "forward_backward_seconds":1.0,"optimizer_seconds":0.1,
            "gradient_layers":list(range(24)),"nonzero_gradient_layers":list(range(24)),
            "updated_layers":list(range(24)),"cgroup":state,
            "checkpoint_calls":[{"index":i,"block_type":"full_attention" if i%4==3 else "linear_attention",
                "checkpointing":i in indices,"checkpoint_calls":int(i in indices)} for i in range(24)]}
    complete={"status":"TWO UPDATES COMPLETE; PAIRED COMPARISON REQUIRED","steps":2,"mask":mask,
        "frozen_parameters_unchanged":True,"capacity_margin":1.4,"capacity_margin_passed":True,
        "cgroup":state,"model_accuracy_measured":False,"model_accepted":False,
        "full_training_authorized":False,"production_activation":False,"resume_training_from_diagnostic":False}
    for name in compare.TENSOR_FILES:
        (root/name).write_bytes(b"synthetic metadata fixture, not a tensor")
    def persist(repin=True):
        (root/"binding.json").write_text(json.dumps(binding))
        binding_sha=compare.sha(root/"binding.json")
        command=[binding["server_python"],"-B","-u",str(Path(compare.__file__).with_name("probe_cpu_selective.py")),
                 "--binding",str(root.parent/(mask+"-operator.json")),"--binding-sha256",binding_sha]
        plan["operator_invocation"]={"binding_path":command[5],"binding_sha256":binding_sha,"command":command}
        service["ExecStart"]="{ path=/usr/bin/python3 ; argv[]="+" ".join(command)+" ; ignore_errors=no ; start_time=n/a ; stop_time=n/a ; }"
        for name,value in documents.items():
            (root/name).write_text(json.dumps(value))
        complete["evidence_sha256"]={name:compare.sha(root/name) for name in compare.EVIDENCE_FILES}
        (root/"complete.json").write_text(json.dumps(complete))
        if repin:
            PINNED[str(root.resolve())]={"binding_sha256":binding_sha,"complete_sha256":compare.sha(root/"complete.json")}
    persist()
    return documents,complete,persist


class PairEvidenceTests(unittest.TestCase):
    def test_valid_pair_and_capacity_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for mask in ("full","alternate"): fixture(root/mask,mask)
            full=inspect(root/"full","full")
            alternate=inspect(root/"alternate","alternate")
            compare.verify_pair(full,alternate)
            self.assertTrue(full["complete"]["capacity_margin_passed"])

    def test_missing_or_modified_artifacts_reject(self):
        for mutation in ("missing","modified","missing_hash"):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                root=Path(temp)/"full"; _,complete,_=fixture(root,"full")
                if mutation=="missing": (root/"gradients-1.safetensors").unlink()
                elif mutation=="modified": (root/"step-1.json").write_text("{}")
                else:
                    complete["evidence_sha256"].pop("gradients-1.safetensors")
                    (root/"complete.json").write_text(json.dumps(complete))
                with self.assertRaises((ValueError,FileNotFoundError)):
                    inspect(root,"full")

    def test_missing_updates_incorrect_calls_and_nonfinite_metrics_reject(self):
        for mutation in ("layers","missing_calls","wrong_calls","disabled_call","nan","state"):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                root=Path(temp)/"alternate"; docs,_,persist=fixture(root,"alternate")
                item=docs["step-2.json"]
                if mutation=="layers": item["updated_layers"].pop()
                elif mutation=="missing_calls": item["checkpoint_calls"].pop()
                elif mutation=="wrong_calls": item["checkpoint_calls"][0]["checkpoint_calls"]=0
                elif mutation=="disabled_call": item["checkpoint_calls"][1]["checkpoint_calls"]=1
                elif mutation=="nan": item["loss"]=float("nan")
                else:
                    item["cgroup"]=deepcopy(item["cgroup"])
                    item["cgroup"]["service"]["InvocationID"]="c"*32
                persist()
                with self.assertRaises(ValueError): inspect(root,"alternate")

    def test_false_capacity_success_and_unfrozen_weights_reject(self):
        for mutation in ("capacity","frozen","pressure"):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                root=Path(temp)/"full"; _,complete,persist=fixture(root,"full")
                if mutation=="capacity": complete["cgroup"]["memory_peak_bytes"]=30*1024**3
                elif mutation=="frozen": complete["frozen_parameters_unchanged"]=False
                else: complete["cgroup"]["memory_events"]["oom"]=1
                persist()
                with self.assertRaises(ValueError): inspect(root,"full")

    def test_rehashed_replacement_cannot_change_independent_pins(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"full"; docs,_,persist=fixture(root,"full")
            docs["step-1.json"]["loss"]=0.123
            persist(repin=False)
            with self.assertRaisesRegex(ValueError,"independently pinned"):
                inspect(root,"full")

    def test_changed_helper_rejects_before_import(self):
        root=Path(compare.__file__).resolve().parent
        binding={"source_sha256":{str(root/"compare_selective_checkpointing.py"):"wrong",
                                   str(root/"probe_cpu_selective.py"):"wrong"}}
        original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name=="probe_cpu_selective": raise AssertionError("Unverified helper import")
            return original(name,*args,**kwargs)
        with patch("builtins.__import__",side_effect=guarded):
            with self.assertRaisesRegex(ValueError,"Reviewed comparator source"):
                compare.verified_probe(binding)

    def test_paired_inputs_and_layer_types_must_match(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for mask in ("full","alternate"): fixture(root/mask,mask)
            full=inspect(root/"full","full")
            original=inspect(root/"alternate","alternate")
            for area,key in (("plan","selected_train_row_sha256"),("plan","fixed_settings"),
                             ("binding","source_sha256"),("binding","package_versions")):
                alternate=deepcopy(original); alternate[area][key]="changed"
                with self.subTest(area=area,key=key),self.assertRaises(ValueError):
                    compare.verify_pair(full,alternate)
            alternate=deepcopy(original)
            alternate["metrics"][1]["checkpoint_calls"][0]["block_type"]="full_attention"
            with self.assertRaises(ValueError): compare.verify_pair(full,alternate)

    def test_still_running_failed_or_different_invocation_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"full"; fixture(root,"full")
            run=inspect(root,"full")
            initial=run["plan"]["initial_service"]["service"]
            values={key:initial[key] for key in ("InvocationID","CPUQuotaPerSecUSec",
                    "MemoryMax","MemorySwapMax","KillMode","ExecStart")}
            values.update(MainPID="0",ActiveState="inactive",SubState="dead",Result="success",ExecMainStatus="0")
            def check(state):
                with patch.object(compare.subprocess,"check_output",
                    return_value="\n".join(k+"="+v for k,v in state.items())):
                    return compare.stopped_service(run)
            self.assertEqual(check(values),values)
            for key,value in (("MainPID","123"),("Result","oom-kill"),("ExecMainStatus","9"),
                              ("InvocationID","c"*32),("SubState","running"),("ExecStart","argv[]=wrong ; ignore_errors=no")):
                with self.subTest(key=key),self.assertRaises(ValueError):
                    check({**values,key:value})


if __name__=="__main__": unittest.main()
