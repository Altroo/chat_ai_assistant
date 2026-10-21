"""Verify completed training metadata; this never establishes model accuracy."""
import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

import facturation_factor_coverage_training_v1 as recipe

PROVENANCE_KEYS = {
    "provenance_version", "script", "schedule_script", "lora_setup_script",
    "semantic_loss_script", "validation_selection_script", "base_artifacts",
    "python_version", "dependency_versions", "host", "platform",
    "dataset_sha256", "validation_sha256", "training_config",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def uniform_validation(loss):
    require(set(loss) == {"micro", "macro", "by_application", "unweighted"}
            and set(loss["unweighted"]) == {"micro", "macro", "by_application"},
            "Unexpected validation summary fields")
    plain = loss["unweighted"]
    require(set(loss["by_application"]) == set(plain["by_application"]),
            "Weighted/unweighted application inventory differs")
    pairs = [(loss[key], plain[key]) for key in ("micro", "macro")]
    pairs += [(value, plain["by_application"][app])
              for app, value in loss["by_application"].items()]
    for weighted, unweighted in pairs:
        require(all(type(value) in (int, float) and math.isfinite(value) and value >= 0
                    for value in (weighted, unweighted))
                and math.isclose(weighted, unweighted, rel_tol=1e-7, abs_tol=1e-9),
                "Uniform weighted/unweighted validation losses differ")


def verify(report, provenance, history, saved_selection, log, selection_source,
           selection_sha256, *, pins, parent_artifacts, dependency_versions,
           model_path, data_path, output_path):
    """Replay the trusted hash-pinned selector and couple all terminal records."""
    recipe.validate_training_report(report, pins, parent_artifacts, dependency_versions, True)
    config = report["training_config"]
    require(report["model_path"] == str(model_path)
            and config["model_path"] == str(model_path)
            and config["data_path"] == str(data_path)
            and config["output_path"] == str(output_path),
            "Reported training paths differ from the trusted binding")

    require(selection_sha256 == pins["validation_selection.py"]
            == report["validation_selection_script"]["sha256"],
            "Validation selector digest differs from the pinned source")
    require(hashlib.sha256(selection_source).hexdigest() == selection_sha256,
            "Validation selector source changed")
    tree = ast.parse(selection_source)
    nodes = [node for node in tree.body
             if isinstance(node, ast.ClassDef) and node.name == "ValidationSelection"]
    require(len(nodes) == 1, "Expected one pinned validation selector")
    scope = {"deepcopy": deepcopy, "math": math}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "pinned_validation_selection", "exec"), scope)
    require(set(provenance) == PROVENANCE_KEYS and provenance["provenance_version"] == 1,
            "Incomplete run provenance")
    require(all(report.get(key) == value for key, value in provenance.items()),
            "Report/provenance mismatch")
    require(report["validation_selection_script"]["sha256"] == selection_sha256,
            "Reported validation source changed")
    require(history == report["validation_history"]
            and [entry["step"] for entry in history] == list(recipe.VALIDATION_STEPS),
            "Raw validation history differs")
    for entry in history:
        uniform_validation(entry["loss"])
    selector = scope["ValidationSelection"](history[0]["loss"], report["application_exposure"])
    adapter = None
    for entry in history:
        selector._score(entry["loss"])
        selector._score(entry["loss"]["unweighted"])
    for entry in history[1:]:
        improved = selector.observe(entry["step"], entry["loss"])
        require(entry["improved"] is improved and entry["selected_step"] == selector.best_step,
                "Recorded validation choice differs")
        if improved:
            adapter = "selected-" + str(entry["step"])
    metric = "validation application-macro semantic loss"
    require(report["checkpoint_selection"] == {
        "metric": metric, "step": selector.best_step, "adapter": adapter, "validation": selector.best},
        "Report checkpoint selection differs")
    require(saved_selection == {
        "metric": metric, "selected_step": selector.best_step, "selected_adapter": adapter,
        "validation": selector.best,
        "policy": "Baseline remains selected unless validation improves. This is not model acceptance."},
        "Saved checkpoint selection differs")
    baseline, final = history[0]["loss"], history[-1]["loss"]
    for prefix, loss in (("baseline", baseline), ("final", final)):
        require(report[prefix + "_validation_by_application"] == loss
                and report[prefix + "_validation_loss"] == loss["micro"]
                and report[prefix + "_validation_unweighted_loss"] == loss["unweighted"]["micro"],
                "Reported validation summary differs")
    events = []
    for line in log.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    updates = [event for event in events if set(event) == {"step", "loss", "seconds", "rss_bytes"}]
    require(len(updates) == 176 and updates == report["steps_metrics"]
            and [event["step"] for event in updates] == list(range(1, 177)),
            "Printed optimizer updates differ")
    require([event["baseline_validation_loss"] for event in events
             if "baseline_validation_loss" in event] == [baseline],
            "Printed baseline validation differs")
    require([event["validation_checkpoint"] for event in events
             if "validation_checkpoint" in event] == history[1:],
            "Printed validation checkpoints differ")
    recognized = [event for event in events if (
        "baseline_validation_loss" in event or "validation_checkpoint" in event
        or "step" in event)]
    expected_events = [{"baseline_validation_loss": baseline}]
    checkpoints = {entry["step"]: entry for entry in history[1:]}
    for update in report["steps_metrics"]:
        expected_events.append(update)
        if update["step"] in checkpoints:
            expected_events.append({"validation_checkpoint": checkpoints[update["step"]]})
    require(recognized == expected_events,
            "Printed baseline, updates and validation events are out of order")
    return {"verified": True, "optimizer_updates": 176,
            "validation_steps": list(recipe.VALIDATION_STEPS), "loss_selected_step": selector.best_step,
            "functional_evaluation_required": True, "model_accepted": False,
            "binding_paths_verified": True, "uniform_weighted_unweighted_consistent": True,
            "production_activation": False}
