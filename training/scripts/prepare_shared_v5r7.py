"""Assemble reviewed training replacements and selection contrasts, without training.

Completed R6 datasets and original evaluation scores are never overwritten.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from jsonschema import validate

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/chat_ai_assistant/__init__.py").exists())
sys.path.insert(0, str(ROOT / "training/scripts"))
from build_shared_v5r3 import key
from prepare_shared_v5r6 import current_request
PINS = {'shared-v5r6-en-fr': '71d2f2e11ce5f7abf55a32b486c76169d67e8231547084d42ce1c08583ca60b4', 'training-scope-errata-v1-en-fr': '3112f4dcd745fad241019f40cd08991b07faa15de3fb788b233b6d02d488994e', 'selection-contrasts-v1-en-fr': '114933e8f298d6a97abfbf8de114ad62e4c24f56326fa566226a5983b0e994a0', 'shared-validation-v2-en-fr': '3a0b7d2ec0b42be841af4b367d5a159022097f6faf0146e50f8610b5a35f3792', 'shared-dialogue-v1-en-fr': '5bfa383c276e28cf3a78a20788d1b51fd7769563243aa26f33fcab7fed9b13e3', 'shared-dialogue-v2-en-fr': '6e8df0592ddcde75fd2d4c1277aaf789545cd7f1ca9224fc756787abe22e73f3'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_sources(root):
    values = {}
    for name, expected in PINS.items():
        folder = root / "training/datasets" / name
        require(sha(folder / "manifest.json") == expected, "Reviewed manifest changed: " + name)
        manifest = json.loads((folder / "manifest.json").read_text())
        for filename, digest in manifest["files"].items():
            require(sha(folder / filename) == digest, "Reviewed source changed: " + name + "/" + filename)
        values[name] = (folder, manifest)
    return values

def replace_rows(original, replacements, provenance, extra_count):
    require(len(original) == 1969 and len(replacements) == len(provenance) == 12 and extra_count == 96, "Prepared source counts differ")
    indices = [entry["source_index"] for entry in provenance]
    require(len(set(indices)) == len(indices), "Duplicate replacement index")
    merged = original.copy()
    for line, item in zip(replacements, provenance):
        index = item["source_index"]
        require(0 <= index < len(original), "Replacement index outside parent")
        old, new = json.loads(original[index]), json.loads(line)
        require(current_request(old) == item["old_request"] and current_request(new) == item["new_request"], "Replacement request mismatch")
        require(old["messages"][-2]["content"][:-len(item["old_request"])] == new["messages"][-2]["content"][:-len(item["new_request"])], "Replacement changed history")
        old["messages"][-2]["content"] = new["messages"][-2]["content"]
        require(old == new, "Replacement changed more than the reviewed user request")
        merged[index] = line
    require(sum(a == b for a, b in zip(original, merged)) == 1957, "Unexpected retained row count")
    return merged

def assemble(sources):
    parent, parent_manifest = sources["shared-v5r6-en-fr"]
    errata, errata_manifest = sources["training-scope-errata-v1-en-fr"]
    contrasts, contrasts_manifest = sources["selection-contrasts-v1-en-fr"]
    validation, validation_manifest = sources["shared-validation-v2-en-fr"]
    original = (parent / "train.jsonl").read_text().splitlines(keepends=True)
    replacements = (errata / "train.replacements.jsonl").read_text().splitlines(keepends=True)
    extra = (contrasts / "train.jsonl").read_text().splitlines(keepends=True)
    provenance = errata_manifest["provenance"]
    merged = replace_rows(original, replacements, provenance, len(extra))
    train = "".join(merged + extra)
    prior_inputs = {json.dumps({"messages": r["messages"][:-1], "tools": r["tools"]}, sort_keys=True) for r in map(json.loads, merged)}
    extra_inputs = [json.dumps({"messages": r["messages"][:-1], "tools": r["tools"]}, sort_keys=True) for r in map(json.loads, extra)]
    require(len(set(extra_inputs)) == 96 and not prior_inputs.intersection(extra_inputs), "Duplicate added model inputs")
    valid = (validation / "valid.jsonl").read_text()
    rows = list(map(json.loads, train.splitlines()))
    valid_rows = list(map(json.loads, valid.splitlines()))
    require(len(valid_rows) == 275, "Validation size changed")
    exclusions = set()
    for folder in (parent, validation):
        for row in map(json.loads, (folder / "valid.jsonl").read_text().splitlines()):
            exclusions.add(key(row["application"], current_request(row)))
    held = {}
    for name in ("shared-dialogue-v1-en-fr", "shared-dialogue-v2-en-fr"):
        folder, manifest = sources[name]
        held[name] = {str((folder / filename).relative_to(ROOT)): {"sha256": manifest["files"][filename], "count": info["count"]} for filename, info in manifest["inputs"].items()}
        for filename in manifest["inputs"]:
            for row in map(json.loads, (folder / filename).read_text().splitlines()):
                app = json.loads(row["messages"][0]["content"].split("Trusted context: ", 1)[1])["application"]
                exclusions.add(key(app, current_request({"messages": row["messages"] + [{}]})))
    require(not any(key(row["application"], current_request(row)) in exclusions for row in rows), "Training request overlaps validation or held-out split")
    for row in rows + valid_rows:
        target = row["messages"][-1]["tool_calls"][0]["function"]
        schemas = {tool["function"]["name"]: tool["function"]["parameters"] for tool in row["tools"]}
        require(target["name"] in schemas, "Unregistered target")
        validate(target["arguments"], schemas[target["name"]])
    require(not re.search(r"[\u0600-\u06ff]|BEGIN.{0,12}PRIVATE KEY|Bearer\s+\S+|(?:password|api_key|secret)\s*[:=]", train + valid, re.I), "Sensitive or out-of-scope text")
    return {"train.jsonl": train, "valid.jsonl": valid}, {"train": len(rows), "valid": len(valid_rows), "retained_train_bytes": 1957, "replaced_train_rows": 12, "added_training_contrasts": 96, "by_application": dict(Counter(row["application"] for row in rows))}, held

def prepare(root=ROOT, output=None):
    output = output or root / "training/datasets/shared-v5r7-en-fr"
    require(not output.exists(), "Never overwrite versioned data")
    sources = load_sources(root)
    payloads, counts, held = assemble(sources)
    manifest = {"version": output.name, "applications": ["facturation", "management_projet", "design_workflow"], "languages": ["en", "fr"], "status": "PREPARED ONLY; not trained or evaluated", "generator_sha256": sha(Path(__file__)), "source_manifest_sha256": PINS, "counts": counts, "files": {name: hashlib.sha256(value.encode()).hexdigest() for name, value in payloads.items()}, "held_out": held["shared-dialogue-v2-en-fr"], "historical_regression_held_out": held["shared-dialogue-v1-en-fr"], "held_out_count": 438, "evaluation_manifest_sha256": PINS["shared-dialogue-v2-en-fr"], "historical_evaluation_manifest_sha256": PINS["shared-dialogue-v1-en-fr"], "validation_policy": "Uses separately versioned V2 validation: reviewed question clarifications, unchanged targets. Baseline and candidate must use this same split; its scores are not directly comparable with V1. Original V1 datasets and scores remain unchanged.", "training_policy": "Replace twelve indexed instructions, retain all other parent bytes and append 96 reviewed training-only context contrasts. No held-out labels create examples. Contrasts and language/history variants are correlated, not independent scenarios. Server-only training requires separate baseline, resource and configuration checks. No model download, optimization or activation follows preparation.", "limitations": ["Normalized exact request overlap is rejected against both validation and evaluation versions; exhaustive semantic near-duplicate exclusion is not claimed.", "Prepared data establishes no measured accuracy improvement."]}
    output.mkdir()
    for name, value in payloads.items():
        with (output / name).open("x") as handle: handle.write(value)
    with (output / "manifest.json").open("x") as handle: json.dump(manifest, handle, indent=2); handle.write("\n")
    return manifest

if __name__ == "__main__":
    print(json.dumps(prepare()["counts"]))
