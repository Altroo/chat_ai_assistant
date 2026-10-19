"""Prepare a bounded TRAIN-only entity-copying supplement; never train a model."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator
import prepare_facturation_role_variants_v1 as prior

VERSION = "facturation-entity-spans-v1-en-fr"
SOURCE_SHA256 = {
    "train.jsonl": "d15058b975111808ed14166af92921bdfd14adeb63069a8bf0fd8b281af2c276",
    "valid.jsonl": "8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487",
}
ROLES = {
    "search_clients": {"query": "person"},
    "search_articles": {"reference": "reference", "query": "article_term",
                        "product_name": "article_term"},
    "search_payments": {"client_name": "person", "product_name": "article_term",
                        "query": "payment_query"},
}
FIRST = ("Ava", "Valentine", "Éloi", "Lina")
LAST = ("Roy", "Chanterelle", "d'Aubrac", "Mont-Argent", "Belrive", "Clairval")
HEAD = ("Nacre", "Boréal", "Éclat", "Rive")
TAIL = ("Atelier", "d'Argent", "Ligne 48", "Mont-Fleur", "Clair", "Collection C9")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def function(row):
    messages = row.get("messages", [])
    if (row.get("application") != "facturation" or len(messages) < 3
            or messages[-2].get("role") != "user"
            or messages[-1].get("role") != "assistant"
            or len(messages[-1].get("tool_calls", [])) != 1):
        raise ValueError("One supervised Facturation action is required")
    value = messages[-1]["tool_calls"][0]["function"]
    if value["name"] not in ROLES or not isinstance(value["arguments"], dict):
        raise ValueError("Only declared native search tools are supported")
    return value


def replacement(role, parent, variant):
    person = FIRST[variant] + " " + LAST[(parent + variant) % len(LAST)]
    references = (f"A{parent + 20}", f"RF-{parent + 70}-K2",
                  f"ART/{parent + 300}.Q", f"REF-B{parent + 500}-09/Z")
    if role == "person":
        return person
    if role == "reference":
        return references[variant]
    if role == "article_term":
        return HEAD[variant] + " " + TAIL[(parent + variant) % len(TAIL)]
    if role == "payment_query":
        return person if variant % 2 == 0 else references[variant]
    raise ValueError("Unknown literal role")


def variant(row, fields, language, parent, index):
    target = function(row)
    name, arguments = target["name"], target["arguments"]
    if language not in ("en", "fr") or row.get("language") not in (None, language):
        raise ValueError("Verified English or French parent required")
    expected = {key for key in arguments if key in ROLES[name]}
    if set(fields) != expected or not fields or len(fields) != len(set(fields)):
        raise ValueError("Every supported parent literal must be declared once")
    prefix, text = prior.current_request(row["messages"][-2]["content"])
    other = prior.encoded(row["messages"][:-2]) + prefix
    values = [arguments[field] for field in fields]
    if (any(not isinstance(v, str)
            or not re.fullmatch(r"SYN-[\w-]+(?: [\w'-]+)*", v) for v in values)
            or len(set(values)) != len(values)):
        raise ValueError("Distinct approved synthetic source literals required")
    if any(v in other for v in values):
        raise ValueError("History or trusted-context-linked literals cannot change")
    if any(v in prior.encoded(value) for v in values
           for key, value in arguments.items() if key not in fields):
        raise ValueError("A literal is linked to an unchanged target argument")
    if len(values) > 1 and prior.has_untyped_role_conjunction(text, values):
        raise ValueError("Ambiguous source role assignment")
    lowered = text.casefold()
    if name == "search_clients" and re.search(
            r"\b(code|codes|company|société|entreprise)\b", lowered):
        raise ValueError("Personal-name variants cannot replace company/code intents")
    if name == "search_payments" and "query" in fields and not re.search(
            r"invoice numbers? or customer names?|numéros? de facture ou (?:les )?noms? de client",
            lowered):
        raise ValueError("Payment query must explicitly search invoice/customer fields")
    if name == "search_articles" and any(f != "reference" for f in fields):
        if not re.search(r"designation|désignation", lowered):
            raise ValueError("Broad article term intent must be explicit")
    offered = {t["function"]["name"]: t["function"]["parameters"] for t in row["tools"]}
    if name not in offered:
        raise ValueError("Original target tool is not offered")
    validator = Draft202012Validator(offered[name])
    validator.validate(arguments)
    assigned = {field: replacement(ROLES[name][field], parent, index) for field in fields}
    if len(set(assigned.values())) != len(assigned):
        raise ValueError("Replacement literals must remain distinct")
    if any(v in other or v in text for v in assigned.values()):
        raise ValueError("Replacement collides with existing context")
    replacements = {arguments[field]: assigned[field] for field in fields}
    changed = prior.substitute(text, replacements)
    if prior.substitute(changed, {v: k for k, v in replacements.items()}) != text:
        raise ValueError("Nonliteral text changed")
    result = deepcopy(row)
    result["messages"][-2]["content"] = prefix + changed
    result["messages"][-1]["tool_calls"][0]["function"]["arguments"].update(assigned)
    result["language"] = language
    validator.validate(result["messages"][-1]["tool_calls"][0]["function"]["arguments"])
    result["augmentation"] = {
        "version": VERSION, "source_parent": parent, "variant": index,
        "fields": list(fields), "source_input_sha256": digest(prior.input_key(row).encode()),
        "source_target_sha256": digest(prior.encoded(target).encode()),
    }
    return result


def prepare(source, plan_path, output):
    source, plan_path, output = map(lambda p: Path(p).resolve(),
                                   (source, plan_path, output))
    if output.exists() or source == output or source in output.parents:
        raise ValueError("A new isolated output directory is required")
    raw = {name: (source / name).read_bytes() for name in SOURCE_SHA256}
    if any(digest(value) != SOURCE_SHA256[name] for name, value in raw.items()):
        raise ValueError("Immutable TRAIN/development source changed")
    train_lines = raw["train.jsonl"].splitlines()
    train = [json.loads(line) for line in train_lines]
    development = [json.loads(line) for line in raw["valid.jsonl"].splitlines()]
    if len(train) != 3103 or len(development) != 275:
        raise ValueError("Unexpected source corpus")
    plan_raw = plan_path.read_bytes()
    plan = json.loads(plan_raw)
    if (plan["version"] != VERSION or plan["source_sha256"] != SOURCE_SHA256
            or plan["variants_per_parent"] != 4 or len(plan["parents"]) != 18):
        raise ValueError("Exact reviewed 18-parent/four-variant plan required")
    excluded_keys = {prior.canonical_input_key(r) for r in development}
    excluded_patterns = {prior.request_pattern(r) for r in development}
    existing = {prior.canonical_input_key(r) for r in train}
    parents_seen, generated, stats = set(), [], Counter()
    for parent, item in enumerate(plan["parents"]):
        if set(item) != {"line", "row_sha256", "tool", "fields", "language"}:
            raise ValueError("Unexpected parent metadata")
        line = item["line"]
        if type(line) is not int or not 1 <= line <= len(train):
            raise ValueError("Invalid one-based TRAIN row")
        row = train[line - 1]
        if digest(train_lines[line - 1]) != item["row_sha256"]:
            raise ValueError("Parent row changed")
        if function(row)["name"] != item["tool"]:
            raise ValueError("Parent operation changed")
        key = prior.canonical_input_key(row)
        if (key in parents_seen or key in excluded_keys
                or prior.request_pattern(row) in excluded_patterns):
            raise ValueError("Duplicate or development-linked parent")
        parents_seen.add(key)
        stats[(item["tool"], item["language"])] += 1
        for index in range(4):
            value = variant(row, item["fields"], item["language"], parent, index)
            key = prior.canonical_input_key(value)
            if (key in existing or key in excluded_keys
                    or prior.request_pattern(value) in excluded_patterns):
                raise ValueError("Generated input duplicate or development overlap")
            existing.add(key)
            value["augmentation"]["source_train_line"] = line
            generated.append(value)
    if stats != Counter({(tool, lang): 3 for tool in ROLES for lang in ("en", "fr")}):
        raise ValueError("Three distinct parents per tool and language required")
    payload = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n"
                      for r in generated).encode()
    manifest = {
        "version": VERSION, "status": "PREPARED SUPPLEMENT ONLY; NOT TRAINED OR ACCEPTED",
        "source_sha256": SOURCE_SHA256, "plan_sha256": digest(plan_raw),
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "parent_helper_sha256": digest(Path(prior.__file__).read_bytes()),
        "application": "facturation", "languages": ["en", "fr"], "count": len(generated),
        "parents": len(parents_seen), "by_tool": dict(Counter(function(r)["name"] for r in generated)),
        "by_language": dict(Counter(r["language"] for r in generated)),
        "files": {"contrasts.jsonl": digest(payload)}, "starting_checkpoint": 600,
        "training_executed": False, "model_accepted": False, "production_activation": False,
        "limitations": ["Literal diversity only; existing request wordings are retained.",
                        "This small supplement does not establish model generalization.",
                        "Development inputs/templates excluded; held-out prompts never opened.",
                        "Native schemas, argument keys, filters and trusted context retained.",
                        "Client variants cover personal names, not new company/code patterns."],
    }
    if len(generated) != 72:
        raise ValueError("Exactly 72 distinct supplement rows required")
    output.mkdir(parents=True, exist_ok=False)
    (output / "contrasts.jsonl").write_bytes(payload)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "plan", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.plan, args.output), indent=2))
