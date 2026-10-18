"""Prepare natural EN/FR compound stock questions from reviewed TRAIN labels.

Only current-request wording changes. No development label, model, business
database or inference service is used.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import date
import json
from pathlib import Path

from jsonschema import Draft202012Validator

import prepare_facturation_stock_profiles_v1 as profiles

SOURCE_MANIFEST_SHA256 = "5f539a4902e0e1163be53b412029f90706607638188fe9a097921ee1c73da210"
SOURCE_CONTRAST_SHA256 = "14378b89b5ce62a310fb67a77592f295744b722e83427fe6bd82a1df0fa3f6f8"
VERSION = "facturation-natural-stock-v1-en-fr"
MONTHS = {
    "en": ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"),
    "fr": ("janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"),
}
NOUNS = {
    "stock_balance": ("stock balances", "fiches de stock", "updated", "mises à jour"),
    "stock_movement": ("stock movements", "mouvements de stock", "created", "créés"),
    "stock_receipt": ("stock receipts", "réceptions de stock", "created", "créées"),
    "stock_inventory": ("stock inventories", "inventaires", "created", "créés"),
}


def written(value, language):
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Canonical ISO dates are required")
    return f"{parsed.day} {MONTHS[language][parsed.month - 1]} {parsed.year}"


def questions(row):
    if row.get("application") != "facturation" or row.get("language") not in ("en", "fr"):
        return {}
    function = row["messages"][-1]["tool_calls"][0]["function"]
    args = function["arguments"]
    required = {"resource", "product_name", "location_name", "limit"}
    allowed = required | {"date_from", "date_to"}
    if (function["name"] != "search_operations" or args.get("resource") not in NOUNS
            or not required <= set(args) or not set(args) <= allowed
            or not ({"date_from", "date_to"} & set(args))):
        return {}
    language = row["language"]
    if (any(not isinstance(args[k], str) or not args[k].startswith("SYN-")
            for k in ("product_name", "location_name"))
            or args["product_name"] == args["location_name"]):
        return {}
    Draft202012Validator(profiles.operation_schema(row["tools"])).validate(args)
    if args.get("date_from") and args.get("date_to") and args["date_from"] > args["date_to"]:
        raise ValueError("Inverted reporting interval")
    lower = written(args["date_from"], language) if "date_from" in args else None
    upper = written(args["date_to"], language) if "date_to" in args else None
    product, location, limit = args["product_name"], args["location_name"], args["limit"]
    en_noun, fr_noun, en_event, fr_event = NOUNS[args["resource"]]
    if language == "en":
        dates = (f"between {lower} and {upper}, inclusive" if lower and upper
                 else f"on or after {lower}" if lower else f"on or before {upper}")
        return {
            "product_first": f"Look up {en_noun} {en_event} {dates}. "
                             f"Limit the matches to {product} in {location}, and show no more than {limit}.",
            "location_first": f"In {location}, show {en_noun} of {product} {en_event} {dates}. "
                              f"Return at most {limit} results.",
        }
    dates = (f"entre le {lower} et le {upper} inclus" if lower and upper
             else f"à partir du {lower} inclus" if lower else f"au plus tard le {upper} inclus")
    return {
        "product_first": f"Je cherche les {fr_noun} {fr_event} {dates}, "
                         f"concernant {product} dans {location}. Garde seulement {limit} résultats maximum.",
        "location_first": f"À {location}, affiche les {fr_noun} de {product}, {fr_event} {dates}. "
                          f"Pas plus de {limit} résultats.",
    }


def prepare(source, development, output):
    source, development, output = Path(source).resolve(), Path(development).resolve(), Path(output).resolve()
    if output.exists() or any(root == output or root in output.parents
                              for root in (source, development.parent)):
        raise ValueError("Output must be new and outside the immutable inputs")
    helper = profiles.prior
    manifest_raw, raw, valid_raw = ((source / "manifest.json").read_bytes(),
                                   (source / "contrasts.jsonl").read_bytes(), development.read_bytes())
    if (helper.digest(manifest_raw) != SOURCE_MANIFEST_SHA256
            or helper.digest(raw) != SOURCE_CONTRAST_SHA256
            or helper.digest(valid_raw) != helper.SOURCE_SHA256["valid.jsonl"]):
        raise ValueError("Reviewed source or frozen development inputs changed")
    previous = json.loads(manifest_raw)
    if (helper.digest(Path(profiles.__file__).read_bytes()) != previous["generator_sha256"]
            or helper.digest(Path(helper.__file__).read_bytes()) != previous["helper_sha256"]):
        raise ValueError("Reviewed source preparers changed")
    rows = [json.loads(line) for line in raw.splitlines()]
    development_rows = [json.loads(line) for line in valid_raw.splitlines()]
    excluded = {helper.request_pattern(row) for row in development_rows}
    targets = {helper.canonical_input_key(row): helper.encoded(
        row["messages"][-1]["tool_calls"][0]["function"]) for row in rows}
    generated, skipped = [], Counter()
    for index, row in enumerate(rows):
        for kind, text in questions(row).items():
            variant = deepcopy(row)
            prefix, _ = helper.current_request(row["messages"][-2]["content"])
            # Remove only the four known single neutral greeting wrappers.
            # Other genuine history is retained exactly.
            if helper.canonical_input_key(row) != helper.input_key(row):
                prefix = ""
            variant["messages"][-2]["content"] = prefix + text
            key = helper.canonical_input_key(variant)
            target = helper.encoded(variant["messages"][-1]["tool_calls"][0]["function"])
            if helper.request_pattern(variant) in excluded:
                skipped["development_request_pattern"] += 1
                continue
            if key in targets:
                if targets[key] != target:
                    raise ValueError("A generated input has conflicting targets")
                skipped["duplicate_input"] += 1
                continue
            targets[key] = target
            variant["augmentation"] = {
                "version": VERSION, "kind": kind, "source_profile_row_index": index,
                "source_original_train_row_index": row["augmentation"]["source_row_index"],
                "source_profile_input_sha256": helper.digest(helper.input_key(row).encode()),
                "source_target_sha256": helper.digest(target.encode()),
            }
            generated.append(variant)
    if not generated:
        raise ValueError("No safe natural compound questions prepared")
    data = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                   for row in generated).encode()
    manifest = {
        "version": VERSION, "status": "PREPARED ONLY; not trained or model-tested",
        "applications": ["facturation"], "languages": ["en", "fr"], "count": len(generated),
        "by_language": dict(Counter(row["language"] for row in generated)),
        "by_kind": dict(Counter(row["augmentation"]["kind"] for row in generated)),
        "source_profile_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "source_profile_contrast_sha256": SOURCE_CONTRAST_SHA256,
        "frozen_development_input_sha256": helper.digest(valid_raw),
        "files": {"contrasts.jsonl": helper.digest(data)}, "exclusions": dict(skipped),
        "generator_sha256": helper.digest(Path(__file__).read_bytes()),
        "training_executed": False, "model_accepted": False, "production_activation": False,
        "limitations": [
            "Two authored wording families do not represent all natural language or predict accuracy.",
            "Targets come exclusively from reviewed TRAIN profile variants; development inputs supply exclusions only.",
            "Only existing current-request wording and recognized neutral history change; schemas, trusted context and targets remain unchanged.",
            "Semantic review, server preflight and actual candidate admission remain required before training.",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "contrasts.jsonl").write_bytes(data)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--development-inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.development_inputs, args.output), indent=2))


if __name__ == "__main__":
    main()
