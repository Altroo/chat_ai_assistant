"""Admission checks for the TRAIN-only 256-update argument correction.

Infrastructure bindings remain private. These checks neither launch training nor
accept, deploy, or activate a model. The frozen trainer is invoked unchanged with equal assistant-token weights.
"""
import math
from pathlib import Path

TRAIN_SHA256 = "f71f48c19a7fe3e469d800fb451aa2e624150407804fc90ff8abcec4c1596022"
VALID_SHA256 = "8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487"
EXPOSURE = {"facturation": 224, "management_projet": 16, "design_workflow": 16}
SAVED_STEPS = (64, 128, 192, 256)
VALIDATION_STEPS = (0, 128, 256)
TRAIN_TIMEOUT_SECONDS = 5 * 3600
UNIT_TIMEOUT_SECONDS = 6 * 3600
THREADS = 14


def require(condition, message):
    if not condition:
        raise ValueError(message)


def is_uniform_weight(value):
    """Reject booleans and strings that could mimic a numeric recipe value."""
    return type(value) in (int, float) and value == 1


def memory_admission(total, available, ceiling_gib):
    require(all(type(value) is int and value > 0 for value in
                (total, available, ceiling_gib)), "Positive integer memory values required")
    require(available <= total and 1 <= ceiling_gib <= 40, "Invalid memory profile")
    require(available - ceiling_gib * 1024**3 > total * .10,
            "Capacity ceiling must preserve ten percent of host RAM")


def training_command(python, root, parent, checkpointing):
    require(type(checkpointing) is bool, "Explicit checkpointing mode required")
    root = Path(root)
    command = [
        str(python), "-B", "-u", str(root / "scripts/train_cpu.py"),
        "--model", str(parent), "--data", str(root / "data"),
        "--output", str(root / "training"), "--complete-epochs", "1",
        "--threads", str(THREADS), "--max-seq-length", "8192",
        "--learning-rate", "0.000002", "--lora-layers", "24",
        "--lora-rank", "16", "--lora-alpha", "32",
        "--semantic-loss-weight", "1", "--attention", "sdpa",
        "--checkpoint-interval", "64", "--validation-interval", "128",
    ]
    if checkpointing:
        command.append("--gradient-checkpointing")
    return command


def validate_preflight(report):
    for split, count, digest in (("train.jsonl", 256, TRAIN_SHA256),
                                 ("valid.jsonl", 275, VALID_SHA256)):
        measured = report[split]
        require(measured["sha256"] == digest, "Preflight dataset changed")
        for field in ("count", "round_trip_passed", "runtime_prefix_parity_passed",
                      "loss_boundary_passed", "semantic_alignment_passed",
                      "output_budget_passed"):
            require(type(measured[field]) is int and measured[field] == count,
                    "Every preflight case must pass: " + field)
        require(is_uniform_weight(measured["semantic_loss_weight"])
                and measured["maximum_tokens"] <= 8192
                and measured["maximum_output_tokens"] == 512
                and measured["output_budget_contract"] == "conservative-target-v1"
                and 0 < measured["maximum_target_tokens"] <= measured["minimum_output_budget"],
                "Preflight context, semantic loss or serving budget changed")


def validate_capacity(report, pins, model_path, checkpointing, maximum_tokens, ceiling_gib):
    require(type(checkpointing) is bool, "Explicit checkpointing mode required")
    expected = {
        "passed": True, "model_path": str(model_path), "dataset_sha256": TRAIN_SHA256,
        "threads": THREADS, "dtype": "bfloat16", "attention": "sdpa",
        "lora_layers": 24, "lora_rank": 16, "lora_alpha": 32,
        "semantic_loss_weight": 1, "learning_rate": 0.000002,
        "gradient_checkpointing": "nonreentrant" if checkpointing else False,
        "sequence_tokens": maximum_tokens,
        "script_sha256": pins["probe_cpu_capacity.py"],
        "lora_setup_sha256": pins["text_lora.py"],
        "semantic_loss_sha256": pins["semantic_loss.py"],
    }
    require(all(report.get(key) == value and
                (type(report.get(key)) is bool if type(value) is bool else True)
                for key, value in expected.items()), "Capacity measurement uses another recipe")
    require(is_uniform_weight(report.get("semantic_loss_weight")), "Capacity token weighting changed")
    require(0 < report["peak_rss_kib"] * 1024 < ceiling_gib * 1024**3,
            "Capacity measurement exceeded its memory ceiling")
    require(len(report["steps"]) == 2, "Two complete capacity updates required")
    for index, step in enumerate(report["steps"], 1):
        require(step["step"] == index, "Noncontiguous capacity updates")
        for field in ("loss", "unweighted_loss", "gradient_norm", "seconds"):
            require(math.isfinite(step[field]) and step[field] >= 0,
                    "Non-finite capacity update")
        for field in ("gradient_layers", "nonzero_gradient_layers", "updated_layers"):
            require(step[field] == list(range(24)), "Incomplete adapter layer coverage")
        require(step["optimizer_state_entries"] > 0 and step["optimizer_state_bytes"] > 0,
                "Missing optimizer state")


def validate_training_report(report, pins, parent_artifacts, dependency_versions, checkpointing):
    require(type(checkpointing) is bool, "Explicit checkpointing mode required")
    config = report["training_config"]
    require(type(report["steps"]) is int and report["steps"] == 256
            and config["steps"] == 256 and config["complete_epochs"] == 1,
            "A complete 256-update epoch is required")
    require(report["dataset_sha256"] == TRAIN_SHA256
            and report["validation_sha256"] == VALID_SHA256, "Training data changed")
    require(report["base_artifacts"] == parent_artifacts, "Training used another FP32 parent")
    require(report["dependency_versions"] == dependency_versions, "Training environment changed")
    expected = {"threads": THREADS, "interop_threads": 1, "max_seq_length": 8192,
                "learning_rate": 0.000002, "seed": 17, "device": "cpu",
                "dtype": "bfloat16", "attention_implementation": "sdpa",
                "batch_size": 1, "gradient_accumulation_steps": 1,
                "gradient_clip_norm": 1.0, "checkpoint_interval_steps": 64,
                "validation_interval_steps": 128, "thinking": False,
                "gradient_checkpointing": "nonreentrant" if checkpointing else False,
                "semantic_loss_weight": 1}
    require(all(config.get(key) == value and
                (type(config.get(key)) is bool if type(value) is bool else True)
                for key, value in expected.items()), "Training recipe changed")
    require(is_uniform_weight(config.get("semantic_loss_weight")), "Training token weighting changed")
    require(config["lora"]["r"] == 16 and config["lora"]["alpha"] == 32
            and config["lora"]["layers"] == 24 and config["lora"]["dropout"] == 0,
            "Adapter recipe changed")
    require(config["optimizer"]["class"] == "torch.optim.AdamW"
            and config["optimizer"]["lr"] == 0.000002
            and config["optimizer"]["weight_decay"] == 0, "Optimizer recipe changed")
    require(report["application_exposure"] == {
        app: {"steps": count, "unique_examples": count} for app, count in EXPOSURE.items()
    }, "Full replay inventory was not trained exactly once")
    metrics = report["steps_metrics"]
    require(len(metrics) == 256
            and [row["step"] for row in metrics] == list(range(1, 257)),
            "Training updates are missing or repeated")
    require(all(math.isfinite(row["loss"]) and row["loss"] >= 0
                and math.isfinite(row["seconds"]) and row["seconds"] >= 0
                for row in metrics), "Non-finite update metrics")
    history = report["validation_history"]
    require([row["step"] for row in history] == list(VALIDATION_STEPS),
            "Teacher-forced validation schedule changed")
    for entry in history:
        loss = entry["loss"]
        require(set(loss["by_application"]) == set(EXPOSURE)
                and all(math.isfinite(value) and value >= 0 for value in
                        [loss["micro"], loss["macro"], *loss["by_application"].values()]),
                "Non-finite or incomplete validation loss")
    for key, filename in (
            ("script", "train_cpu.py"), ("schedule_script", "training_schedule.py"),
            ("lora_setup_script", "text_lora.py"), ("semantic_loss_script", "semantic_loss.py"),
            ("validation_selection_script", "validation_selection.py")):
        require(report[key]["sha256"] == pins[filename], "Training source changed")
    return {"training_complete": True, "functional_evaluation_required": True,
            "model_accepted": False, "production_activation": False,
            "next_application_training_started": False}
