"""Verify completed training metadata; this never establishes model accuracy."""
import ast
from copy import deepcopy
import hashlib
import json
import math

PROVENANCE_KEYS = {
    "provenance_version", "script", "schedule_script", "lora_setup_script",
    "semantic_loss_script", "validation_selection_script", "base_artifacts",
    "python_version", "dependency_versions", "host", "platform",
    "dataset_sha256", "validation_sha256", "training_config",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(report, provenance, history, saved_selection, log, selection_source, selection_sha256):
    """Replay the trusted hash-pinned selector and couple all terminal records."""
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
            and [entry["step"] for entry in history] == [0, 64, 128],
            "Raw validation history differs")
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
    require(len(updates) == 128 and updates == report["steps_metrics"]
            and [event["step"] for event in updates] == list(range(1, 129)),
            "Printed optimizer updates differ")
    require([event["baseline_validation_loss"] for event in events
             if "baseline_validation_loss" in event] == [baseline],
            "Printed baseline validation differs")
    require([event["validation_checkpoint"] for event in events
             if "validation_checkpoint" in event] == history[1:],
            "Printed validation checkpoints differ")
    return {"verified": True, "optimizer_updates": 128,
            "validation_steps": [0, 64, 128], "loss_selected_step": selector.best_step,
            "functional_evaluation_required": True, "model_accepted": False}
