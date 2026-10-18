"""Prepare training-only name-role variants from the reviewed Facturation corpus.

Questions and targets change together. This loads no model, executes no business
operation and does not authorize training, acceptance or deployment.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from jsonschema import Draft202012Validator

VERSION = "facturation-role-variants-v1-en-fr"
SOURCE_SHA256 = {
    "manifest.json": "38b3d6d148940b2cfa7e44a9f59550fc4847ebb4e709b6c372b682f96c5b696f",
    "train.jsonl": "c6fb838c8714b78ae6f0b17dab33d1ca9fa48dc086b4f1ca56a8aaf9e85e88ba",
    "valid.jsonl": "8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487",
}
ROLE_FIELDS = ("client_name", "product_name", "location_name", "supplier_name")
SEARCH_TOOLS = {"search_invoices", "search_quotes", "search_documents", "search_operations"}
NEUTRAL_HISTORY = {"Hello", "Bonjour", "Hello, thanks for your help.",
                   "Bonjour, merci pour votre aide."}
OPAQUE_NAMES = ("SYN-CF-Alto", "SYN-CF-Brume", "SYN-CF-Cedre", "SYN-CF-Dune",
                "SYN-CF-Eclat", "SYN-CF-Fauve", "SYN-CF-Galet", "SYN-CF-Halo")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def input_key(row):
    return encoded({"messages": row["messages"][:-1], "tools": row["tools"]})


def current_request(content):
    prefix = "Earlier user messages (background only): "
    if not isinstance(content, str):
        raise ValueError("A text user request is required")
    if not content.startswith(prefix):
        return "", content
    history, end = json.JSONDecoder().raw_decode(content[len(prefix):])
    tail = content[len(prefix) + end:]
    boundary = "\nCurrent request: "
    if (not isinstance(history, list) or not history
            or any(not isinstance(value, str) for value in history)
            or not tail.startswith(boundary)):
        raise ValueError("Invalid training history wrapper")
    offset = len(prefix) + end + len(boundary)
    return content[:offset], content[offset:]


def canonical_input_key(row):
    """Ignore only a single known neutral greeting, retaining real history."""
    messages = deepcopy(row["messages"][:-1])
    content = messages[-1]["content"]
    prefix, text = current_request(content)
    if prefix:
        history, _ = json.JSONDecoder().raw_decode(
            content[len("Earlier user messages (background only): "):])
        if len(history) == 1 and history[0] in NEUTRAL_HISTORY:
            messages[-1]["content"] = text
    return encoded({"messages": messages, "tools": row["tools"]})


def has_untyped_role_conjunction(text, values):
    """Fail closed when separate literals are joined without a role cue."""
    pattern = re.compile(r"(?<![\w-])(?:" + "|".join(
        re.escape(value) for value in sorted(values, key=lambda v: (-len(v), v))
    ) + r")(?![\w-])")
    mentions = list(pattern.finditer(text))
    return any(
        left.group() != right.group()
        and re.fullmatch(r"(?:\s|[,;&+()/:]|\b(?:and|et|or|ou)\b)+",
                         text[left.end():right.start()], flags=re.IGNORECASE)
        for left, right in zip(mentions, mentions[1:])
    )


def request_pattern(row):
    """Reject value-only duplicate templates against development INPUTS."""
    _, text = current_request(row["messages"][-2]["content"])
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"\bsyn-[\w-]+\b", "<synthetic>", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "<date>", text)
    text = re.sub(r"\b\d+\b", "<number>", text)
    return " ".join(text.split())


def substitute(text, replacements):
    pattern = re.compile(r"(?<![\w-])(?:" + "|".join(
        re.escape(value) for value in sorted(replacements, key=lambda v: (-len(v), v))
    ) + r")(?![\w-])")
    found = {match.group() for match in pattern.finditer(text)}
    if found != set(replacements):
        raise ValueError("Every literal must occur as a complete identifier")
    return pattern.sub(lambda match: replacements[match.group()], text)


def role_variants(row, source_index):
    if row.get("application") != "facturation":
        return []
    messages = row.get("messages", [])
    if (len(messages) < 3 or messages[-2].get("role") != "user"
            or messages[-1].get("role") != "assistant"
            or len(messages[-1].get("tool_calls", [])) != 1):
        raise ValueError("Invalid supervised message boundary")
    function = messages[-1]["tool_calls"][0]["function"]
    if function["name"] not in SEARCH_TOOLS or not isinstance(function["arguments"], dict):
        return []
    arguments = function["arguments"]
    fields = [name for name in ROLE_FIELDS if name in arguments]
    values = [arguments[name] for name in fields]
    if (len(fields) < 2
            or any(not isinstance(value, str) or not re.fullmatch(r"SYN-[\w-]+", value)
                   for value in values) or len(set(values)) != len(values)):
        return []
    prefix, text = current_request(messages[-2]["content"])
    other = encoded(messages[:-2]) + prefix
    if any(value in other or value not in text for value in values):
        return []
    if has_untyped_role_conjunction(text, values):
        return []
    offered = {tool["function"]["name"]: tool["function"]["parameters"] for tool in row["tools"]}
    if function["name"] not in offered:
        raise ValueError("Original target tool must be offered")
    validator = Draft202012Validator(offered[function["name"]])
    validator.validate(arguments)
    offset = int(digest(canonical_input_key(row).encode())[:8], 16) % len(OPAQUE_NAMES)
    opaque = [OPAQUE_NAMES[(offset + i) % len(OPAQUE_NAMES)] for i in range(len(fields))]
    alternatives = [("rotate_roles", values[1:] + values[:1])]
    if not any(value in text for value in opaque):
        alternatives.append(("opaque_roles", opaque))
    result = []
    for kind, assigned in alternatives:
        replacements = dict(zip(values, assigned))
        variant = deepcopy(row)
        variant["messages"][-2]["content"] = prefix + substitute(text, replacements)
        updated = variant["messages"][-1]["tool_calls"][0]["function"]["arguments"]
        for field, value in zip(fields, assigned):
            updated[field] = value
        validator.validate(updated)
        variant["augmentation"] = {
            "version": VERSION, "kind": kind, "source_row_index": source_index,
            "source_input_sha256": digest(input_key(row).encode()),
            "source_target_sha256": digest(encoded(function).encode()), "fields": fields,
        }
        result.append(variant)
    return result


def prepare(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() or source == output or source in output.parents:
        raise ValueError("Output must be new and outside the immutable source")
    payloads = {name: (source / name).read_bytes() for name in SOURCE_SHA256}
    if any(digest(raw) != SOURCE_SHA256[name] for name, raw in payloads.items()):
        raise ValueError("Reviewed source corpus changed")
    original = json.loads(payloads["manifest.json"])
    if original["version"] != "facturation-replay-v3-en-fr":
        raise ValueError("Reviewed source version required")
    train = [json.loads(line) for line in payloads["train.jsonl"].splitlines()]
    if len(train) != 2975:
        raise ValueError("All reviewed training rows are required")
    # Development data supplies exclusion keys only. Its expected actions never
    # supply a generated label; no acceptance or fresh-control file is opened.
    development = [json.loads(line) for line in payloads["valid.jsonl"].splitlines()]
    excluded_inputs = {canonical_input_key(row) for row in development}
    excluded_patterns = {request_pattern(row) for row in development}
    targets = {}
    for row in train:
        key = canonical_input_key(row)
        target = encoded(row["messages"][-1]["tool_calls"][0]["function"])
        if key in targets and targets[key] != target:
            raise ValueError("Contradictory original training targets")
        targets[key] = target
    generated, excluded, parent_keys = [], Counter(), set()
    for index, row in enumerate(train):
        if row.get("application") != "facturation":
            continue
        if request_pattern(row) in excluded_patterns:
            excluded["development_template"] += 1
            continue
        variants = role_variants(row, index)
        if not variants:
            continue
        parent_key = canonical_input_key(row)
        if parent_key in parent_keys:
            excluded["neutral_parent_duplicate"] += 1
            continue
        parent_keys.add(parent_key)
        for variant in variants:
            key = canonical_input_key(variant)
            target = encoded(variant["messages"][-1]["tool_calls"][0]["function"])
            if key in excluded_inputs or request_pattern(variant) in excluded_patterns:
                excluded["development_input_or_template"] += 1
                continue
            if key in targets:
                if targets[key] != target:
                    raise ValueError("Generated input has contradictory targets")
                excluded["duplicate_input"] += 1
                continue
            targets[key] = target
            generated.append(variant)
    if not generated:
        raise ValueError("No nonduplicate training contrasts prepared")
    data = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                   for row in generated).encode()
    manifest = {
        "version": VERSION, "status": "PREPARED CONTRASTS ONLY; no training or accuracy claim",
        "source_files_sha256": SOURCE_SHA256, "generated_application": "facturation",
        "languages": ["en", "fr"], "count": len(generated),
        "by_kind": dict(Counter(row["augmentation"]["kind"] for row in generated)),
        "distinct_source_parents": len({row["augmentation"]["source_row_index"]
                                        for row in generated}),
        "input_canonicalization": "Only exact single known neutral greetings are ignored; "
                                  "generated history bytes are retained.",
        "exclusions": dict(excluded), "files": {"contrasts.jsonl": digest(data)},
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "training_executed": False, "model_accepted": False, "production_activation": False,
        "required_next_checks": ["semantic review", "server tokenizer/context preflight",
                                 "paired model diagnostic", "reviewed training admission"],
        "limitations": ["Existing synthetic training paraphrases are retained.",
                       "Input and literal-normalized template checks cover development inputs; "
                       "semantic independence from uninspected held-out cases is not established."],
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "contrasts.jsonl").write_bytes(data)
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
