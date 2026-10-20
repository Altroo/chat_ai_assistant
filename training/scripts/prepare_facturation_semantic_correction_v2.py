"""Prepare a bounded corrective TRAIN pilot without loading any model.

Targets come from existing permission-filtered TRAIN contracts. Development
inputs are used only to exclude duplicates; their targets are never consulted.
"""
import argparse
import calendar
from collections import Counter
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path

VERSION = "facturation-semantic-correction-v2-en-fr"
SOURCE_TRAIN_SHA = "05e792a632ba37cdbb71845e57c0444f4feb4c94851addc5ec84a9674da0cb0d"
SOURCE_VALID_SHA = "8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487"
QUOTAS = {"facturation": 32, "management_projet": 16, "design_workflow": 16}
FAMILIES = {"full_literal": 16, "optional_filters": 24, "month_endings": 24}
CALENDAR_SHA256 = "6ee2c0f63ef33c0ba8b8f1ea29fbcd5d6f1e88e4273dc40ece33dab75619aeb9"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_helper(name, expected=None):
    path = Path(__file__).with_name(name + ".py")
    if expected is not None and sha(path.read_bytes()) != expected:
        raise ValueError("Reviewed helper changed")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def helper():
    return load_helper("prepare_facturation_semantic_contrasts_v1",
                       "3d7f2eee56c328593d8ccfbd01c4aea1e637da0b6a4d13079ee48d5489d27d43")


def calendar_context(context):
    """Use the actual shared context implementation, without extending its API."""
    path = Path(__file__).resolve().parents[2] / "src/chat_ai_assistant/calendar_context.py"
    if sha(path.read_bytes()) != CALENDAR_SHA256:
        raise ValueError("Reviewed calendar implementation changed")
    spec = importlib.util.spec_from_file_location("correction_calendar_context", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.with_calendar_context(context)


def generate(rows):
    old = helper()
    contrasts = rows[384:]
    if len(rows) != 500 or len(contrasts) != 116:
        raise ValueError("Complete reviewed 500-row source required")
    families = {}
    for row in contrasts:
        families.setdefault(row["augmentation"]["family"], []).append(row)
    result = []

    def add(parent, text, args, language, family, factors):
        index = next(i for i, r in enumerate(rows, 1) if r is parent)
        row = old.make(parent, index, family, language, text, args, factors=factors)
        row["augmentation"]["version"] = VERSION
        result.append(row)
        return row

    literals = [
        "SYN-Review ready for verification 829",
        "SYN-Final checks completed; await signature 830",
        "SYN-Dossier contrôlé, document prêt pour validation 831.",
        'SYN-Use the label "Approved" after review 832',
    ]
    for resource in ("proforma", "quote"):
        parent = next(r for r in families["verbatim_update_text"]
                      if old.target(r)["arguments"]["resource"] == resource)
        original = old.target(parent)["arguments"]
        for value in literals:
            for language in ("en", "fr"):
                args = deepcopy(original)
                args["changes"]["remarque"] = value
                label = ({"proforma": "pro forma invoice", "quote": "quote"} if language == "en"
                         else {"proforma": "facture pro forma", "quote": "devis"})[resource]
                literal = json.dumps(value, ensure_ascii=False)
                text = (f'On {label} ID {args["identifier"]}, replace the entire Remark with {literal} '
                        f'and set Due date to {args["changes"]["date_echeance"]}.'
                        if language == "en" else
                        f'Pour le document {label} ID {args["identifier"]}, remplace toute la Remarque '
                        f'par {literal} et fixe la Date d’échéance au {args["changes"]["date_echeance"]}.')
                add(parent, text, args, language, "full_literal",
                    {"resource": resource, "literal": value})

    parent = next(r for r in families["unpaid_with_other_filters"]
                  if "date_to" not in old.target(r)["arguments"]
                  and "unpaid" not in old.target(r)["arguments"])
    for variant, anchor in enumerate(("2033-03-07", "2035-08-12")):
        end = (date.fromisoformat(anchor) + timedelta(days=6)).isoformat()
        client, product = f"SYN-Optional-Client-{variant}", f"SYN-Optional-Product-{variant}"
        for mode in ("lower", "upper", "closed"):
            dates = {"lower": {"date_from": anchor}, "upper": {"date_to": end},
                     "closed": {"date_from": anchor, "date_to": end}}[mode]
            for unpaid in (False, True):
                for language in ("en", "fr"):
                    args = {"client_name": client, "product_name": product,
                            "limit": 1 if variant == 0 else 4, **dates}
                    if unpaid:
                        args["unpaid"] = True
                    when = ({
                        "lower": f"on or after {anchor}; leave the end date unrestricted",
                        "upper": f"on or before {end}; leave the start date unrestricted",
                        "closed": f"between {anchor} and {end}, including both days",
                    } if language == "en" else {
                        "lower": f"à partir du {anchor} inclus, sans limiter la date de fin",
                        "upper": f"jusqu’au {end} inclus, sans limiter la date de début",
                        "closed": f"du {anchor} au {end}, les deux jours inclus",
                    })[mode]
                    status = (" with an outstanding balance" if language == "en"
                              else " dont le solde est impayé") if unpaid else ""
                    text = (f'Search invoices{status} for customer {client}, with product {product}, '
                            f'dated {when}. Return at most {args["limit"]} matches.'
                            if language == "en" else
                            f'Recherche les factures{status} du client {client} avec le produit {product}, '
                            f'datées {when}. Renvoie au maximum {args["limit"]} résultats.')
                    add(parent, text, args, language, "optional_filters",
                        {"mode": mode, "unpaid": unpaid, "variant": variant})

    parent = families["relative_quote_month"][0]
    for today in ("2028-02-14", "2031-02-11", "2030-11-18", "2031-01-21"):
        for mode in ("current_full", "previous_full", "month_to_date"):
            start, end = old.month_bounds(today, previous=mode == "previous_full")
            if mode == "month_to_date":
                end = today
            for language in ("en", "fr"):
                phrase = ({
                    "current_full": "the whole current calendar month, including its final day",
                    "previous_full": "the whole previous calendar month, including its final day",
                    "month_to_date": "the period from the first day of this month through today, inclusive",
                } if language == "en" else {
                    "current_full": "tout le mois calendaire en cours, jusqu’à son dernier jour inclus",
                    "previous_full": "tout le mois calendaire précédent, jusqu’à son dernier jour inclus",
                    "month_to_date": "la période allant du premier jour de ce mois jusqu’à aujourd’hui inclus",
                })[mode]
                text = (f"Show no more than 3 quotes dated within {phrase}."
                        if language == "en" else f"Affiche au plus 3 devis datés pendant {phrase}.")
                row = add(parent, text, {"limit": 3, "date_from": start, "date_to": end},
                          language, "month_endings", {"today": today, "mode": mode})
                system = row["messages"][0]["content"]
                prefix = system.split("Trusted context: ", 1)[0]
                context = old.trusted_context(row)
                context["today"] = today
                context = calendar_context(context)
                row["messages"][0]["content"] = prefix + "Trusted context: " + json.dumps(
                    context, ensure_ascii=False)
                old.target(row)
    if Counter(r["augmentation"]["family"] for r in result) != Counter(FAMILIES):
        raise ValueError("Corrective inventory is incomplete")
    if Counter(r["language"] for r in result) != Counter(en=32, fr=32):
        raise ValueError("Corrective language coverage changed")
    return result


def features(row):
    target = row["messages"][-1].get("tool_calls", [])
    name = target[0]["function"]["name"] if target else "text"
    result = {("tool", name), ("capability", row.get("capability_profile", "")),
              ("category", row.get("curriculum_category", ""))}
    meta = row.get("augmentation", {})
    family = meta.get("family")
    if family:
        result.add(("semantic_family", family))
        if family == "users_collection_versus_detail":
            result.add(("semantic_pair", family, str(meta["factors"]["collection"])))
        if family == "ambiguous_previous_result_selection":
            result.add(("semantic_pair", family, str(meta["factors"]["explicit"])))
        if family == "unsupported_current_language":
            result.add(("semantic_pair", family, row["language"]))
        if family == "date_boundaries" and meta["factors"]["mode"] in (
                "upper_inclusive", "upper_exclusive"):
            result.add(("semantic_pair", family, meta["factors"]["mode"]))
    if target:
        args = target[0]["function"]["arguments"]
        if name == "search_articles":
            for key in ("query", "product_name"):
                if key in args:
                    result.add(("critical_shape", name, key))
        if name == "search_payments" and set(args) == {"invoice_number", "limit"}:
            result.add(("critical_shape", name, "invoice_number_with_limit"))
        result.add(("argument_shape", name, tuple(sorted(args))))
        result.update(("argument_key", name, key) for key in args)
        schema = next(t["function"]["parameters"] for t in row["tools"]
                      if t["function"]["name"] == name)
        for key, value in args.items():
            if value in schema.get("properties", {}).get(key, {}).get("enum", []):
                result.add(("enum", name, key, encoded(value)))
            if isinstance(value, dict):
                result.add(("nested_shape", name, key, tuple(sorted(value))))
    return result


def retain(rows):
    """Cover target tools, then diversify argument shapes, enums and access tags."""
    selected = []
    for app, quota in QUOTAS.items():
        candidates = sorted((r for r in rows if r["application"] == app),
                            key=lambda r: sha(encoded(r).encode()))
        mandatory_kinds = {"tool", "semantic_family", "semantic_pair", "critical_shape"} if app == "facturation" else {"tool"}
        required = {value for r in candidates for value in features(r)
                    if value[0] in mandatory_kinds}
        chosen, covered = [], set()
        while len(chosen) < quota:
            if not candidates:
                raise ValueError("Insufficient retention inventory")
            row = max(candidates, key=lambda r: (
                1000 * len((features(r) - covered) & required)
                + len(features(r) - covered)))
            chosen.append(row)
            candidates.remove(row)
            covered |= features(row)
        if not required <= covered:
            raise ValueError("Mandatory tools and semantic contrast pairs must be retained")
        selected.extend(deepcopy(chosen))
    return selected



def assemble(retained, generated, source_raw):
    """Keep replay prompt and argument order byte-identical to its source."""
    original = {}
    for line in source_raw.splitlines():
        key = encoded(json.loads(line))
        if key in original:
            raise ValueError("Duplicate source row identity")
        original[key] = line
    replay = [original[encoded(row)] for row in retained]
    additions = [json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode()
                 for row in generated]
    return b"\n".join(replay + additions) + b"\n", b"\n".join(additions) + b"\n"

def prepare(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() or not output.parent.is_dir() or source == output or source in output.parents:
        raise ValueError("A new isolated output directory is required")
    payloads = {name: (source / name).read_bytes() for name in ("train.jsonl", "valid.jsonl")}
    if sha(payloads["train.jsonl"]) != SOURCE_TRAIN_SHA or sha(payloads["valid.jsonl"]) != SOURCE_VALID_SHA:
        raise ValueError("Reviewed source data changed")
    rows = [json.loads(line) for line in payloads["train.jsonl"].splitlines()]
    old = helper()
    generated, retained = generate(rows), retain(rows)
    development = [json.loads(line) for line in payloads["valid.jsonl"].splitlines()]
    old.validate_exclusions(rows, generated, development)
    combined = retained + generated
    for row in combined:
        old.target(row)
    if len(combined) != 128:
        raise ValueError("Exactly 128 pilot rows required")
    train, additions = assemble(retained, generated, payloads["train.jsonl"])
    files = {"train.jsonl": train, "valid.jsonl": payloads["valid.jsonl"],
             "contrasts.jsonl": additions}
    source_lines = {encoded(r): line for line, r in enumerate(rows, 1)}
    manifest = {
        "version": VERSION, "status": "PREPARED ONLY; NOT TRAINED OR ACCEPTED",
        "applications": list(QUOTAS), "languages": ["en", "fr"],
        "count": 128, "new_contrasts": FAMILIES, "retention_quotas": QUOTAS,
        "retained_raw_lines_byte_identical": True,
        "all_eight_semantic_families_retained": True,
        "generated_tool_and_message_key_order_preserved": True,
        "by_application": dict(Counter(r["application"] for r in combined)),
        "retained_source_lines": [source_lines[encoded(r)] for r in retained],
        "retained_target_tools": {app: sorted({v[1] for r in retained if r["application"] == app
                                             for v in features(r) if v[0] == "tool"})
                                  for app in QUOTAS},
        "retention_feature_coverage": {
            app: {
                "available": len(set().union(*(features(r) for r in rows if r["application"] == app))),
                "selected": len(set().union(*(features(r) for r in retained if r["application"] == app))),
            } for app in QUOTAS
        },
        "source_sha256": {"train.jsonl": SOURCE_TRAIN_SHA, "valid.jsonl": SOURCE_VALID_SHA},
        "files": {name: sha(raw) for name, raw in files.items()},
        "generator_sha256": sha(Path(__file__).read_bytes()),
        "calendar_source_sha256": sha((Path(__file__).resolve().parents[2] /
                                       "src/chat_ai_assistant/calendar_context.py").read_bytes()),
        "limitations": ["A bounded diagnostic pilot; retention coverage is partial.",
                       "Dataset checks are not functional model accuracy.",
                       "No learning rate or number of updates is proven sufficient.",
                       "Frozen evaluation labels and scoring remain unchanged."],
        "training_executed": False, "model_accepted": False, "production_activation": False,
    }
    output.mkdir(mode=0o700)
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), indent=2))
