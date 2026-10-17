"""Prepare complete argument-shape replay from unchanged approved training rows.

This metadata-only successor preserves the frozen V1 recipe and evaluation
controls. It creates no labels and cannot authorize training or activation.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

V1_SHA256 = "9930425f1b1beb47932e9c632b30bb401f03ef63310661f08729191de783ac17"
if hashlib.sha256(Path(__file__).with_name("prepare_facturation_replay_v1.py").read_bytes()).hexdigest() != V1_SHA256:
    raise ValueError("Frozen V1 preparation changed")

import prepare_facturation_replay_v1 as frozen

base = frozen.base
VERSION = "facturation-replay-v3-en-fr"
APPLICATIONS = frozen.APPLICATIONS
HELPER_SHA256 = {**frozen.HELPER_SHA256, "prepare_facturation_replay_v1.py": V1_SHA256,
                 "prepare_facturation_replay_v2.py": "cb4d11ac174ce02ba39c9ffe72c98d60476446b7760d795691641eb6d870052d",
                 "prepare_shared_v5r5.py": "b7702319000f9d4f0b6f44bab28a2d1063093e0b44a0b2e5bf522f29891f87f6"}
PREDECESSOR_REPORT = "388e6dfd0fe915cb13f85deb9e85aaf16df7272c8f2306ee0e3dd54290fcc258"
# These are annotated TRAINING sources, not independent evaluation cases.
LANGUAGE_SOURCES = {
    "facturation-refinement-v2-en-fr": {
        "manifest": "bf6d6213d4bdce55a217258ea0dea2abc52823a18eefd636797252afe4715673",
        "train.eval.jsonl": "301816a60bd4cc17e78f3402bdd5f9ed0aefa5898ad22e13dab2f149b97f9b3b",
    },
    "management-projet-refinement-v2-en-fr": {
        "manifest": "51afb0a17f841335f3a7f3e830db515c731ac8efea749bd1856f3a2d1e0dea87",
        "train.eval.jsonl": "2f9c929b6bea16e538677c2670cbfce3b6fb18f64ed9215e619bd51e1e0e1462",
    },
    "design-workflow-refinement-v2-en-fr": {
        "manifest": "feb3ee946b89e65bebdd036bb2730badfc36d2799025910a227f56e0ef6dc420",
        "train.eval.jsonl": "2ae8258882b3a68ea7334a2c9c1a9b85393b83b0f58cd8715f531f06089ace7d",
    },
}


def checked_helpers():
    for name, expected in HELPER_SHA256.items():
        if frozen.sha(Path(__file__).with_name(name).read_bytes()) != expected:
            raise ValueError("Reviewed helper changed: " + name)


def current_training_request(row):
    content = row["messages"][-2]["content"]
    prefix = "Earlier user messages (background only): "
    if not content.startswith(prefix):
        return content, len(row["messages"]) > 3
    history, end = json.JSONDecoder().raw_decode(content[len(prefix):])
    tail = content[len(prefix) + end:]
    boundary = "\nCurrent request: "
    if (not isinstance(history, list) or not history
            or any(not isinstance(value, str) for value in history) or not tail.startswith(boundary)):
        raise ValueError("Verified training history wrapper required")
    return tail[len(boundary):], True


def request_languages(rows, language_root=None):
    lookup = {}
    root = frozen.ROOT / "training/datasets" if language_root is None else Path(language_root)
    for dataset, pins in LANGUAGE_SOURCES.items():
        directory = root / dataset
        manifest_raw = (directory / "manifest.json").read_bytes()
        payload = (directory / "train.eval.jsonl").read_bytes()
        if (frozen.sha(manifest_raw) != pins["manifest"]
                or frozen.sha(payload) != pins["train.eval.jsonl"]
                or json.loads(manifest_raw)["files"]["train.eval.jsonl"] != pins["train.eval.jsonl"]):
            raise ValueError("Reviewed training language provenance changed: " + dataset)
        for item in map(json.loads, payload.splitlines()):
            app, language = item["trusted_context"]["application"], item["language"]
            if language not in ("en", "fr") or app not in APPLICATIONS:
                raise ValueError("English/French training language provenance required")
            key = app, item["messages"][-1]["content"]
            if key in lookup and lookup[key][0] != language:
                raise ValueError("Contradictory training request language provenance")
            lookup[key] = language, dataset
    resolved = []
    for row in rows:
        request, _ = current_training_request(row)
        inherited = lookup.get((row["application"], request))
        explicit = row.get("language")
        if explicit is not None:
            if explicit not in ("en", "fr") or (inherited and inherited[0] != explicit):
                raise ValueError("Contradictory explicit request language")
            resolved.append({"language": explicit, "source": "explicit_row_metadata"})
        elif inherited:
            resolved.append({"language": inherited[0], "source": inherited[1]})
        else:
            resolved.append({"language": "unknown", "source": "unresolved_legacy_training"})
    return resolved


def context_features(row, request_language=None):
    """Use semantic shapes, never particular record IDs or calendar values."""
    context = json.loads(row["messages"][0]["content"].split("Trusted context: ", 1)[1])
    interface_language = context.get("interface_language")
    language = row.get("language", "unknown") if request_language is None else request_language
    if (context.get("application") != row["application"] or interface_language not in ("en", "fr")
            or language not in ("en", "fr", "unknown")
            or ("language" in row and row["language"] != language)):
        raise ValueError("Verified request language and English/French interface required")
    count = context.get("previous_result_count", 0)
    if type(count) is not int or count < 0:
        raise ValueError("Nonnegative trusted result count required")
    capabilities = context.get("capabilities")
    if capabilities is not None and (
            not isinstance(capabilities, list) or any(not isinstance(v, str) for v in capabilities)):
        raise ValueError("Trusted capability list required")
    return language, {
        "interface_language": interface_language,
        "current_resource": context.get("current_resource"),
        "has_current_identifier": context.get("current_identifier") is not None,
        "has_current_invoice": context.get("current_invoice_id") is not None,
        "previous_result_type": context.get("previous_result_type"),
        "previous_result_count": "none" if count == 0 else "one" if count == 1 else "multiple",
        "capabilities": sorted(set(capabilities)) if capabilities is not None else None,
        "has_history": current_training_request(row)[1],
    }


NEUTRAL_HISTORY = ("Hello", "Bonjour", "Hello, thanks for your help.", "Bonjour, merci pour votre aide.")
INTENT_FIELDS = ("resource", "metric", "period", "status", "operation", "reason", "unpaid")


def scenario_messages(messages):
    """Undo only the four pinned synthetic greeting augmentations.

    Real histories, altered greetings and malformed wrappers remain exact and
    cannot borrow a scenario from an unrelated original request.
    """
    result = deepcopy(messages)
    prefix = "Earlier user messages (background only): "
    if len(result) == 2 and result[-1].get("role") == "user":
        content = result[-1].get("content", "")
        if isinstance(content, str) and content.startswith(prefix):
            try:
                history, end = json.JSONDecoder().raw_decode(content[len(prefix):])
            except ValueError:
                return result
            tail = content[len(prefix) + end:]
            if (isinstance(history, list) and len(history) == 1
                    and history[0] in NEUTRAL_HISTORY and tail.startswith("\nCurrent request: ")):
                result[-1]["content"] = tail[len("\nCurrent request: "):]
    return result


def scenario_key(application, messages, tools, action):
    # Full messages (apart from the four pinned neutral augmentations),
    # offered schemas and target must agree. Text-only joins are forbidden.
    return base.encoded({"application": application, "messages": scenario_messages(messages),
                         "tools": [t for t in tools if t["function"]["name"] != "clarify"],
                         "action": action})


def training_scenarios(rows, language_root=None):
    root = frozen.ROOT / "training/datasets" if language_root is None else Path(language_root)
    import ast
    augmentation = Path(__file__).with_name("prepare_shared_v5r5.py").read_bytes()
    if frozen.sha(augmentation) != HELPER_SHA256["prepare_shared_v5r5.py"]:
        raise ValueError("Pinned neutral training augmentation changed")
    declared = [node for node in ast.parse(augmentation).body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "NEUTRAL" for target in node.targets)]
    if len(declared) != 1 or ast.literal_eval(declared[0].value) != NEUTRAL_HISTORY:
        raise ValueError("Neutral augmentation provenance differs")
    lookup = {}
    for dataset, pins in LANGUAGE_SOURCES.items():
        directory = root / dataset
        manifest_raw = (directory / "manifest.json").read_bytes()
        payload = (directory / "train.eval.jsonl").read_bytes()
        if (frozen.sha(manifest_raw) != pins["manifest"]
                or frozen.sha(payload) != pins["train.eval.jsonl"]
                or json.loads(manifest_raw)["files"]["train.eval.jsonl"] != pins["train.eval.jsonl"]):
            raise ValueError("Reviewed training scenario provenance changed: " + dataset)
        for item in map(json.loads, payload.splitlines()):
            app, category = item["trusted_context"]["application"], item["category"]
            if (app not in APPLICATIONS or not isinstance(category, str) or not category
                    or item["language"] not in ("en", "fr")
                    or json.loads(item["messages"][0]["content"].split("Trusted context: ", 1)[1]) != item["trusted_context"]):
                raise ValueError("Verified training scenario metadata required")
            action = {"name": item["expected"]["tool"], "arguments": item["expected"]["arguments"]}
            key = scenario_key(app, item["messages"], item["offered_tool_schemas"], action)
            entry = {"category": category, "language": item["language"], "source": dataset}
            if key in lookup and lookup[key] != entry:
                raise ValueError("Contradictory exact training scenario provenance")
            lookup[key] = entry
    result = []
    for row in rows:
        if row.get("curriculum_category"):
            result.append({"category": row["curriculum_category"], "source": "explicit_row_metadata"})
        else:
            key = scenario_key(row["application"], row["messages"][:-1], row["tools"], base.target(row))
            entry = lookup.get(key)
            result.append(entry if entry is not None else {"category": None, "source": "unresolved_legacy_training"})
    return result


def argument_shape(value):
    """Preserve every nested field/type conjunction without IDs or text values."""
    if value is None:
        return ["null"]
    if type(value) is bool:
        return ["boolean"]
    if type(value) is int:
        return ["integer"]
    if type(value) is float:
        if not __import__("math").isfinite(value):
            raise ValueError("Finite JSON numbers required")
        return ["number"]
    if isinstance(value, str):
        return ["string"]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        return ["object", [[key, argument_shape(value[key])] for key in sorted(value)]]
    if isinstance(value, list):
        return ["array", sorted({base.encoded(argument_shape(item)) for item in value})]
    raise ValueError("Strict JSON argument types required")


def retention_features(row, request_language=None, scenario=None):
    """Cover available joint intents/context/languages and bilingual omissions.

    This is a bounded projection of the existing training curriculum, not every
    free-text argument combination. No evaluation outcomes select rows.
    """
    language, context = context_features(row, request_language)
    action = base.target(row)
    app, tool, arguments = row["application"], action["name"], action["arguments"]
    schema = next(t["function"]["parameters"] for t in row["tools"] if t["function"]["name"] == tool)
    properties = schema.get("properties", {})
    finite = {name: value for name, value in arguments.items()
              if "enum" in properties.get(name, {}) or type(value) is bool or name in INTENT_FIELDS}
    result = set(frozen.retention_features(row))
    result.add((app, "joint_intent_context_language", language, tool,
                base.encoded(finite), base.encoded(context)))
    result.add((app, "joint_argument_context_language", language, tool,
                base.encoded(finite), base.encoded(argument_shape(arguments)), base.encoded(context)))
    if scenario is not None and scenario.get("category") is not None:
        if scenario.get("language", language) != language:
            raise ValueError("Training scenario and request language disagree")
        result.add((app, "verified_training_scenario", language, tool, scenario["category"],
                    base.encoded(finite), base.encoded(argument_shape(arguments)), base.encoded(context)))
    for name in properties:
        result.add((app, "argument_language", tool, language, name, str(name in arguments)))
    if row.get("curriculum_category"):
        # Original V1 focus date examples include a synthetic literal date.
        # Retain the declared operator and argument structure, not each date.
        contrast = {k: v for k, v in row.get("contrast", {}).items() if k != "literal_date"}
        result.add((app, "curriculum_semantics", language, tool, row["curriculum_category"],
                    base.encoded(finite), base.encoded(sorted(arguments)), base.encoded(contrast)))
    return result


def eligible_pools(rows, focus_indices):
    if (len(rows) != 2975 or len(focus_indices) != 1487
            or len(set(focus_indices)) != 1487
            or any(type(i) is not int or not 0 <= i < len(rows) for i in focus_indices)
            or set(focus_indices[:931]) != {i for i in range(2419) if rows[i]["application"] == "facturation"}
            or focus_indices[931:] != list(range(2419, 2975))
            or any(rows[i]["application"] != "facturation" for i in focus_indices)):
        raise ValueError("Reviewed focused source mapping required")
    new = list(focus_indices[1047:])
    inherited = list(focus_indices[931:1047])
    replay = sorted(set(range(len(rows))) - set(new))
    if len(new) != 440 or len(inherited) != 116 or len(replay) != 2535:
        raise ValueError("Reviewed source pool dimensions changed")
    if not set(inherited) <= set(replay):
        raise ValueError("Inherited focus curriculum excluded from replay")
    return new, replay, inherited


def bucket(index, rows, new_pool):
    return "new_facturation" if index in new_pool else "retained_" + rows[index]["application"]


def selection(rows, focus_indices, maximum=2975, *, language_root=None):
    if type(maximum) is not int or not 1 <= maximum <= 2975:
        raise ValueError("Positive selection budget within source size required")
    new_pool, replay_pool, inherited = eligible_pools(rows, focus_indices)
    languages = request_languages(rows, language_root)
    scenarios = training_scenarios(rows, language_root)
    axes = {i: frozen.prior.axis_features(rows[i]) for i in new_pool}
    required_axes = set().union(*axes.values())
    new_features = {i: axes[i] | retention_features(rows[i], languages[i]["language"], scenarios[i]) for i in new_pool}
    required_new = set().union(*new_features.values())
    new = frozen.greedy_units(rows, frozen.contrast_blocks(rows, new_pool), new_features, required_new)
    features = {i: retention_features(rows[i], languages[i]["language"], scenarios[i]) for i in replay_pool}
    required_retention = set().union(*features.values())
    replay = frozen.greedy_units(rows, [[i] for i in replay_pool], features, required_retention)
    chosen = new + replay
    if len(chosen) > maximum or len(chosen) != len(set(chosen)):
        raise ValueError("Selection budget cannot cover contrasts and joint-context replay")
    if len({base.model_input_key(rows[i]) for i in chosen}) != len(chosen):
        raise ValueError("Selection has duplicate model inputs")
    new_set = set(new_pool)
    buckets = [{"application": bucket(i, rows, new_set)} for i in chosen]
    order = [chosen[i] for i in frozen.complete_epoch_order(buckets)]
    windows = [{"first_step": start + 1, "last_step": min(start + 32, len(order)),
                "by_source_bucket": dict(Counter(bucket(i, rows, new_set) for i in order[start:start + 32]))}
               for start in range(0, len(order), 32)]
    inherited_features = set().union(*(features[i] for i in inherited))
    if not inherited_features <= set().union(*(features[i] for i in replay)):
        raise ValueError("Inherited curriculum semantics not covered")
    return {
        "contract": "complete-contrast-blocks-with-nested-argument-context-bilingual-training-replay",
        "row_indices": order, "count": len(order),
        "new_training_rows": sorted(new), "retained_training_rows": sorted(replay),
        "by_source_bucket": dict(Counter(bucket(i, rows, new_set) for i in order)),
        "eligible_training_rows": {"new": new_pool, "replay": replay_pool, "inherited_focus": inherited},
        "selected_inherited_focus_count": len(set(replay) & set(inherited)),
        "request_language_by_row": languages,
        "training_scenario_by_row": scenarios,
        "training_scenario_counts": dict(Counter(item["category"] or "unresolved" for item in scenarios)),
        "request_language_counts": dict(Counter(item["language"] for item in languages)),
        "unresolved_request_language_indices": [i for i, item in enumerate(languages) if item["language"] == "unknown"],
        "covered_axes": [list(v) for v in sorted(required_axes)],
        "new_training_features": [list(v) for v in sorted(required_new)],
        "retention_features": [list(v) for v in sorted(required_retention)],
        "inherited_retention_features": [list(v) for v in sorted(inherited_features)],
        "schedule_windows": windows,
        "selected_rows_sha256": frozen.sha(base.encoded([rows[i] for i in order]).encode()),
        "limitations": [
            "Covers every available nested argument-field/type, finite intent, trusted context and request-language conjunction.",
            "New contrast selection covers these conjunctions as well as the original contrast axes.",
            "Shape coverage does not imply coverage of every free-text meaning or paraphrase.",
            "Inherited focus examples are replay-eligible; semantic coverage does not require every paraphrase.",
            "Request language uses explicit or pinned training provenance; unresolved legacy rows stay unknown.",
            "Interface language and background-history language are never request-language labels.",
            "Scenario intent uses explicit metadata or matching full training messages/schemas/targets, normalizing only four pinned neutral greetings.",
            "Uses only existing training inputs and metadata; evaluation outcomes do not select rows.",
            "Static coverage and diagnostics do not predict retention or 95 percent accuracy.",
            "No numerical work, longer run, acceptance result or production activation is admitted.",
        ],
    }


def capture_plan(rows, valid_rows, chosen):
    new_pool = set(chosen["eligible_training_rows"]["new"])
    train = []
    for name in chosen["by_source_bucket"]:
        eligible = [i for i in chosen["row_indices"] if bucket(i, rows, new_pool) == name]
        if len(eligible) < 2:
            raise ValueError("Two training diagnostics per source bucket required")
        train.extend(sorted(eligible, key=lambda i: frozen.sha(base.model_input_key(rows[i]).encode()))[:2])
    valid = []
    for app in APPLICATIONS:
        eligible = [i for i, row in enumerate(valid_rows) if row["application"] == app]
        if len(eligible) < 2:
            raise ValueError("Two development diagnostics per application required")
        valid.extend(sorted(eligible, key=lambda i: frozen.sha(base.model_input_key(valid_rows[i]).encode()))[:2])
    return {"train": train, "valid": valid}


def material():
    checked_helpers()
    shared, focus, rows, train_bytes, valid_bytes, focus_indices = frozen.combined()
    chosen = selection(rows, focus_indices)
    valid_rows = [json.loads(line) for line in valid_bytes.splitlines()]
    captures = capture_plan(rows, valid_rows, chosen)
    native = deepcopy(shared["native_metadata"])
    native["facturation"] = focus["native_metadata"]["facturation"]
    manifest = {
        "version": VERSION, "applications": list(APPLICATIONS), "languages": ["en", "fr"],
        "status": "PREPARATION ONLY; no numerical work or accuracy claim",
        "generator_sha256": frozen.sha(Path(__file__).read_bytes()),
        "helper_sha256": {"training/scripts/" + name: expected for name, expected in HELPER_SHA256.items()},
        "source_manifests": {frozen.SHARED: frozen.SHARED_SHA256, frozen.FOCUS: frozen.FOCUS_SHA256},
        "request_language_sources": deepcopy(LANGUAGE_SOURCES),
        "focus_row_indices": focus_indices,
        "counts": {"train": len(rows), "valid": len(valid_rows), "cumulative_prefix": 2419,
                   "inherited_focus": 116, "new_focus": 440,
                   "by_application": dict(Counter(r["application"] for r in rows))},
        "files": {"train.jsonl": frozen.sha(train_bytes), "valid.jsonl": frozen.sha(valid_bytes)},
        "native_metadata": native, **frozen.control_metadata(shared, focus),
        "selection_sha256": frozen.sha(base.encoded(chosen).encode()),
        "captures_sha256": frozen.sha(base.encoded(captures).encode()),
        "starting_model": {
            "required_predecessor_selected_step": 600,
            "required_predecessor_report_sha256": PREDECESSOR_REPORT,
            "actual_model_binding_required_before_numerical_work": True,
            "disposable_adapter_must_not_be_used": True,
        },
        "training_executed": False, "model_accepted": False,
        "full_training_authorized": False, "production_activation": False,
    }
    return manifest, {"train": train_bytes, "valid": valid_bytes}, chosen, captures


def admit_prepared(data, expected_manifest_sha256):
    """Reproduce the source/selection contract before any separate numerical job."""
    data = Path(data)
    raw = (data / "manifest.json").read_bytes()
    if frozen.sha(raw) != expected_manifest_sha256:
        raise ValueError("Reviewed preparation manifest changed")
    manifest = json.loads(raw)
    expected_helpers = {"training/scripts/" + name: value for name, value in HELPER_SHA256.items()}
    if (manifest.get("version") != VERSION or manifest.get("applications") != list(APPLICATIONS)
            or manifest.get("languages") != ["en", "fr"]
            or manifest.get("generator_sha256") != frozen.sha(Path(__file__).read_bytes())
            or manifest.get("helper_sha256") != expected_helpers
            or manifest.get("source_manifests") != {
                frozen.SHARED: frozen.SHARED_SHA256, frozen.FOCUS: frozen.FOCUS_SHA256}
            or manifest.get("request_language_sources") != LANGUAGE_SOURCES
            or manifest.get("starting_model") != {
                "required_predecessor_selected_step": 600,
                "required_predecessor_report_sha256": PREDECESSOR_REPORT,
                "actual_model_binding_required_before_numerical_work": True,
                "disposable_adapter_must_not_be_used": True}
            or any(manifest.get(key) is not False for key in (
                "training_executed", "model_accepted", "full_training_authorized", "production_activation"))):
        raise ValueError("Prepared scope, provenance or selection differs from reviewed source")
    checked_helpers()
    audit = base.audit(data)
    payloads = {split: (data / (split + ".jsonl")).read_bytes() for split in ("train", "valid")}
    rows = {s: [json.loads(line) for line in value.splitlines()] for s, value in payloads.items()}
    if len(rows["train"]) != 2975 or len(rows["valid"]) != 275:
        raise ValueError("Reviewed prepared data dimensions changed")
    language_root = data / "language_sources"
    chosen = selection(rows["train"], manifest["focus_row_indices"], language_root=language_root)
    captures = capture_plan(rows["train"], rows["valid"], chosen)
    if (manifest.get("selection_sha256") != frozen.sha(base.encoded(chosen).encode())
            or manifest.get("captures_sha256") != frozen.sha(base.encoded(captures).encode())):
        raise ValueError("Prepared deterministic selection or diagnostic plan changed")
    audit["rehearsal"] = chosen
    checked_helpers()
    if request_languages(rows["train"], language_root) != chosen["request_language_by_row"]:
        raise ValueError("Prepared language provenance changed during admission")
    if (data / "manifest.json").read_bytes() != raw or any(
            frozen.sha(value) != audit["input_sha256"][split]
            or (data / (split + ".jsonl")).read_bytes() != value
            for split, value in payloads.items()):
        raise ValueError("Prepared data changed during admission")
    lineage = {
        "application": "facturation", "retained_applications": ["management_projet", "design_workflow"],
        "manifest_sha256": expected_manifest_sha256, "source_manifests": manifest["source_manifests"],
        "model_acceptance_verified": False, "longer_training_admitted": False,
        "actual_model_binding_required_before_numerical_work": True,
        "disposable_adapter_must_not_be_used": True,
    }
    return audit, rows, captures, lineage


def prepare(output):
    output = Path(output)
    if output.exists():
        raise ValueError("Never overwrite existing preparation")
    manifest, payloads, chosen, captures = material()
    generator = manifest["generator_sha256"]
    output.mkdir(parents=True)
    for split, payload in payloads.items():
        (output / (split + ".jsonl")).write_bytes(payload)
    # Keep admission self-contained in isolated server staging. Only pinned
    # synthetic TRAINING metadata is copied, never independent cases.
    for dataset, pins in LANGUAGE_SOURCES.items():
        target = output / "language_sources" / dataset
        target.mkdir(parents=True)
        for name, expected in (("manifest.json", pins["manifest"]),
                               ("train.eval.jsonl", pins["train.eval.jsonl"])):
            payload = (frozen.ROOT / "training/datasets" / dataset / name).read_bytes()
            if frozen.sha(payload) != expected:
                raise ValueError("Training language provenance changed during preparation")
            (target / name).write_bytes(payload)
    raw = (json.dumps(manifest, indent=2) + "\n").encode()
    (output / "manifest.json").write_bytes(raw)
    audit, _, admitted_captures, lineage = admit_prepared(output, frozen.sha(raw))
    checked_helpers()
    frozen.source(frozen.SHARED, frozen.SHARED_SHA256)
    frozen.source(frozen.FOCUS, frozen.FOCUS_SHA256)
    if frozen.sha(Path(__file__).read_bytes()) != generator:
        raise ValueError("Generator changed during preparation")
    if admitted_captures != captures:
        raise ValueError("Diagnostic selection changed during preparation")
    report = {
        "version": VERSION, "manifest_sha256": frozen.sha(raw),
        "audit": audit, "selection": chosen,
        "captures": {**captures, "total": 14,
                     "scope": "Eight training and six development diagnostics; not acceptance"},
        "lineage": lineage, "training_executed": False, "accuracy_estimated": False,
        "model_accepted": False, "production_activation": False,
    }
    (output / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    report = prepare(parser.parse_args().output)
    print(json.dumps({
        "rows_checked": report["audit"]["rows_checked"],
        "selected_updates": report["selection"]["count"],
        "by_source_bucket": report["selection"]["by_source_bucket"],
        "training_executed": False, "accuracy_estimated": False,
    }))


if __name__ == "__main__":
    main()
