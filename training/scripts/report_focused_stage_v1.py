"""Report a focused app separately from global model gates.

Read-only status analysis of one completed comparison. Uses its recorded gate
results without rescoring, reranking, changing thresholds or authorizing work.
"""
import argparse
import hashlib
import json
from pathlib import Path

APPLICATIONS = (
    "facturation", "management_projet", "contrat", "reservation",
    "design_workflow", "gestion_magasin",
)
INPUTS = (
    "comparison-binding.json", "selection.json", "state.json",
    "model-gates.json", "development.json",
)


def boolean_map(value, name):
    if (not isinstance(value, dict) or
            any(key not in APPLICATIONS or type(flag) is not bool
                for key, flag in value.items())):
        raise ValueError("Invalid " + name)
    return dict(value)


def status(binding, selection, state, gates, development, application):
    """Separate recorded scopes; this is not a new numerical admission policy."""
    if application not in APPLICATIONS:
        raise ValueError("Unknown application")
    if binding.get("policy", {}).get("application") != application:
        raise ValueError("Focused application differs from bound policy")
    if state.get("phase") != "finished":
        raise ValueError("Comparison has not finished")
    if state.get("production_activation") is not False or gates.get("production_activation") is not False:
        raise ValueError("Expected a comparison without production activation")
    step = gates.get("selected_step")
    if (type(step) is not int or step <= 0 or
            selection.get("selected_step") != step or development.get("selected_step") != step):
        raise ValueError("Comparison checkpoint mismatch")
    per_app = boolean_map(gates.get("by_application"), "application gate results")
    if application not in per_app:
        raise ValueError("Focused application was not evaluated")
    if boolean_map(state.get("by_application"), "terminal gate results") != per_app:
        raise ValueError("Terminal and recorded application gates differ")
    if type(state.get("accepted")) is not bool or state["accepted"] != all(per_app.values()):
        raise ValueError("Global comparison gate differs")
    retained = boolean_map(gates.get("retained_no_decline"), "retained development results")
    if (set(retained) != set(per_app) - {application} or
            boolean_map(development.get("retained_no_decline"), "development retention") != retained):
        raise ValueError("Retained development scope differs")
    legacy_key = application + "_accepted"
    legacy = state.get(legacy_key)
    if legacy is not None and type(legacy) is not bool:
        raise ValueError("Invalid legacy focused flag")
    focused = per_app[application]
    return {
        "version": "focused-stage-status-v1",
        "application": application,
        "selected_step": step,
        "focused_application_recorded_gate_passed": focused,
        "recorded_application_gates": per_app,
        "all_evaluated_application_gates_passed": all(per_app.values()),
        "retained_development_application_results": retained,
        "retained_development_not_regressed": all(retained.values()) if retained else None,
        "retention_scope": "Recorded development comparisons only.",
        "applications_not_evaluated": [app for app in APPLICATIONS if app not in per_app],
        "all_six_recorded_model_gates_passed": (
            set(per_app) == set(APPLICATIONS) and all(per_app.values())),
        "legacy_focused_acceptance_flag": legacy,
        "legacy_focused_flag_differs": legacy is not None and legacy != focused,
        "native_backend_security_verified": None,
        "all_six_apps_accepted": False,
        "next_application_training_authorized": False,
        "production_activation": False,
        "limitations": [
            "Recorded gates are copied from the completed comparison, not rescored.",
            "A focused model result is separate from retention and global acceptance.",
            "Development retention does not prove full-regression or critical-case nonregression.",
            "Planner critical-case failures do not establish backend authorization bypasses.",
            "Native security, operational admission and final six-app verification remain separate.",
            "This report cannot authorize training or production activation.",
        ],
    }


def build(directory, application):
    directory = Path(directory)
    raw = {name: (directory / name).read_bytes() for name in INPUTS}
    values = {name: json.loads(value) for name, value in raw.items()}
    result = status(*(values[name] for name in INPUTS), application)
    if any((directory / name).read_bytes() != value for name, value in raw.items()):
        raise ValueError("Comparison evidence changed during reporting")
    result["evidence_sha256"] = {
        name: hashlib.sha256(value).hexdigest() for name, value in raw.items()
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--application", choices=APPLICATIONS, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.comparison, args.application), indent=2))


if __name__ == "__main__":
    main()
