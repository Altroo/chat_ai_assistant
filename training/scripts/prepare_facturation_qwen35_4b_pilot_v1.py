"""Select a bounded TRAIN-only coverage pilot for the new shared model.

Copies reviewed rows unchanged. Selection does not read validation answers or
model outcomes and does not authorize numerical training or deployment.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "training/datasets/facturation-qwen35-4b-v1-en-fr"
PARENT_SHA = "1f4c8863adabacc776947c54529a0190e6b7a9a2c076355d47c79267ecb75a6b"
REPLAY_SHA = "0638fdeb8d9ffbdd97af54f1feba6b7bf218f977fafdea89ad4e217d17757814"
VERSION = "facturation-qwen35-4b-pilot-v1-en-fr"
MAXIMUM = 640
MANDATORY = {18, 19, *range(1487, 1503)}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def helpers(manifest):
    pins = dict(manifest["helper_sha256"])
    pins["training/scripts/prepare_facturation_qwen35_4b_v1.py"] = manifest["generator_sha256"]
    pins["training/scripts/prepare_facturation_replay_v3.py"] = REPLAY_SHA
    for name, digest in pins.items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("Reviewed pilot dependency changed: " + name)
    import prepare_facturation_replay_v3 as prior
    prior.checked_helpers()
    for name, digest in prior.HELPER_SHA256.items():
        pins["training/scripts/" + name] = digest
    for folder, values in prior.LANGUAGE_SOURCES.items():
        for filename, digest in values.items():
            name = "manifest.json" if filename == "manifest" else filename
            pins["training/datasets/" + folder + "/" + name] = digest
    for name, digest in pins.items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("Reviewed pilot provenance changed: " + name)
    return prior, pins


def features(row, language, prior):
    call = row["messages"][-1]["tool_calls"][0]["function"]
    tool, arguments = call["name"], call["arguments"]
    trusted = json.loads(row["messages"][0]["content"].split("Trusted context: ", 1)[1])
    schema = next(t["function"]["parameters"] for t in row["tools"]
                  if t["function"]["name"] == tool)
    properties = schema.get("properties", {})
    finite = {name: value for name, value in arguments.items()
              if isinstance(value, bool) or "enum" in properties.get(name, {})
              or name in ("resource", "metric", "period", "status", "operation", "reason")}
    result = {
        ("tool_language", tool, language),
        ("intent_language", tool, language, canonical(finite)),
        ("shape_language", tool, language, canonical(prior.argument_shape(arguments))),
        ("category_language", row.get("curriculum_category", "legacy"), language),
    }
    for name in properties:
        result.add(("argument_presence", tool, language, name, str(name in arguments)))
    result.add(("tool_bundle", tool, language,
                canonical(sorted(t["function"]["name"] for t in row["tools"]))))
    context = {name: (trusted[name] if name in ("current_resource", "previous_result_type")
                      else bool(trusted[name]))
               for name in ("current_resource", "current_identifier", "current_invoice_id",
                            "previous_result_type", "previous_result_count") if name in trusted}
    result.add(("context", tool, language, canonical(context)))
    for name in ("mode", "operator", "optional_state", "filter", "quoted", "style", "date_mode"):
        if name in row.get("contrast", {}):
            result.add(("factor", tool, language, row.get("curriculum_category"),
                        name, canonical(row["contrast"][name])))
    return result


def select(rows, prior, maximum=MAXIMUM):
    if len(rows) != 1503 or not len(MANDATORY) <= maximum <= len(rows):
        raise ValueError("Complete reviewed corpus and a bounded positive budget required")
    language_provenance = prior.request_languages(rows)
    # These two reviewed request corrections retain their legacy row metadata.
    # Language is explicit in the pinned correction, independent of UI language.
    for index, language in ((18, "en"), (19, "fr")):
        language_provenance[index] = {"language": language,
                                     "source": "reviewed_explicit_role_correction"}
    axes = [features(row, language["language"], prior)
            for row, language in zip(rows, language_provenance)]
    required = set().union(*axes)
    chosen = set(MANDATORY)
    uncovered = required - set().union(*(axes[index] for index in chosen))
    while uncovered:
        if len(chosen) >= maximum:
            raise ValueError("Pilot budget cannot preserve declared coverage")
        best = max((i for i in range(len(rows)) if i not in chosen),
                   key=lambda i: (len(axes[i] & uncovered), sha(str(i).encode())))
        if not axes[best] & uncovered:
            raise ValueError("Unreachable coverage feature")
        chosen.add(best)
        uncovered -= axes[best]
    indices = sorted(chosen)
    return {
        "source_indices_zero_based": indices,
        "source_row_count": len(rows), "count": len(indices), "maximum": maximum,
        "projected_features_available": len(required),
        "projected_features_selected": len(set().union(*(axes[i] for i in indices))),
        "uncovered_projected_features": [],
        "by_tool": dict(sorted(Counter(
            rows[i]["messages"][-1]["tool_calls"][0]["function"]["name"] for i in indices).items())),
        "by_request_language": dict(sorted(Counter(
            language_provenance[i]["language"] for i in indices).items())),
        "mandatory_rows_present": MANDATORY <= chosen,
        "source_unknown_language_rows": sum(v["language"] == "unknown" for v in language_provenance),
        "language_policy": "Keep unresolved legacy metadata unknown; never infer request language from UI language.",
        "selection_policy": "Greedy projected coverage with deterministic hash tie breaking; not a proven minimum.",
        "evaluation_outcomes_used": False,
    }


def prepare(output):
    if output.exists() or not output.parent.is_dir():
        raise ValueError("New isolated output with existing parent required")
    raw_manifest = (PARENT / "manifest.json").read_bytes()
    if sha(raw_manifest) != PARENT_SHA:
        raise ValueError("Reviewed parent manifest changed")
    manifest = json.loads(raw_manifest)
    payloads = {name: (PARENT / name).read_bytes() for name in ("train.jsonl", "valid.jsonl")}
    for name, raw in payloads.items():
        if sha(raw) != manifest["files"][name]:
            raise ValueError("Reviewed parent split changed: " + name)
    prior, pins = helpers(manifest)
    rows = [json.loads(line) for line in payloads["train.jsonl"].splitlines()]
    plan = select(rows, prior)
    lines = payloads["train.jsonl"].splitlines(keepends=True)
    if any(not line.endswith(b"\n") for line in lines):
        raise ValueError("Complete source row boundaries required")
    train = b"".join(lines[i] for i in plan["source_indices_zero_based"])
    if len(plan["by_tool"]) != 18 or not plan["mandatory_rows_present"]:
        raise ValueError("All native tools and corrected role rows required")
    summary = {
        "version": VERSION, "status": "PREPARED ONLY; NOT TRAINED OR ACCEPTED",
        "applications": ["facturation"], "languages": ["en", "fr"],
        "source_manifest_sha256": PARENT_SHA,
        "generator_sha256": sha(Path(__file__).read_bytes()),
        "helper_sha256": pins, "selection": plan,
        "counts": {"train": plan["count"], "valid": 133},
        "native_metadata": manifest["native_metadata"],
        "held_out": manifest["held_out"],
        "historical_regression_held_out": manifest["historical_regression_held_out"],
        "fresh_controls": manifest["fresh_controls"],
        "files": {"train.jsonl": sha(train), "valid.jsonl": sha(payloads["valid.jsonl"])},
        "training_executed": False, "model_accepted": False, "production_activation": False,
        "limitations": [
            "Coverage is a declared projection, not every feature interaction or proven accuracy.",
            "All selected rows and original validation bytes are copied unchanged.",
            "Unknown legacy request-language metadata is not counted as English or French.",
            "Requires server tokenizer preflight, successful capacity measurement and numerical recipe review.",
            "No automatic production activation or next-application training.",
        ],
    }
    if (PARENT / "manifest.json").read_bytes() != raw_manifest or helpers(manifest)[1] != pins:
        raise ValueError("Preparation dependencies changed during selection")
    output.mkdir()
    for name, raw in {"train.jsonl": train, "valid.jsonl": payloads["valid.jsonl"]}.items():
        (output / name).write_bytes(raw)
    (output / "manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "training/datasets" / VERSION)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output)["selection"], ensure_ascii=False))
