"""Two disposable Contracts updates for a reviewed text-checkpoint mask.

Requires an accepted, terminal R11 predecessor and its exact model artifacts.
Run full and alternate-text masks in separate sequential services. This is
capacity/mechanics evidence only; no training, accuracy or deployment acceptance.
"""
import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

SETTINGS = {"threads": 14, "max_seq_length": 8192, "learning_rate": 1e-5,
            "semantic_loss_weight": 4, "lora_layers": 24, "lora_rank": 16, "lora_alpha": 32}
FRAMEWORK_FILES = (
    "transformers/modeling_utils.py", "transformers/modeling_layers.py",
    "transformers/models/qwen3_5/modeling_qwen3_5.py", "torch/utils/checkpoint.py",
    "peft/peft_model.py", "peft/tuners/tuners_utils.py",
)
MEMORY_LIMIT = 32 * 1024 ** 3


def sha(path):
    result = hashlib.sha256()
    path = Path(path)
    before = path.stat()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Artifact changed while hashing")
    return result.hexdigest()


def save(path, value):
    with Path(path).open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def validate_basic(binding):
    if sys.platform != "linux" or os.environ.get("CHAT_AI_TRAINING_SERVER") != "1":
        raise ValueError("Diagnostic requires the approved Linux server")
    if any(os.environ.get(name) != "1" for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")):
        raise ValueError("Offline model loading is required")
    if (binding.get("version") != 1 or binding.get("stage") != "contrat"
            or binding.get("mask") not in ("full", "alternate")
            or binding.get("settings") != SETTINGS):
        raise ValueError("Unexpected diagnostic scope or settings")
    if not re.fullmatch(r"chat-ai-[a-z0-9-]+-capacity-(full|alternate)\.service", binding["unit"]):
        raise ValueError("A dedicated capacity service is required")
    if not binding["unit"].endswith("-" + binding["mask"] + ".service"):
        raise ValueError("Service name and mask differ")
    output = Path(binding["output"])
    if not output.is_absolute() or output.exists() or not output.parent.is_dir():
        raise ValueError("A new absolute output directory under an existing parent is required")
    sources = [Path(binding[name]) for name in ("base", "data", "runtime", "trainer", "exporter", "converter", "server_python")]
    sources += [Path(binding["predecessor"][name]) for name in ("evidence_root", "exports_root", "retained_data")]
    sources += [Path(__file__).resolve().parent]
    for path in sources:
        if not path.is_absolute() or not path.exists():
            raise ValueError("Missing absolute source path")
        if output.resolve().is_relative_to(path.resolve()) or path.resolve().is_relative_to(output.resolve()):
            raise ValueError("Output overlaps protected inputs")
    if Path(binding["server_python"]).resolve() != Path(sys.executable).resolve():
        raise ValueError("Diagnostic interpreter differs from the reviewed executable")
    if Path(binding["trainer"]).name != "train_cpu_serial_v4.py":
        raise ValueError("Diagnostic requires the matching serial trainer")
    if shutil.disk_usage(output.parent).free < 12 * 1024 ** 3:
        raise ValueError("Insufficient diagnostic storage")
    return output


def bootstrap(binding):
    # Check all imported repository sources before executing them.
    root = Path(__file__).resolve().parent
    required = {str(root / name) for name in
                (Path(__file__).name, "selective_checkpointing.py", "compare_selective_checkpointing.py", "replay_contracts_after_r11.py")}
    if not required <= set(binding["source_sha256"]):
        raise ValueError("Missing diagnostic source bindings")
    for path, expected in binding["source_sha256"].items():
        if sha(path) != expected:
            raise ValueError("Bound diagnostic source changed")
    import replay_contracts_after_r11 as predecessor
    if Path(predecessor.__file__).resolve() != root / "replay_contracts_after_r11.py":
        raise ValueError("Unexpected predecessor checker")
    predecessor.bootstrap(binding)
    if set(binding["framework_sha256"]) != set(FRAMEWORK_FILES):
        raise ValueError("Incomplete framework source binding")
    if set(binding["package_versions"]) != {"torch", "transformers", "peft", "safetensors"}:
        raise ValueError("Incomplete numerical package binding")
    for package, expected in binding["package_versions"].items():
        if metadata.version(package) != expected:
            raise ValueError("Numerical package version changed")
    for name, expected in binding["framework_sha256"].items():
        path = metadata.distribution(name.split("/")[0]).locate_file(name)
        if sha(path) != expected:
            raise ValueError("Framework checkpoint source changed")
    return predecessor


def check_command(raw, expected):
    prefix, suffix = "argv[]=", " ; ignore_errors="
    if (not expected or any(not isinstance(arg, str) or not arg or re.search(r"[\s;{}]", arg) for arg in expected)
            or raw.count(prefix) != 1 or raw.count(suffix) != 1
            or raw.split(prefix, 1)[1].split(suffix, 1)[0] != " ".join(expected)):
        raise ValueError("Service command differs from the reviewed operator invocation")


def service_state(binding, command):
    lines = Path("/proc/self/cgroup").read_text().splitlines()
    groups = [line.split("::", 1)[1] for line in lines if line.startswith("0::")]
    if len(groups) != 1 or Path(groups[0]).name != binding["unit"]:
        raise ValueError("Diagnostic must run in its own unified service cgroup")
    keys = ("MainPID", "ActiveState", "InvocationID", "ControlGroup",
            "CPUQuotaPerSecUSec", "MemoryMax", "MemorySwapMax", "KillMode", "ExecStart")
    state = dict(line.split("=", 1) for line in subprocess.check_output(
        ["systemctl", "show", binding["unit"], *["--property=" + key for key in keys]],
        text=True).splitlines())
    expected = {"MainPID": str(os.getpid()), "ActiveState": "active", "ControlGroup": groups[0],
                "CPUQuotaPerSecUSec": "14s", "MemoryMax": str(MEMORY_LIMIT),
                "MemorySwapMax": "0", "KillMode": "control-group"}
    if (any(state.get(key) != value for key, value in expected.items())
            or not re.fullmatch("[a-f0-9]{32}", state.get("InvocationID", ""))):
        raise ValueError("Diagnostic service identity or limits differ")
    check_command(state["ExecStart"], command)
    group = Path("/sys/fs/cgroup" + groups[0])
    events = {key: int(value) for key, value in
              (line.split() for line in (group / "memory.events").read_text().splitlines())}
    if any(events.values()):
        raise RuntimeError("Diagnostic cgroup reported memory pressure or OOM")
    return {"service": state, "memory_events": events,
            "memory_peak_bytes": int((group / "memory.peak").read_text())}


def verify_predecessor(binding, predecessor):
    from rehearse_cpu_v2 import prepare_inputs
    if sha(Path(binding["data"]) / "manifest.json") != binding["data_manifest_sha256"]:
        raise ValueError("Next-stage dataset manifest changed")
    checked, rows, _, retained = prepare_inputs(Path(binding["data"]), "contrat",
        Path(binding["predecessor"]["retained_data"]))
    source = predecessor.trainer_functions(Path(binding["trainer"]),
                                          binding["source_sha256"][binding["trainer"]])
    base = source["model_fingerprint"](Path(binding["base"]))
    if base != binding["predecessor"]["base_artifacts"]:
        raise ValueError("Actual FP32 base differs from accepted predecessor binding")
    proof = predecessor.check_predecessor(binding,
        {"stage": "contrat", "base_artifacts": base, "retained_dataset": retained})
    return source, checked, rows, retained, proof


def run(binding, *, binding_path, binding_sha256):
    output = validate_basic(binding)
    binding_path = Path(binding_path).resolve()
    binding_payload = binding_path.read_bytes()
    if hashlib.sha256(binding_payload).hexdigest() != binding_sha256 or json.loads(binding_payload) != binding:
        raise ValueError("Reviewed operator binding changed")
    command = [binding["server_python"], "-B", "-u", str(Path(__file__).resolve()),
               "--binding", str(binding_path), "--binding-sha256", binding_sha256]
    predecessor = bootstrap(binding)
    source, checked, rows, retained, proof = verify_predecessor(binding, predecessor)
    import psutil

    def admit(first=False):
        predecessor.no_other_jobs(psutil)
        state = service_state(binding, command)
        memory = psutil.virtual_memory()
        required = memory.total * .10 + (MEMORY_LIMIT if first else 0)
        if memory.available < required:
            raise RuntimeError("Insufficient memory reserve")
        return state

    initial_service = admit(first=True)
    # No weights or numerical libraries are imported before the preceding gates.
    import torch
    from torch.utils.checkpoint import checkpoint
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5DecoderLayer
    from safetensors.torch import save_file
    from text_lora import configure_text_lora
    from selective_checkpointing import TextCheckpointMask
    from rehearse_cpu_v2 import frozen_parameter_digest
    torch.set_num_threads(14)
    torch.set_num_interop_threads(1)
    torch.manual_seed(17)
    tokenizer = AutoTokenizer.from_pretrained(binding["base"], local_files_only=True, trust_remote_code=False)
    args = SimpleNamespace(**SETTINGS)
    source.update(torch=torch, tokenizer=tokenizer, a=args)
    # Encode all training examples with the actual trainer; choose by length only.
    items = [source["encode"](row) for row in rows["train"]]
    index = max(range(len(items)), key=lambda i: items[i][0].shape[1])
    item = items[index]
    del items
    admit()
    model = Qwen3_5ForConditionalGeneration.from_pretrained(binding["base"],
        local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa")
    model, regex = configure_text_lora(model, layers=24, rank=16, alpha=32, checkpointing=True)
    model.get_base_model().model.language_model.config.use_cache = False
    model.train()
    source["model"] = model
    trainable = {name: value for name, value in model.named_parameters() if value.requires_grad}
    optimizer = torch.optim.AdamW(trainable.values(), lr=SETTINGS["learning_rate"], weight_decay=0)
    expected = set(range(24))
    def layer(name):
        return int(re.search(r"language_model\.layers\.(\d+)\.", name).group(1))
    frozen = frozen_parameter_digest(model, torch)
    mask = range(24) if binding["mask"] == "full" else range(0, 24, 2)
    output.mkdir(exist_ok=False)
    with (output / "binding.json").open("xb") as handle:
        handle.write(binding_payload)
    plan = {"scope": "Disposable checkpoint diagnostic; not model accuracy or training authorization",
        "stage": "contrat", "mask": binding["mask"], "checkpoint_text_indices": list(mask),
        "settings": SETTINGS, "fixed_settings": {"seed": 17, "dtype": "bfloat16",
            "attention": "sdpa", "optimizer": "AdamW", "weight_decay": 0,
            "gradient_clip_norm": 1, "thinking": False, "use_reentrant": False},
        "base_artifacts": binding["predecessor"]["base_artifacts"], "audit": checked,
        "retained_dataset": retained, "predecessor": proof, "selected_train_row": index,
        "selected_train_row_sha256": hashlib.sha256(json.dumps(rows["train"][index],
            ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        "sequence_tokens": item[0].shape[1], "target_regex": regex,
        "trainable_parameters": sum(p.numel() for p in trainable.values()),
        "initial_service": initial_service, "optimizer_defaults": optimizer.defaults,
        "operator_invocation": {"binding_path": str(binding_path),
            "binding_sha256": binding_sha256, "command": command}}
    save(output / "plan.json", plan)
    def save_tensors(name, tensors):
        save_file({key: value.detach().cpu().contiguous().clone()
                   for key, value in tensors.items()}, str(output / name))
    save_tensors("initial.safetensors", trainable)
    metrics = []
    with TextCheckpointMask(model, mask, decoder_type=Qwen3_5DecoderLayer, checkpoint_fn=checkpoint) as observed:
        for step in (1, 2):
            admit()
            optimizer.zero_grad(set_to_none=True)
            observed.begin_step()
            start = time.monotonic()
            loss = source["loss_for"](item)
            if not torch.isfinite(loss):
                raise RuntimeError("Non-finite diagnostic loss")
            loss.backward()
            forward_backward = time.monotonic() - start
            calls = observed.end_step()
            seen, nonzero = set(), set()
            for name, parameter in trainable.items():
                if parameter.grad is None or not torch.isfinite(parameter.grad).all():
                    raise RuntimeError("Missing or non-finite gradient")
                seen.add(layer(name))
                if parameter.grad.abs().max() > 0:
                    nonzero.add(layer(name))
            if seen != expected or nonzero != expected:
                raise RuntimeError("Incomplete layer gradient coverage")
            save_tensors(f"gradients-{step}.safetensors", {n: p.grad for n, p in trainable.items()})
            before = {name: value.detach().clone() for name, value in trainable.items()}
            start = time.monotonic()
            norm = torch.nn.utils.clip_grad_norm_(list(trainable.values()), 1, error_if_nonfinite=True)
            optimizer.step()
            optimizer_seconds = time.monotonic() - start
            updated = {layer(name) for name, value in trainable.items() if not torch.equal(before[name], value.detach())}
            if updated != expected or any(not torch.isfinite(p).all() for p in trainable.values()):
                raise RuntimeError("Incomplete or non-finite layer updates")
            if any(not torch.isfinite(v).all() for state in optimizer.state.values()
                   for v in state.values() if torch.is_tensor(v)):
                raise RuntimeError("Non-finite optimizer state")
            save_tensors(f"updated-{step}.safetensors", trainable)
            state = admit()
            if state["service"] != initial_service["service"]:
                raise RuntimeError("Diagnostic service identity changed")
            metric = {"step": step, "loss": float(loss.detach()), "gradient_norm": float(norm),
                "forward_backward_seconds": forward_backward, "optimizer_seconds": optimizer_seconds,
                "timing_scope": "Measured computation only; excludes checks and tensor serialization",
                "checkpoint_calls": calls, "gradient_layers": sorted(seen),
                "nonzero_gradient_layers": sorted(nonzero), "updated_layers": sorted(updated),
                "rss_bytes": psutil.Process().memory_info().rss, "cgroup": state}
            metrics.append(metric)
            save(output / f"step-{step}.json", metric)
            print(json.dumps(metric), flush=True)
            del loss, before
    if frozen_parameter_digest(model, torch) != frozen:
        raise RuntimeError("Frozen base weights changed")
    bootstrap(binding)
    _, final_checked, _, final_retained, final_proof = verify_predecessor(binding, predecessor)
    if (final_checked, final_retained, final_proof) != (checked, retained, proof):
        raise RuntimeError("Bound inputs changed during diagnostic")
    final_service = admit()
    if final_service["service"] != initial_service["service"]:
        raise RuntimeError("Diagnostic service changed")
    peak = final_service["memory_peak_bytes"]
    margin_ok = peak * 14 <= MEMORY_LIMIT * 10
    files = {path.name: sha(path) for path in output.iterdir() if path.is_file()}
    save(output / "complete.json", {"status": "TWO UPDATES COMPLETE; PAIRED COMPARISON REQUIRED",
        "steps": 2, "mask": binding["mask"], "frozen_parameters_unchanged": True,
        "capacity_margin": 1.4, "capacity_margin_passed": margin_ok, "cgroup": final_service,
        "evidence_sha256": files, "model_accuracy_measured": False, "model_accepted": False,
        "full_training_authorized": False, "production_activation": False,
        "resume_training_from_diagnostic": False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--binding-sha256", required=True)
    args = parser.parse_args()
    if sha(args.binding) != args.binding_sha256:
        raise ValueError("Operator binding changed")
    run(json.loads(args.binding.read_text()), binding_path=args.binding, binding_sha256=args.binding_sha256)


if __name__ == "__main__":
    main()
