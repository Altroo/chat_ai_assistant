"""Assemble one small TRAIN-only entity pilot with deterministic retained coverage.

No model is loaded. Validation bytes remain unchanged and never supply labels.
The retained sample covers native tools and available argument-shape/enum features,
not all behavior. Only a separately reviewed server run may train this corpus.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import prepare_facturation_entity_spans_v1 as entity
import prepare_facturation_role_variants_v1 as prior

VERSION = "facturation-entity-pilot-v1-en-fr"
SUPPLEMENT_SHA256 = {
    "manifest.json": "f120adf84eb7395209259a4b014e2574bce56531684c4c880e6d9028880e621e",
    "contrasts.jsonl": "ccb425530739f0d701eb8ff59b2590e8e4d36b96aec24fc6e4eec70db5c6214f",
}
APPLICATIONS = ("facturation", "management_projet", "design_workflow")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def target(row):
    calls = row["messages"][-1].get("tool_calls", [])
    if row["messages"][-1].get("role") != "assistant" or len(calls) != 1:
        raise ValueError("One supervised native action required")
    result = calls[0]["function"]
    offered = {t["function"]["name"]: t["function"]["parameters"] for t in row["tools"]}
    if result["name"] not in offered:
        raise ValueError("Target tool is not offered")
    Draft202012Validator(offered[result["name"]]).validate(result["arguments"])
    if row.get("language") not in (None, "en", "fr"):
        raise ValueError("Only approved English/French source rows are supported")
    return result, offered[result["name"]]


def features(arguments, schema, path=""):
    """Finite TRAIN-only shape and schema-enum features; never free-text values."""
    result = {path + ":" + type(arguments).__name__}
    if "enum" in schema:
        result.add(path + ":enum=" + prior.encoded(arguments))
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            result.update(features(value, schema.get("properties", {}).get(key, {}),
                                   path + "/" + key))
    elif isinstance(arguments, list):
        for value in arguments:
            result.update(features(value, schema.get("items", {}), path + "/*"))
    return result


def retained(rows, application, count=72):
    """Round-robin tools, greedily cover shapes/enums, stable hash tie-break."""
    unique = {}
    for index, row in enumerate(rows):
        if row["application"] != application:
            continue
        function, schema = target(row)
        key = prior.canonical_input_key(row)
        identity = digest(prior.encoded(row).encode())
        value = (index, row, function, features(function["arguments"], schema), identity)
        if key in unique and prior.encoded(unique[key][2]) != prior.encoded(function):
            raise ValueError("Conflicting canonical TRAIN targets")
        if key not in unique or identity < unique[key][4]:
            unique[key] = value
    groups = defaultdict(list)
    for item in unique.values():
        groups[item[2]["name"]].append(item)
    if type(count) is not int or count < len(groups) or count > len(unique) or not groups:
        raise ValueError("Budget must cover all tools without repeating inputs")
    covered, selected = defaultdict(set), []
    while len(selected) < count:
        for name in sorted(groups):
            pool = groups[name]
            if not pool:
                continue
            best = min(pool, key=lambda item: (-len(item[3] - covered[name]), item[4]))
            pool.remove(best)
            selected.append(best)
            covered[name].update(best[3])
            if len(selected) == count:
                break
    all_features = defaultdict(set)
    for item in unique.values():
        all_features[item[2]["name"]].update(item[3])
    report = {
        "count": len(selected),
        "by_tool": dict(Counter(item[2]["name"] for item in selected)),
        "language_metadata": dict(Counter(item[1].get("language") or "unspecified" for item in selected)),
        "canonical_source_candidates": len(unique),
        "feature_coverage": {name: {
            "selected": len(covered[name]), "available": len(all_features[name]),
            "uncovered": sorted(all_features[name] - covered[name]),
        } for name in sorted(groups)},
        "selected": [{"source_line": item[0] + 1,
                      "canonical_input_sha256": digest(prior.canonical_input_key(item[1]).encode())}
                     for item in selected],
    }
    return [item[0] for item in selected], report


def prepare(source, supplement, output):
    source, supplement, output = [Path(p).resolve() for p in (source, supplement, output)]
    if output.exists() or any(output == p or p in output.parents for p in (source, supplement)):
        raise ValueError("A new isolated output directory is required")
    raw = {name: (source / name).read_bytes() for name in entity.SOURCE_SHA256}
    if any(digest(value) != entity.SOURCE_SHA256[name] for name, value in raw.items()):
        raise ValueError("Immutable TRAIN/development corpus changed")
    extra = {name: (supplement / name).read_bytes() for name in SUPPLEMENT_SHA256}
    if any(digest(value) != SUPPLEMENT_SHA256[name] for name, value in extra.items()):
        raise ValueError("Reviewed supplement changed")
    source_lines = raw["train.jsonl"].splitlines()
    rows = [json.loads(line) for line in source_lines]
    extra_lines = extra["contrasts.jsonl"].splitlines()
    new_rows = [json.loads(line) for line in extra_lines]
    development = [json.loads(line) for line in raw["valid.jsonl"].splitlines()]
    if len(rows) != 3103 or len(new_rows) != 72 or len(development) != 275:
        raise ValueError("Unexpected exact corpus counts")
    if any(row["application"] != "facturation" for row in new_rows):
        raise ValueError("Supplement application changed")
    selected_lines, plans = list(extra_lines), {}
    for app in APPLICATIONS[1:]:
        indices, report = retained(rows, app)
        if len(report["by_tool"]) != 9:
            raise ValueError("Every retained application must cover all nine native tools")
        for item in report["selected"]:
            item["source_row_sha256"] = digest(source_lines[item["source_line"] - 1])
        plans[app] = report
        selected_lines.extend(source_lines[index] for index in indices)
    selected = [json.loads(line) for line in selected_lines]
    excluded = {prior.canonical_input_key(row) for row in development}
    seen = set()
    for row in selected:
        target(row)
        key = prior.canonical_input_key(row)
        if key in excluded or key in seen:
            raise ValueError("Duplicate candidate or development-input overlap")
        seen.add(key)
    if Counter(row["application"] for row in selected) != Counter(dict.fromkeys(APPLICATIONS, 72)):
        raise ValueError("Exactly 72 rows per declared application required")
    plan = {"version": VERSION, "source_sha256": entity.SOURCE_SHA256,
            "method": "TRAIN-only tool round-robin; unseen argument shape/schema-enum coverage; stable row-hash tie-break",
            "applications": plans, "evaluation_outcomes_used_for_selection": False}
    payload = b"\n".join(selected_lines) + b"\n"
    plan_payload = (json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    files = {"train.jsonl": payload, "valid.jsonl": raw["valid.jsonl"],
             "retained-plan.json": plan_payload}
    manifest = {
        "version": VERSION, "status": "PREPARED PILOT; NOT TRAINED OR ACCEPTED",
        "applications": list(APPLICATIONS), "languages": ["en", "fr"],
        "count": 216, "by_application": dict(Counter(row["application"] for row in selected)),
        "files": {name: digest(value) for name, value in files.items()},
        "source_sha256": entity.SOURCE_SHA256, "supplement_sha256": SUPPLEMENT_SHA256,
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "helper_sha256": {Path(module.__file__).name: digest(Path(module.__file__).read_bytes())
                          for module in (entity, prior)},
        "starting_checkpoint": 600, "complete_epochs": 1, "updates": 216,
        "checkpoint_interval": 72, "development_unchanged": True,
        "training_executed": False, "model_accepted": False, "production_activation": False,
        "limitations": [
            "A small sampled retention curriculum cannot establish absence of regressions.",
            "Retained rows are byte-preserved; missing per-row language metadata stays missing.",
            "Feature coverage records argument shapes/schema enums, not all semantic behavior.",
            "Separate reviewed server preflight, numerical admission and unchanged evaluation gates required.",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, value in files.items():
        (output / name).write_bytes(value)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "supplement", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.supplement, args.output), indent=2))
