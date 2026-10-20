"""Prepare bounded TRAIN-only semantic contrasts; never load or train a model.

The approved 704-row replay is preserved byte for byte. Only verified TRAIN
parents supply labels and context. Development inputs supply exclusions only.
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
import re

from jsonschema import Draft202012Validator

VERSION = "facturation-semantic-contrasts-v1-en-fr"
SOURCE_SHA256 = {
    "manifest.json": "f321b2d2e0dd900f1b25f8e24cbcc709b4c5379a909de59741b07ab0e5fceff3",
    "train.jsonl": "2523aa3744e25ff24641dfd8c1bb67dbe051be4db74df7cc2b8d6331f08b0b58",
    "valid.jsonl": "8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487",
}
NATIVE_SHA256 = {
    "chat_ai/tools.py": "2ae44104618a4a0fe3586399ad28a3cb1b06a477ecd9812c80f7b1cbf5969c0a",
    "chat_ai/catalog.py": "f44a946bf2c148d8ecc341316930adccaccd75ff42c7801e137117408ef65f42",
    "chat_ai/navigation.py": "3aeb3a2d946fb01cfb816b8fd6137edb2e079abd0e0fa3c0f2dd76910aa5fb42",
    "chat_ai/operations.py": "06d87733927bf6eace463b8fbb2e235cca4acc45653909d8b64ab712203e74d0",
    "chat_ai/actions.py": "59ffe668c040bec092afd8715509924f225cdc525f90020b26484385fea68984",
}
HELPER_SHA256 = "2a654ed769d246e314803587b9cfa8e7177cf299dcb47b127b65be204557f84e"
PARENTS = (81, 86, 91, 97, 111, 169, 177, 178, 192, 194, 198, 250, 281, 330, 487)
EXPECTED_FAMILIES = {
    "date_boundaries": 22, "users_collection_versus_detail": 12,
    "logistics_entity_roles": 18, "verbatim_update_text": 12,
    "unpaid_with_other_filters": 24, "ambiguous_previous_result_selection": 8,
    "relative_quote_month": 12, "unsupported_current_language": 8,
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def helper():
    path = Path(__file__).with_name("prepare_facturation_role_variants_v1.py")
    if sha(path.read_bytes()) != HELPER_SHA256:
        raise ValueError("Reviewed canonicalization helper changed")
    spec = importlib.util.spec_from_file_location("semantic_contrast_prior", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def target(row):
    messages = row["messages"]
    if (len(messages) < 3 or messages[-2].get("role") != "user"
            or messages[-1].get("role") != "assistant"
            or len(messages[-1].get("tool_calls", [])) != 1):
        raise ValueError("Exactly one supervised action after the current user is required")
    result = messages[-1]["tool_calls"][0]["function"]
    if not isinstance(result.get("arguments"), dict):
        raise ValueError("Typed tool arguments required")
    tools = row["tools"]
    names = [tool["function"]["name"] for tool in tools]
    if len(names) != len(set(names)) or result["name"] not in names:
        raise ValueError("Target must be in the unique permission-filtered offered tools")
    schema = tools[names.index(result["name"])]["function"]["parameters"]
    Draft202012Validator(schema).validate(result["arguments"])
    if row.get("language") not in (None, "en", "fr"):
        raise ValueError("Only English and French rows are supported")
    return result


def trusted_context(row):
    text = row["messages"][0]["content"]
    if row["messages"][0]["role"] != "system" or text.count("Trusted context: ") != 1:
        raise ValueError("One verified trusted-context envelope is required")
    context = json.loads(text.split("Trusted context: ", 1)[1])
    if context["application"] != "facturation":
        raise ValueError("Facturation context required")
    return context


def make(parent, line, family, language, text, arguments, *, tool=None, factors=None):
    """Change only current request, target and explicit augmentation metadata."""
    prior = helper()
    if parent["application"] != "facturation" or language not in ("en", "fr"):
        raise ValueError("Verified Facturation EN/FR parent required")
    original = target(parent)
    prefix, _ = prior.current_request(parent["messages"][-2]["content"])
    if not text.strip() or re.search(
            r"https?://|(?:password|api[_ -]?key|secret)\s*[:=]|-----BEGIN|\b(?:\d{1,3}\.){3}\d{1,3}\b",
            text, flags=re.I):
        raise ValueError("Unsafe generated request")
    # Parent contrast/category annotations describe the old request and target.
    # Keep only the authenticated envelope and its unchanged capability profile.
    child = {key: deepcopy(parent[key]) for key in (
        "application", "messages", "tools", "capability_profile") if key in parent}
    child["curriculum_category"] = family
    child["messages"][-2]["content"] = prefix + text
    function = child["messages"][-1]["tool_calls"][0]["function"]
    function.update(name=tool or original["name"], arguments=deepcopy(arguments))
    child["language"] = language
    child["augmentation"] = {
        "version": VERSION, "family": family, "source_line": line,
        "source_canonical_row_sha256": sha(encoded(parent).encode()),
        "factors": factors or {},
    }
    target(child)
    if (child["tools"] != parent["tools"]
            or child["messages"][:-2] != parent["messages"][:-2]
            or prior.current_request(child["messages"][-2]["content"])[0] != prefix):
        raise ValueError("Permission schemas, context and history must remain unchanged")
    return child


def month_bounds(today, previous=False):
    today = date.fromisoformat(today)
    first = today.replace(day=1)
    if previous:
        first = (first - timedelta(days=1)).replace(day=1)
    return first.isoformat(), first.replace(
        day=calendar.monthrange(first.year, first.month)[1]).isoformat()


def generate(rows):
    """All parent indices are one based in the pinned TRAIN file."""
    parent = {n: rows[n - 1] for n in PARENTS}
    for row in parent.values():
        target(row)
        trusted_context(row)
    result = []

    def add(n, family, language, text, arguments=None, tool=None, **factors):
        row = parent[n]
        result.append(make(
            row, n, family, language, text,
            target(row)["arguments"] if arguments is None else arguments,
            tool=tool, factors=factors))

    # Inclusive backend date filters are derived with datetime, never string math.
    if target(parent[198]) != {"name": "list_payments", "arguments": {}}:
        raise ValueError("An unbounded list-payments TRAIN parent is required")
    for anchor in ("2031-12-31", "2032-02-29"):
        d = date.fromisoformat(anchor)
        for mode in ("lower_inclusive", "lower_exclusive", "upper_inclusive",
                     "upper_exclusive", "closed"):
            end = (d + timedelta(days=6)).isoformat()
            arguments = {
                "lower_inclusive": {"date_from": anchor},
                "lower_exclusive": {"date_from": (d + timedelta(days=1)).isoformat()},
                "upper_inclusive": {"date_to": anchor},
                "upper_exclusive": {"date_to": (d - timedelta(days=1)).isoformat()},
                "closed": {"date_from": anchor, "date_to": end},
            }[mode]
            phrases = {
                "en": {
                    "lower_inclusive": f"dated on or after {anchor}, with no end date",
                    "lower_exclusive": f"dated strictly after {anchor}, with no end date",
                    "upper_inclusive": f"dated on or before {anchor}, with no start date",
                    "upper_exclusive": f"dated strictly before {anchor}, with no start date",
                    "closed": f"dated from {anchor} through {end}, including both dates",
                },
                "fr": {
                    "lower_inclusive": f"datés à partir du {anchor} inclus, sans date de fin",
                    "lower_exclusive": f"datés strictement après le {anchor}, sans date de fin",
                    "upper_inclusive": f"datés au plus tard le {anchor} inclus, sans date de début",
                    "upper_exclusive": f"datés strictement avant le {anchor}, sans date de début",
                    "closed": f"datés du {anchor} au {end}, les deux dates incluses",
                },
            }
            for language in ("en", "fr"):
                text = (f"Retrieve the valid payments {phrases[language][mode]}."
                        if language == "en" else
                        f"Récupère les règlements valides {phrases[language][mode]}.")
                add(198, "date_boundaries", language, text, arguments,
                    mode=mode, anchor=anchor)
    for language, text in (
        ("en", "Retrieve recent valid payments without any date restriction."),
        ("fr", "Récupère les règlements valides récents sans aucune restriction de date."),
    ):
        add(198, "date_boundaries", language, text, {}, mode="unbounded")

    for n in (97, 111):
        args = target(parent[n])["arguments"]
        collection = n == 111
        if (args.get("resource") != ("users" if collection else "user")
                or set(args) != ({"resource"} if collection else {"resource", "identifier"})):
            raise ValueError("Collection/detail TRAIN contract changed")
        if not collection:
            context = trusted_context(parent[n])
            if args["identifier"] not in context.get("previous_result_identifiers", []):
                raise ValueError("The detail identifier must already be authorized in TRAIN context")
        identifier = args.get("identifier")
        phrases = {
            "en": (["Take me to the users directory.", "Open the user accounts list page.",
                    "Go to the page listing user accounts."] if collection else
                   [f"Take me to the detail page of user account {identifier} from my results.",
                    f"Open the profile for the identified user {identifier}.",
                    f"Show the individual user page for account {identifier} in my results."]),
            "fr": (["Va sur le répertoire des utilisateurs.", "Ouvre la liste des comptes utilisateurs.",
                    "Affiche la page qui liste les utilisateurs."] if collection else
                   [f"Va sur la fiche du compte utilisateur {identifier} présent dans mes résultats.",
                    f"Ouvre le profil de l’utilisateur identifié {identifier}.",
                    f"Affiche la page individuelle du compte {identifier} de mes résultats."]),
        }
        for language, texts in phrases.items():
            for index, text in enumerate(texts):
                add(n, "users_collection_versus_detail", language, text,
                    collection=collection, paraphrase=index)

    roles = {
        330: ("product_name", "location_name"),
        487: ("client_name", "product_name"),
        91: ("client_name", "supplier_name", "product_name", "location_name"),
    }
    labels = {
        "en": {"product_name": "product", "location_name": "location",
               "client_name": "customer", "supplier_name": "supplier"},
        "fr": {"product_name": "produit", "location_name": "emplacement",
               "client_name": "client", "supplier_name": "fournisseur"},
    }
    values = ("SYN-Contrast-Aulne", "SYN-Contrast-Buis", "SYN-Contrast-Charme",
              "SYN-Contrast-Douglas")
    for n, fields in roles.items():
        original = target(parent[n])["arguments"]
        expected_fields = {"resource", *fields} if n != 91 else {
            "resource", "client_name", "supplier_name", "product_name", "status"}
        if original["resource"] != "logistics_order" or set(original) != expected_fields:
            raise ValueError("Logistics TRAIN parent has unhandled filters")
        for order in range(3):
            assigned = {field: values[(i + order) % len(values)]
                        for i, field in enumerate(fields)}
            args = {**original, **assigned}
            if n == 91 and original.get("status") != "Transit":
                raise ValueError("Preserve the logistics Transit restriction")
            ordered = list(fields)
            ordered = ordered[order % len(ordered):] + ordered[:order % len(ordered)]
            for language in ("en", "fr"):
                clauses = [f"{labels[language][field]} {assigned[field]}" for field in ordered]
                restriction = ("; status Transit" if language == "en" else "; statut Transit") if n == 91 else ""
                text = (("Find logistics orders matching " if language == "en" else
                         "Recherche les dossiers logistiques correspondant à ") +
                        "; ".join(clauses) + restriction + ".")
                add(n, "logistics_entity_roles", language, text, args, order=order)

    literals = ("SYN-Ready for verification 401", "SYN-Révision terminée, contrôle accepté.",
                "SYN-Le dossier est vérifié et prêt pour la prochaine étape.")
    for n in (81, 169):
        original = target(parent[n])["arguments"]
        resource = original["resource"]
        if (set(original) != {"resource", "identifier", "operation", "changes"}
                or original["operation"] != "update"
                or resource != ("proforma" if n == 81 else "quote")
                or set(original["changes"]) != {"remarque", "date_echeance"}):
            raise ValueError("Update TRAIN parent has unhandled fields")
        for index, literal in enumerate(literals):
            args = deepcopy(original)
            args["changes"]["remarque"] = literal
            due = args["changes"]["date_echeance"]
            for language in ("en", "fr"):
                label = ({"proforma": "pro forma invoice", "quote": "quote"} if language == "en"
                         else {"proforma": "facture pro forma", "quote": "devis"})[resource]
                value = literal if index == 0 else f"« {literal} »"
                text = (f"For {label} ID {args['identifier']}, set Remark to {value}; set Due date to {due}."
                        if language == "en" else
                        f"Pour le document {label} ID {args['identifier']}, mets Remarque à {value}; mets Date d’échéance au {due}.")
                add(n, "verbatim_update_text", language, text, args, literal_style=index)

    for n in (86, 250):
        original = target(parent[n])["arguments"]
        expected_fields = {"client_name", "product_name", "unpaid", "limit", "date_from"}
        if n == 86:
            expected_fields.add("date_to")
        if original.get("unpaid") is not True or set(original) != expected_fields:
            raise ValueError("Unpaid TRAIN parent has unhandled filters")
        for language in ("en", "fr"):
            for phrase in range(3):
                customer, product = original["client_name"], original["product_name"]
                limit = original["limit"]
                start = original["date_from"]
                end = original.get("date_to")
                when = (f"from {start} through {end}, both inclusive" if end else
                        f"on or after {start} without an end date") if language == "en" else (
                        f"du {start} au {end} inclus" if end else
                        f"à partir du {start} inclus, sans date de fin")
                nouns = ("Find invoices", "Retrieve invoices", "Search for invoices") if language == "en" else (
                        "Retrouve les factures", "Recherche les factures", "Liste les factures")
                base = (f"{nouns[phrase]} for customer {customer} containing product {product}, dated {when}, at most {limit} results"
                        if language == "en" else
                        f"{nouns[phrase]} du client {customer} contenant le produit {product}, datées {when}, au maximum {limit} résultats")
                for unpaid in (False, True):
                    args = deepcopy(original)
                    if not unpaid:
                        del args["unpaid"]
                    suffix = (" with an unpaid balance" if language == "en" else
                              " dont le solde reste impayé") if unpaid else ""
                    add(n, "unpaid_with_other_filters", language, base + suffix + ".",
                        args, unpaid=unpaid, paraphrase=phrase)

    for n in (178, 192):
        context = trusted_context(parent[n])
        ids = context["previous_result_identifiers"]
        if (context["previous_result_count"] != len(ids) or len(ids) < 2
                or context.get("current_identifier") is not None
                or context.get("current_invoice_id") is not None):
            raise ValueError("At least two unresolved authorized results are required")
        resource = context["previous_result_type"]
        for language in ("en", "fr"):
            label = ({"invoice": "invoice", "quote": "quote"} if language == "en" else
                     {"invoice": "facture", "quote": "devis"})[resource]
            for explicit in (False, True):
                text = ((f"Open the second {label} from my results." if explicit else
                         f"I want to open one {label} from my results, but I have not chosen which.")
                        if language == "en" else
                        (f"Ouvre le deuxième document {label} de mes résultats." if explicit else
                         f"Je souhaite ouvrir un document {label} de mes résultats, mais je n’ai pas choisi lequel."))
                args = ({"operation": "open", "index": 2} if explicit else
                        {"reason": "missing_details", "language": language})
                add(n, "ambiguous_previous_result_selection", language, text, args,
                    tool="previous_results" if explicit else "clarify", explicit=explicit)

    # Quote months use the parent's trusted local date; no invented clock/year.
    n = 281
    original = target(parent[n])
    if original != {"name": "search_quotes", "arguments": {"limit": 3}}:
        raise ValueError("The bounded quote-list TRAIN parent changed")
    context = trusted_context(parent[n])
    for previous in (False, True):
        start, end = month_bounds(context["today"], previous)
        calendar_key = "previous_month" if previous else "current_month"
        if context["calendar"][calendar_key + "_first_day"] != start:
            raise ValueError("Trusted calendar and local date disagree")
        if previous and context["calendar"]["previous_month_last_day"] != end:
            raise ValueError("Trusted previous-month end disagrees")
        for language in ("en", "fr"):
            month = ("last month" if previous else "this month") if language == "en" else (
                     "le mois dernier" if previous else "ce mois-ci")
            phrases = ([f"Find quotes issued {month}, at most 3 results.",
                        f"Retrieve up to 3 quotes dated during {month}.",
                        f"Search the quotes from {month}; show no more than 3."]
                       if language == "en" else
                       [f"Retrouve les devis émis {month}, au maximum 3 résultats.",
                        f"Recherche jusqu’à 3 devis datés pendant {month}.",
                        f"Liste les devis de {month}; affiche au plus 3 résultats."])
            for index, text in enumerate(phrases):
                add(n, "relative_quote_month", language, text,
                    {"limit": 3, "date_from": start, "date_to": end},
                    previous=previous, paraphrase=index)

    # Both source contexts already label these unavailable requests unsupported.
    # Financial queries remain unsupported only in the schema without that tool.
    unsupported = {
        177: {
            "en": ["Grant my account permission to modify other users.",
                   "Change my access rights so I can edit user accounts."],
            "fr": ["Donne à mon compte le droit de modifier les autres utilisateurs.",
                   "Change mes droits pour que je puisse modifier les comptes utilisateurs."],
        },
        194: {
            "en": ["Report the company’s annual invoiced revenue in MAD.",
                   "Show this year’s company turnover in MAD."],
            "fr": ["Présente le chiffre d’affaires annuel de la société en MAD.",
                   "Indique le chiffre d’affaires de l’entreprise pour cette année en MAD."],
        },
    }
    if any(t["function"]["name"] == "financial_summary" for t in parent[194]["tools"]):
        raise ValueError("The restricted financial TRAIN parent must not offer reporting")
    for n, languages in unsupported.items():
        if target(parent[n])["arguments"]["reason"] != "unsupported":
            raise ValueError("An existing unsupported TRAIN target is required")
        for language, phrases in languages.items():
            for index, text in enumerate(phrases):
                add(n, "unsupported_current_language", language, text,
                    {"reason": "unsupported", "language": language}, paraphrase=index)
    if Counter(r["augmentation"]["family"] for r in result) != Counter(EXPECTED_FAMILIES):
        raise ValueError("Missing declared semantic contrast family")
    if Counter(r["language"] for r in result) != Counter(en=58, fr=58):
        raise ValueError("Balanced EN/FR contrast coverage required")
    return result


def validate_exclusions(source_rows, generated, development, prior=None):
    prior = prior or helper()
    # Do not inspect development labels. Only messages and offered schemas enter keys.
    excluded = {prior.canonical_input_key(row) for row in development}
    patterns = {prior.request_pattern(row) for row in development}
    seen = set()
    for row in source_rows:
        target(row)
        key = prior.canonical_input_key(row)
        if key in seen or key in excluded:
            raise ValueError("Original replay has duplicate/development inputs")
        seen.add(key)
    for row in generated:
        key = prior.canonical_input_key(row)
        if key in seen or key in excluded or prior.request_pattern(row) in patterns:
            raise ValueError("Generated duplicate or development input/template overlap")
        seen.add(key)


def prepare(source, native, output):
    source, native, output = (Path(p).resolve() for p in (source, native, output))
    if (output.exists() or source == output or source in output.parents
            or not output.parent.is_dir()):
        raise ValueError("A new isolated output directory with an existing parent is required")
    payloads = {name: (source / name).read_bytes() for name in SOURCE_SHA256}
    if {name: sha(raw) for name, raw in payloads.items()} != SOURCE_SHA256:
        raise ValueError("Reviewed TRAIN/development source changed")
    if {name: sha((native / name).read_bytes()) for name in NATIVE_SHA256} != NATIVE_SHA256:
        raise ValueError("Verified native business contracts changed")
    original = payloads["train.jsonl"]
    if not original.endswith(b"\n") or len(original.splitlines()) != 704:
        raise ValueError("The entire approved 704-row replay is required")
    rows = [json.loads(line) for line in original.splitlines()]
    development = [json.loads(line) for line in payloads["valid.jsonl"].splitlines()]
    if (len(development) != 275 or Counter(row["application"] for row in rows) !=
            Counter(facturation=520, management_projet=112, design_workflow=72)):
        raise ValueError("Reviewed application replay counts changed")
    generated = generate(rows)
    validate_exclusions(rows, generated, development)
    additions = ("".join(encoded(row) + "\n" for row in generated)).encode()
    files = {"contrasts.jsonl": additions, "train.jsonl": original + additions,
             "valid.jsonl": payloads["valid.jsonl"]}
    manifest = {
        "version": VERSION, "status": "PREPARED ONLY; diagnostic and numerical review pending",
        "languages": ["en", "fr"],
        "applications": ["facturation", "management_projet", "design_workflow"],
        "source_sha256": SOURCE_SHA256, "native_contract_sha256": NATIVE_SHA256,
        "generator_sha256": sha(Path(__file__).read_bytes()),
        "canonicalization_helper_sha256": HELPER_SHA256,
        "source_rows_preserved_byte_for_byte": 704,
        "new_rows": len(generated), "combined_rows": len(rows) + len(generated),
        "by_family": EXPECTED_FAMILIES, "new_languages": {"en": 58, "fr": 58},
        "application_rows": {"facturation": 636, "management_projet": 112, "design_workflow": 72},
        "parents": {str(n): {
            "raw_row_sha256": sha(original.splitlines()[n - 1]),
            "canonical_row_sha256": sha(encoded(rows[n - 1]).encode()),
            "original_target": target(rows[n - 1]),
        } for n in PARENTS},
        "files": {name: sha(raw) for name, raw in files.items()},
        "generation_sources": "Pinned TRAIN parents and verified native contracts only.",
        "development_use": "Input/template exclusion only; labels never supply a contrast target.",
        "remaining_mechanisms": [
            "Stock-resource product/location distinctions retained but no new contrast.",
            "Staff name versus broader name/email query retained but no new contrast.",
            "Payment client versus broad query retained but no new contrast.",
            "Native-equivalent article aliases remain under frozen exact-argument scoring.",
            "Unsupported invalid-output cause needs raw TRAIN-analogue diagnostic.",
        ],
        "required_next": ["Independent semantic and exact-corpus review",
                          "Server tokenizer/context preflight",
                          "Bounded TRAIN-only selected-parent diagnostic",
                          "Separately reviewed numerical recipe before training"],
        "training_executed": False, "model_accepted": False,
        "production_activation": False, "next_application_training": False,
    }
    # Check inputs a second time before publishing this isolated preparation.
    if any((source / name).read_bytes() != raw for name, raw in payloads.items()):
        raise ValueError("Input changed during preparation")
    output.mkdir(mode=0o700)
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.native, args.output), indent=2, ensure_ascii=False))
