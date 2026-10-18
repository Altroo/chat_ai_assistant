"""Prepare TRAIN-only stock searches under the existing native stock-only bundle.

This changes synthetic offered tools, never application permissions or requests.
It does not load a model or admit training, evaluation, or production activation.
"""
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

import prepare_facturation_role_variants_v1 as prior

VERSION = "facturation-stock-profiles-v1-en-fr"
STOCK = ("stock_balance", "stock_movement", "stock_receipt", "stock_inventory")
TOOL_NAMES = ["search_operations", "navigate", "knowledge", "clarify"]


def operation_schema(tools):
    return next(tool["function"]["parameters"] for tool in tools
                if tool["function"]["name"] == "search_operations")


def resources(schema):
    return tuple(branch["properties"]["resource"]["const"] for branch in schema["oneOf"])


def template(rows):
    candidates = [(i, row) for i, row in enumerate(rows)
                  if row.get("application") == "facturation"
                  and [tool["function"]["name"] for tool in row["tools"]] == TOOL_NAMES
                  and resources(operation_schema(row["tools"])) == STOCK]
    if not candidates:
        raise ValueError("The reviewed native stock-only TRAIN tool bundle is required")
    if len({prior.encoded(row["tools"]) for _, row in candidates}) != 1:
        raise ValueError("Conflicting stock-only tool bundles require separate review")
    return min(candidates, key=lambda item: prior.digest(
        prior.canonical_input_key(item[1]).encode()))


def profile_variant(row, tools, index):
    if row.get("application") != "facturation":
        return None
    messages = row["messages"]
    if (len(messages) != 3 or messages[-2]["role"] != "user"
            or messages[-1]["role"] != "assistant"
            or len(messages[-1].get("tool_calls", [])) != 1):
        raise ValueError("A single supervised current user turn is required")
    function = messages[-1]["tool_calls"][0]["function"]
    if (function["name"] != "search_operations"
            or function["arguments"].get("resource") not in STOCK):
        return None
    stock_schema, original = operation_schema(tools), operation_schema(row["tools"])
    if resources(stock_schema) != STOCK:
        raise ValueError("Only the reviewed four-stock-resource bundle is allowed")
    if resources(original) == STOCK:
        return None
    if (resources(original) != (*STOCK, "logistics_order")
            or prior.encoded(original["oneOf"][:4]) != prior.encoded(stock_schema["oneOf"])):
        raise ValueError("The original stock schemas must be retained exactly")
    context = json.loads(messages[0]["content"].split("Trusted context: ", 1)[1])
    if (context.get("current_invoice_id") is not None
            or context.get("current_resource") not in (None, *STOCK)
            or context.get("previous_result_type") not in (None, *STOCK)):
        return None
    Draft202012Validator(original).validate(function["arguments"])
    Draft202012Validator(stock_schema).validate(function["arguments"])
    variant = deepcopy(row)
    variant["tools"] = deepcopy(tools)
    variant["capability_profile"] = "stock_only"
    variant["augmentation"] = {
        "version": VERSION, "kind": "native_stock_only",
        "source_row_index": index,
        "source_input_sha256": prior.digest(prior.input_key(row).encode()),
        "source_target_sha256": prior.digest(prior.encoded(function).encode()),
    }
    return variant


def prepare(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() or source == output or source in output.parents:
        raise ValueError("Output must be new and outside the immutable source")
    payloads = {name: (source / name).read_bytes() for name in prior.SOURCE_SHA256}
    if any(prior.digest(raw) != prior.SOURCE_SHA256[name] for name, raw in payloads.items()):
        raise ValueError("Reviewed source corpus changed")
    train = [json.loads(line) for line in payloads["train.jsonl"].splitlines()]
    if len(train) != 2975:
        raise ValueError("All reviewed training rows are required")
    development = [json.loads(line) for line in payloads["valid.jsonl"].splitlines()]
    excluded_inputs = {prior.canonical_input_key(row) for row in development}
    excluded_patterns = {prior.request_pattern(row) for row in development}
    template_index, template_row = template(train)
    targets = {}
    for row in train:
        key = prior.canonical_input_key(row)
        target = prior.encoded(row["messages"][-1]["tool_calls"][0]["function"])
        if key in targets and targets[key] != target:
            raise ValueError("Conflicting original training targets")
        targets[key] = target
    generated, exclusions = [], Counter()
    for index, row in enumerate(train):
        if row.get("application") != "facturation":
            continue
        if prior.request_pattern(row) in excluded_patterns:
            exclusions["development_request_pattern"] += 1
            continue
        variant = profile_variant(row, template_row["tools"], index)
        if variant is None:
            continue
        key = prior.canonical_input_key(variant)
        target = prior.encoded(variant["messages"][-1]["tool_calls"][0]["function"])
        if key in excluded_inputs:
            exclusions["development_input"] += 1
            continue
        if key in targets:
            if targets[key] != target:
                raise ValueError("Profile transfer creates a conflicting target")
            exclusions["duplicate_input"] += 1
            continue
        targets[key] = target
        generated.append(variant)
    if not generated:
        raise ValueError("No safe nonduplicate profile contrasts prepared")
    raw = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                  for row in generated).encode()
    manifest = {
        "version": VERSION, "status": "PREPARED CONTRASTS ONLY; not trained or accepted",
        "applications": ["facturation"], "languages": ["en", "fr"],
        "source_files_sha256": prior.SOURCE_SHA256, "count": len(generated),
        "by_resource": dict(Counter(row["messages"][-1]["tool_calls"][0]["function"][
            "arguments"]["resource"] for row in generated)),
        "template_train_index": template_index,
        "template_input_sha256": prior.digest(prior.input_key(template_row).encode()),
        "template_tools_sha256": prior.digest(prior.encoded(template_row["tools"]).encode()),
        "exclusions": dict(exclusions), "files": {"contrasts.jsonl": prior.digest(raw)},
        "generator_sha256": prior.digest(Path(__file__).read_bytes()),
        "helper_sha256": prior.digest(Path(prior.__file__).read_bytes()),
        "training_executed": False, "model_accepted": False, "production_activation": False,
        "required_next_checks": ["semantic/native scope review", "server tokenizer/context preflight",
                                 "reviewed candidate admission from original selected checkpoint"],
        "limitations": [
            "Existing TRAIN questions and targets are retained exactly; only the whole offered tool bundle changes.",
            "Other tools and navigation schemas change together with the operation resource branches.",
            "This does not change real user permissions or demonstrate a model improvement.",
            "Development inputs supply exclusions only; no acceptance or fresh-control data is opened.",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "contrasts.jsonl").write_bytes(raw)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), indent=2))


if __name__ == "__main__":
    main()
