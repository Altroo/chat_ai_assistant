"""Add explicit filter/copy contrasts from approved training metadata only."""
from collections import Counter
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import re

from jsonschema import validate
from build_dialogue_v1 import digest, encode, reframe, write_dataset
from build_shared_v5r3 import key
from prepare_shared_v5r5 import rebalance

ROOT = Path(__file__).resolve().parents[2]
# Native resource identifiers and existing labels, not new backend capabilities.
FACT_DATES = [
    ("search_invoices", None, "invoices", "factures"),
    ("search_quotes", None, "quotes", "devis"),
    ("search_documents", "proforma", "pro forma invoices", "factures pro forma"),
    ("search_documents", "credit_note", "credit notes", "factures d’avoir"),
    ("search_documents", "delivery_note", "delivery notes", "bons de livraison"),
    ("search_articles", None, "article records", "fiches articles"),
    ("search_users", None, "user accounts", "comptes utilisateurs"),
    ("search_payments", None, "payment records", "règlements"),
    ("search_operations", "stock_balance", "stock balance records", "éléments de stock"),
    ("search_operations", "stock_movement", "stock movement records", "mouvements de stock"),
    ("search_operations", "stock_receipt", "stock receipt records", "réceptions de stock"),
    ("search_operations", "stock_inventory", "stock inventory records", "inventaires"),
    ("search_operations", "logistics_order", "logistics orders", "dossiers logistiques"),
]
MG_DATES = [
    ("search_records", "project", "projects", "projets"),
    ("search_records", "quote", "quotes", "devis"),
    ("search_records", "expense", "expenses", "dépenses"),
    ("search_records", "revenue", "receipts", "encaissements"),
    ("search_records", "payment_schedule", "payment schedules", "échéances de paiement"),
    ("search_records", "budget_entry", "actual budget entries", "lignes de budget réel"),
]
RECORD_LABELS = {
    "project": ("project", "projet"), "quote": ("quote", "devis"),
    "expense": ("expense", "dépense"), "revenue": ("receipt", "encaissement"),
    "payment_schedule": ("payment schedule", "échéance de paiement"),
    "budget_entry": ("actual budget entry", "ligne de budget réel"),
    "client": ("customer", "client"), "supplier": ("supplier", "fournisseur"),
    "task": ("task", "tâche"),
}
MONTHS = {
    "en": ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"),
    "fr": ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"),
}


def function(row):
    return row["messages"][-1]["tool_calls"][0]["function"]


def select_template(rows, app, tool, resource=None, predicate=lambda row: True):
    for row in rows:
        target = function(row)
        if (row["application"] == app and target["name"] == tool
                and target["arguments"].get("resource") == resource and predicate(row)):
            return row
    raise ValueError(f"No approved training template for {app}/{tool}/{resource}")


def make_row(template, request, tool, arguments):
    """Retain native prompt/context/schema; label must validate against offered tool."""
    offered = [t["function"] for t in template["tools"] if t["function"]["name"] == tool]
    if len(offered) != 1:
        raise ValueError("Target tool is not uniquely offered")
    validate(arguments, offered[0]["parameters"])
    row = deepcopy(template)
    target = deepcopy(row["messages"][-1])
    target["tool_calls"][0]["function"] = {"name": tool, "arguments": arguments}
    row["messages"] = [row["messages"][0], {"role": "user", "content": request}, target]
    return row


def additions(rows):
    result, categories = [], []

    def add(template, request, tool, args, category):
        result.append(make_row(template, request, tool, args))
        categories.append(category)

    for app, specs in (("facturation", FACT_DATES), ("management_projet", MG_DATES)):
        for index, (tool, resource, en, fr) in enumerate(specs):
            template = select_template(rows, app, tool, resource)
            for mode in ("lower", "upper", "day"):
                # Interior days and different months/years: no month-end inference.
                day = date(2024 + index % 3, 1 + (index * 5) % 12, 12 + index % 13)
                limit = 1 + index % 4
                args = {"resource": resource} if resource else {}
                args["limit"] = limit
                if mode in ("lower", "day"): args["date_from"] = day.isoformat()
                if mode in ("upper", "day"): args["date_to"] = day.isoformat()
                for language, label in (("en", en), ("fr", fr)):
                    written = f"{day.day} {MONTHS[language][day.month-1]} {day.year}"
                    if language == "en":
                        term = {"lower": f"on or after {written}",
                                "upper": f"on or before {written}",
                                "day": f"on {written} only"}[mode]
                        request = f"Find at most {limit} {label} dated {term}."
                    else:
                        term = {"lower": f"à partir du {written} inclus",
                                "upper": f"jusqu’au {written} inclus",
                                "day": f"uniquement le {written}"}[mode]
                        request = f"Recherche au maximum {limit} {label} datés {term}."
                    add(template, request, tool, deepcopy(args), "date_"+mode)

    template = select_template(rows, "facturation", "search_invoices")
    for index in range(8):
        day = date(2023 + index % 3, 1 + (index * 7) % 12, 9 + index)
        customer, product = f"SYN-Citrine-{index+1}", f"SYN-PROFILE-{index+1}"
        args = {"client_name": customer, "product_name": product, "unpaid": True,
                "limit": 1 + index % 4}
        bound = "date_from" if index % 2 == 0 else "date_to"
        args[bound] = day.isoformat()
        en_date = ("since " if bound == "date_from" else "on or before ") + day.isoformat()
        fr_date = ("depuis le " if bound == "date_from" else "au plus tard le ") + day.isoformat()
        prompts = (
            f"Up to {args['limit']} invoices with an outstanding balance for customer {customer}, containing product {product}, dated {en_date}.",
            f"Au plus {args['limit']} factures avec un reste à payer pour le client {customer}, contenant le produit {product}, datées {fr_date}.",
        )
        for request in prompts:
            add(template, request, "search_invoices", deepcopy(args), "combined_unpaid_filters")

    for app in ("management_projet", "design_workflow"):
        resources = sorted({function(row)["arguments"]["resource"] for row in rows
                            if row["application"] == app and function(row)["name"] == "get_record"
                            and set(function(row)["arguments"]) == {"resource"}})
        for resource in resources:
            template = select_template(rows, app, "get_record", resource,
                                       lambda row: set(function(row)["arguments"]) == {"resource"})
            context = json.loads(template["messages"][0]["content"].split("Trusted context: ", 1)[1])
            if context.get("current_resource") != resource or not context.get("current_identifier"):
                raise ValueError("Current-page example lacks trusted current record")
            en, fr = RECORD_LABELS[resource]
            for request in (f"Read the {en} I am currently viewing.",
                            f"Consulte la fiche {fr} actuellement affichée sur ma page."):
                add(template, request, "get_record", {"resource": resource}, "current_page")

    # Both fields are native approved customer fields, not invented schema keys.
    template = select_template(rows, "management_projet", "prepare_change", "client",
                               lambda row: function(row)["arguments"].get("operation") == "update")
    identifier = function(template)["arguments"]["identifier"]
    for index, city in enumerate(("Oujda", "Essaouira", "Larache", "El Jadida")):
        address = f"SYN-Allée des Ateliers {42+index}, bâtiment C"
        args = {"resource": "client", "identifier": identifier, "operation": "update",
                "changes": {"adresse": address, "ville": city}}
        for request in (
                f"Edit customer ID {identifier}: prepare a confirmation preview setting Address to “{address}” and City to “{city}”.",
                f"Modifie le client ID {identifier} dans un aperçu à confirmer : Adresse « {address} », Ville « {city} »."):
            add(template, request, "prepare_change", deepcopy(args), "literal_multifield")

    # Quoted multiword text must survive exactly, including punctuation.
    for resource, en, fr in (("quote", "quote", "devis"), ("proforma", "proforma", "facture pro forma"),
                             ("credit_note", "credit note", "facture d’avoir"), ("delivery_note", "delivery note", "bon de livraison")):
        template = select_template(rows, "facturation", "prepare_change", resource,
                                   lambda row: "remarque" in function(row)["arguments"].get("changes", {}))
        args = deepcopy(function(template)["arguments"])
        value = "SYN-Vérification terminée ; conserver les deux exemplaires."
        args["changes"] = {"remarque": value}
        identifier = args["identifier"]
        for request in (
                f"Prepare an update to {en} ID {identifier}: set Remark to exactly “{value}”, pending my confirmation.",
                f"Prépare la modification du document {fr} ID {identifier} : Remarque exactement « {value} », à confirmer ensuite."):
            add(template, request, "prepare_change", deepcopy(args), "literal_text")
    repaired, history = rebalance(result)
    return [{**row, "messages": reframe(row["messages"])} for row in repaired], categories, history


def current_request(row):
    text = row["messages"][-2]["content"]
    return text.split("\nCurrent request: ", 1)[1] if text.startswith("Earlier user messages (background only): ") else text


def prepare():
    parent = ROOT/"training/datasets/shared-v5r5-en-fr"
    output = ROOT/"training/datasets/shared-v5r6-en-fr"
    if output.exists(): raise ValueError("Never overwrite a versioned dataset")
    manifest = json.loads((parent/"manifest.json").read_text())
    for name in ("train.jsonl", "valid.jsonl"):
        if digest(parent/name) != manifest["files"][name]: raise ValueError("Parent data changed")
    train = [json.loads(line) for line in (parent/"train.jsonl").read_text().splitlines()]
    valid = [json.loads(line) for line in (parent/"valid.jsonl").read_text().splitlines()]
    extra, categories, history = additions(train)
    excluded = {key(row["application"], current_request(row)) for row in train+valid}
    for relative, proof in manifest["held_out"].items():
        path = ROOT/relative
        if digest(path) != proof["sha256"]: raise ValueError("Frozen evaluation changed")
        for row in map(json.loads, path.read_text().splitlines()):
            app = json.loads(row["messages"][0]["content"].split("Trusted context: ", 1)[1])["application"]
            excluded.add(key(app, row["messages"][-1]["content"]))
    seen = set()
    for row in extra:
        identity = key(row["application"], current_request(row))
        if identity in excluded or identity in seen: raise ValueError("Duplicate or frozen request in additions")
        seen.add(identity)
    payload = (parent/"train.jsonl").read_text() + encode(extra)
    if re.search(r"[\u0600-\u06ff]|BEGIN.{0,12}PRIVATE KEY|Bearer\s+\S+|(?:password|api_key|secret)\s*[:=]", payload, re.I):
        raise ValueError("Sensitive or out-of-scope language content")
    report = {
        "version": output.name, "applications": manifest["applications"], "languages": ["en", "fr"],
        "generator_sha256": digest(Path(__file__)),
        "parent_manifest_sha256": digest(parent/"manifest.json"),
        "helpers": {name: digest(ROOT/"training/scripts"/name) for name in
                    ("build_dialogue_v1.py", "build_shared_v5r3.py", "prepare_shared_v5r5.py")},
        "planning_messages_sha256": manifest["planning_messages_sha256"],
        "source_files": manifest["files"], "held_out": manifest["held_out"],
        "held_out_count": manifest["held_out_count"],
        "evaluation_manifest_sha256": manifest["evaluation_manifest_sha256"],
        "counts": {"retained_train": len(train), "added_train": len(extra), "train": len(train)+len(extra), "valid": len(valid)},
        "added_categories": dict(Counter(categories)),
        "added_applications": dict(Counter(row["application"] for row in extra)),
        "history_assignment": history,
        "split_policy": "Retain exact parent train bytes and unchanged validation. New synthetic training-only contrasts reuse approved native metadata. No frozen validation/test request or expected answer is copied into training; normalized overlap is rejected. Resource/language/date variants are correlated. Existing regressions are repeatedly inspected, not blind certification.",
        "training_policy": "PREPARED ONLY. Server preflight, capacity, baseline and reviewed training configuration required. One shared model; no automatic training, download or activation.",
    }
    write_dataset(output, {"train.jsonl": payload, "valid.jsonl": (parent/"valid.jsonl").read_text()}, report)
    return report


if __name__ == "__main__":
    print(json.dumps(prepare()["counts"]))
