"""Compare two completed server checkpoint diagnostics without accepting a model."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

# Bootstrap is standard-library only. Do not execute an unverified helper.
MEMORY_LIMIT = 32 * 1024 ** 3
SETTINGS = {"threads": 14, "max_seq_length": 8192, "learning_rate": 1e-5,
            "semantic_loss_weight": 4, "lora_layers": 24, "lora_rank": 16, "lora_alpha": 32}


def sha(path):
    result = hashlib.sha256()
    path = Path(path); before = path.stat()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b""):
            result.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Artifact changed while hashing")
    return result.hexdigest()


def save(path, value):
    with Path(path).open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def verified_probe(binding):
    root = Path(__file__).resolve().parent
    required = {str(root / name) for name in (Path(__file__).name, "probe_cpu_selective.py")}
    if not required <= set(binding["source_sha256"]):
        raise ValueError("Missing comparator source bindings")
    for name, expected in binding["source_sha256"].items():
        if sha(name) != expected:
            raise ValueError("Reviewed comparator source changed")
    import probe_cpu_selective as probe
    if Path(probe.__file__).resolve() != root / "probe_cpu_selective.py":
        raise ValueError("Unexpected probe helper location")
    return probe

TENSOR_FILES = ("initial.safetensors", "gradients-1.safetensors", "updated-1.safetensors",
                "gradients-2.safetensors", "updated-2.safetensors")
EVIDENCE_FILES = {"binding.json", "plan.json", "step-1.json", "step-2.json", *TENSOR_FILES}
COMMON_PLAN_KEYS = ("stage", "settings", "fixed_settings", "base_artifacts", "audit",
    "retained_dataset", "predecessor", "selected_train_row", "selected_train_row_sha256",
    "sequence_tokens", "target_regex", "trainable_parameters", "optimizer_defaults")


def read(path):
    return json.loads(Path(path).read_text())


def inspect_run(root, mask, *, binding_sha256, complete_sha256):
    root = Path(root).resolve()
    complete_bytes = (root / "complete.json").read_bytes()
    complete = json.loads(complete_bytes)
    complete_sha = hashlib.sha256(complete_bytes).hexdigest()
    if complete_sha != complete_sha256 or sha(root / "binding.json") != binding_sha256:
        raise ValueError("Diagnostic differs from independently pinned operator evidence")
    if (complete.get("status") != "TWO UPDATES COMPLETE; PAIRED COMPARISON REQUIRED"
            or complete.get("steps") != 2 or complete.get("mask") != mask
            or complete.get("frozen_parameters_unchanged") is not True
            or complete.get("capacity_margin") != 1.4
            or any(complete.get(key) is not False for key in (
                "model_accuracy_measured", "model_accepted", "full_training_authorized",
                "production_activation", "resume_training_from_diagnostic"))):
        raise ValueError("Incomplete or unexpected diagnostic completion")
    files = complete["evidence_sha256"]
    if set(files) != EVIDENCE_FILES or any(sha(root / name) != value for name, value in files.items()):
        raise ValueError("Diagnostic evidence changed or is incomplete")
    binding, plan = read(root / "binding.json"), read(root / "plan.json")
    if (binding["mask"] != mask or plan["mask"] != mask
            or Path(binding["output"]).resolve() != root
            or plan["settings"] != SETTINGS or binding["settings"] != SETTINGS
            or plan["stage"] != "contrat" or binding["stage"] != "contrat"
            or plan["base_artifacts"] != binding["predecessor"]["base_artifacts"]
            or plan["audit"]["manifest_sha256"] != binding["data_manifest_sha256"]):
        raise ValueError("Diagnostic plan and binding differ")
    indices = list(range(24)) if mask == "full" else list(range(0, 24, 2))
    if plan["checkpoint_text_indices"] != indices:
        raise ValueError("Wrong checkpoint mask")
    invocation = plan["operator_invocation"]
    command = [binding["server_python"], "-B", "-u",
        str(Path(__file__).resolve().with_name("probe_cpu_selective.py")), "--binding",
        invocation["binding_path"], "--binding-sha256", binding_sha256]
    if (invocation["binding_sha256"] != binding_sha256 or invocation["command"] != command
            or not Path(invocation["binding_path"]).is_absolute()):
        raise ValueError("Diagnostic invocation differs from reviewed binding")
    initial = plan["initial_service"]["service"]
    for state in (plan["initial_service"], complete["cgroup"]):
        if state["service"] != initial or any(state["memory_events"].values()):
            raise ValueError("Service identity changed or memory pressure occurred")
    peak = complete["cgroup"]["memory_peak_bytes"]
    if type(peak) is not int or peak <= 0 or complete["capacity_margin_passed"] is not (peak*14 <= MEMORY_LIMIT*10):
        raise ValueError("Invalid capacity margin")
    metrics = []
    for step in (1, 2):
        item = read(root / f"step-{step}.json")
        if (item["step"] != step or any(item[key] != list(range(24)) for key in (
            "gradient_layers", "nonzero_gradient_layers", "updated_layers"))
                or item["cgroup"]["service"] != initial
                or any(item["cgroup"]["memory_events"].values())):
            raise ValueError("Incomplete layer updates or changed service")
        for key in ("loss", "gradient_norm", "forward_backward_seconds", "optimizer_seconds"):
            if type(item[key]) not in (int, float) or not math.isfinite(item[key]) or item[key] < 0:
                raise ValueError("Invalid diagnostic metric")
        calls = item["checkpoint_calls"]
        if len(calls) != 24:
            raise ValueError("Incomplete checkpoint-call evidence")
        for index, call in enumerate(calls):
            enabled = index in indices
            if (call["index"] != index or call["checkpointing"] is not enabled
                    or call["checkpoint_calls"] != int(enabled)
                    or call["block_type"] not in ("linear_attention", "full_attention")):
                raise ValueError("Actual checkpoint calls differ from the mask")
        metrics.append(item)
    return {"root": root, "binding": binding, "plan": plan, "complete": complete, "metrics": metrics, "complete_sha256": complete_sha}


def verify_pair(full, alternate):
    if full["root"] == alternate["root"]:
        raise ValueError("Comparison needs two separate diagnostic runs")
    for key in COMMON_PLAN_KEYS:
        if full["plan"][key] != alternate["plan"][key]:
            raise ValueError("Paired diagnostic inputs differ: " + key)
    for key in ("base", "data", "runtime", "trainer", "source_sha256",
                "framework_sha256", "package_versions", "predecessor", "data_manifest_sha256"):
        if full["binding"][key] != alternate["binding"][key]:
            raise ValueError("Paired source or artifact bindings differ: " + key)
    full_calls = full["metrics"][0]["checkpoint_calls"]
    for item in (*full["metrics"], *alternate["metrics"]):
        if [c["block_type"] for c in item["checkpoint_calls"]] != [c["block_type"] for c in full_calls]:
            raise ValueError("Decoder block types differ across paired steps")


def stopped_service(run):
    initial = run["plan"]["initial_service"]["service"]
    keys = ("MainPID", "ActiveState", "SubState", "Result", "ExecMainStatus", "InvocationID",
            "CPUQuotaPerSecUSec", "MemoryMax", "MemorySwapMax", "KillMode", "ExecStart")
    state = dict(line.split("=", 1) for line in subprocess.check_output(
        ["systemctl", "show", run["binding"]["unit"], *["--property=" + key for key in keys]],
        text=True).splitlines())
    if (state["MainPID"] != "0" or state["ActiveState"] not in ("active", "inactive")
            or state["SubState"] not in ("exited", "dead") or state["Result"] != "success"
            or state["ExecMainStatus"] != "0" or any(state[key] != initial[key] for key in (
                "InvocationID", "CPUQuotaPerSecUSec", "MemoryMax", "MemorySwapMax", "KillMode"))):
        raise ValueError("Diagnostic invocation has not stopped successfully")
    raw = state["ExecStart"]; prefix, suffix = "argv[]=", " ; ignore_errors="
    if (raw.count(prefix) != 1 or raw.count(suffix) != 1
            or raw.split(prefix, 1)[1].split(suffix, 1)[0] != " ".join(run["plan"]["operator_invocation"]["command"])):
        raise ValueError("Stopped service command differs from reviewed invocation")
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", type=Path, required=True)
    parser.add_argument("--alternate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    for mode in ("full", "alternate"):
        parser.add_argument("--" + mode + "-binding-sha256", required=True)
        parser.add_argument("--" + mode + "-complete-sha256", required=True)
    args = parser.parse_args()
    if sys.platform != "linux" or os.environ.get("CHAT_AI_TRAINING_SERVER") != "1":
        raise ValueError("Tensor comparison is restricted to the approved Linux server")
    if args.output.exists() or not args.output.parent.is_dir():
        raise ValueError("A new comparison output is required")
    full = inspect_run(args.full, "full", binding_sha256=args.full_binding_sha256,
                       complete_sha256=args.full_complete_sha256)
    alternate = inspect_run(args.alternate, "alternate", binding_sha256=args.alternate_binding_sha256,
                            complete_sha256=args.alternate_complete_sha256)
    verify_pair(full, alternate)
    probe = verified_probe(full["binding"])
    predecessor = probe.bootstrap(full["binding"])
    if str(Path(__file__).resolve()) not in full["binding"]["source_sha256"]:
        raise ValueError("Comparator must be included in the reviewed source binding")
    import psutil
    predecessor.no_other_jobs(psutil)
    stopped = [stopped_service(run) for run in (full, alternate)]
    memory = psutil.virtual_memory()
    if memory.available < memory.total*.10 + 2*1024**3:
        raise RuntimeError("Insufficient comparison memory reserve")
    import torch
    from safetensors import safe_open
    torch.set_num_threads(2)
    results = {}
    for name in TENSOR_FILES:
        mismatches = []
        with safe_open(full["root"]/name, framework="pt", device="cpu") as left, \
             safe_open(alternate["root"]/name, framework="pt", device="cpu") as right:
            names = sorted(left.keys())
            if not names or names != sorted(right.keys()):
                raise ValueError("Paired tensor names differ")
            for key in names:
                a, b = left.get_tensor(key), right.get_tensor(key)
                if a.shape != b.shape or a.dtype != b.dtype:
                    raise ValueError("Paired tensor shape or dtype differs")
                if not torch.isfinite(a).all() or not torch.isfinite(b).all():
                    raise ValueError("Non-finite paired tensor")
                if not torch.equal(a, b):
                    mismatches.append({"tensor": key, "max_absolute_difference": float((a.float()-b.float()).abs().max())})
        results[name] = {"tensors": len(names), "exactly_equal": not mismatches,
                         "mismatched_tensors": mismatches}
    # Initial-state equality is mandatory even when reporting a numerical failure.
    if not results["initial.safetensors"]["exactly_equal"]:
        raise ValueError("Diagnostic runs started with different adapters")
    for run, mask in ((full, "full"), (alternate, "alternate")):
        if inspect_run(run["root"], mask, binding_sha256=run["plan"]["operator_invocation"]["binding_sha256"],
                       complete_sha256=run["complete_sha256"])["complete_sha256"] != run["complete_sha256"]:
            raise ValueError("Completion evidence changed during tensor comparison")
    probe.bootstrap(full["binding"])
    if stopped != [stopped_service(run) for run in (full, alternate)]:
        raise ValueError("Diagnostic invocation identity changed")
    predecessor.no_other_jobs(psutil)
    seconds = {run["binding"]["mask"]: sum(
        item["forward_backward_seconds"] + item["optimizer_seconds"] for item in run["metrics"])
        for run in (full, alternate)}
    equal = all(value["exactly_equal"] for value in results.values())
    capacity = all(run["complete"]["capacity_margin_passed"] for run in (full, alternate))
    save(args.output, {"scope": "Paired two-step mechanics/capacity diagnostic, not model accuracy",
        "exact_gradients_and_updates_equal": equal, "capacity_margin_passed": capacity,
        "diagnostic_passed": equal and capacity, "tensors": results,
        "equality_rule": "torch.equal with matching dtype/shape and finite values; signed zeros compare equal",
        "two_step_compute_seconds": seconds,
        "timing_scope": "Same longest training row twice; excludes serialization and checks; not a full-run ETA",
        "complete_sha256": {run["binding"]["mask"]: run["complete_sha256"] for run in (full, alternate)},
        "stopped_invocations": stopped, "model_accepted": False,
        "full_training_authorized": False, "production_activation": False})


if __name__ == "__main__":
    main()
