"""Prepare balanced, source-verified Facturation extraction contrasts.

Preparation only: no model loading, numerical training, database queries, or
acceptance claim. Existing focused training and validation bytes are retained.
"""
import argparse
import calendar
from collections import Counter
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import prepare_facturation_focus_v1 as prior
from prepare_shared_v5r6 import MONTHS, current_request, function, select_template
from prepare_shared_v5r8 import context, native_check, SECRET
from build_shared_v5r3 import key
from build_dialogue_v1 import encode

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "training/datasets/facturation-focus-v1-en-fr"
PARENT_SHA = "70d19dd8ed341f13bd8dcd9b17f00382f0e75c996bb098260e27ddf5919b470c"
VERSION = "facturation-focus-v2-en-fr"
DOCUMENTS = (
    ("search_invoices", None, "factures clients", "customer invoices"),
    ("search_quotes", None, "devis", "quotes"),
    ("search_documents", "proforma", "factures pro forma", "pro forma invoices"),
    ("search_documents", "credit_note", "factures d’avoir", "credit notes"),
    ("search_documents", "delivery_note", "bons de livraison", "delivery notes"),
)
OPERATIONS = (
    ("stock_balance", "fiches de stock", "stock balance records", "mises à jour", "updated"),
    ("stock_movement", "mouvements de stock", "stock movements", "créés", "created"),
    ("stock_receipt", "réceptions de stock", "stock receipts", "créées", "created"),
    ("stock_inventory", "inventaires", "stock inventories", "créés", "created"),
    ("logistics_order", "dossiers logistiques", "logistics orders", "créés", "created"),
)
DOCUMENT_MODES = ("none", "lower", "upper", "month")
OPERATION_MODES = ("none", "lower", "upper", "day")
OPTIONAL_STATES = ("none", "first", "second", "limit")
ADDED_COUNT = 440
NATIVE_UPDATES = {
    "chat_ai/operations.py": {
        "previous_sha256": "8107fc9dadc8c0d6051068f9ab6fe606214a96963656eb51e08b6c0041cff862",
        "current_sha256": "06d87733927bf6eace463b8fbb2e235cca4acc45653909d8b64ab712203e74d0",
        "source_commit": "e00a9012351f9d9287223e994cd455da36fe67e5",
        "reason": "Reviewed supplier-workflow read scoping; tool schemas and permissions unchanged.",
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def retained():
    if sha(PARENT / "manifest.json") != PARENT_SHA:
        raise ValueError("Reviewed focused parent manifest changed")
    manifest = json.loads((PARENT / "manifest.json").read_text())
    payloads, rows = {}, {}
    for split, count in (("train", 1047), ("valid", 133)):
        raw = (PARENT / (split + ".jsonl")).read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["files"][split + ".jsonl"]:
            raise ValueError("Reviewed focused parent split changed")
        lines = raw.splitlines(keepends=True)
        if any(not line.endswith(b"\n") for line in lines):
            raise ValueError("Complete newline-terminated parent rows required")
        values = [json.loads(line) for line in lines]
        if len(values) != count or {r["application"] for r in values} != {"facturation"}:
            raise ValueError("Unexpected focused parent scope")
        payloads[split + ".jsonl"] = raw
        rows[split] = values
    return manifest, payloads, rows




def checked_helpers(manifest):
    generator = Path(prior.__file__)
    if sha(generator) != manifest["generator_sha256"]:
        raise ValueError("Reviewed parent generator changed")
    helpers = prior.helpers(manifest)
    helpers["training/scripts/prepare_facturation_focus_v1.py"] = sha(generator)
    return helpers


def native_expectations(manifest):
    expected = dict(manifest["native_metadata"]["facturation"])
    for name, transition in NATIVE_UPDATES.items():
        if expected.get(name) != transition["previous_sha256"]:
            raise ValueError("Native source transition no longer matches parent")
        expected[name] = transition["current_sha256"]
    return expected


def bounds(day, mode):
    if mode == "none":
        return {}
    if mode == "lower":
        return {"date_from": day.isoformat()}
    if mode == "upper":
        return {"date_to": day.isoformat()}
    if mode == "day":
        return {"date_from": day.isoformat(), "date_to": day.isoformat()}
    if mode == "after":
        return {"date_from": (day + timedelta(days=1)).isoformat()}
    if mode == "before":
        return {"date_to": (day - timedelta(days=1)).isoformat()}
    if mode == "month":
        return {"date_from": day.replace(day=1).isoformat(),
                "date_to": day.replace(day=calendar.monthrange(day.year, day.month)[1]).isoformat()}
    raise ValueError("Unsupported declared date mode")


def matrix_day(resource_index, mode_index):
    # Each date mode sees every year, month and day width across the five resources.
    years = (2041, 2044, 2047, 2050, 2053)
    months = (2, 4, 7, 9, 12)
    days = (2, 5, 8, 14, 23)
    return date(years[(resource_index + mode_index) % 5],
                months[(resource_index + 2 * mode_index) % 5],
                days[(resource_index + 3 * mode_index) % 5])


def date_words(day, mode, locale, iso=False):
    written = day.isoformat() if iso else f"{day.day} {MONTHS[locale][day.month - 1]} {day.year}"
    if locale == "fr":
        return {
            "none": "", "lower": f"à compter du {written} inclus",
            "upper": f"jusqu’au {written} inclus", "day": f"le {written} seulement",
            "month": f"pendant {MONTHS['fr'][day.month - 1]} {day.year}",
            "after": f"strictement après le {written}", "before": f"strictement avant le {written}",
        }[mode]
    return {
        "none": "", "lower": f"on {written} or later",
        "upper": f"up to and including {written}", "day": f"on {written} only",
        "month": f"during {MONTHS['en'][day.month - 1]} {day.year}",
        "after": f"strictly after {written}", "before": f"strictly before {written}",
    }[mode]


def additions(parent):
    result = []

    def add(tool, args, fr, en, category, family, *, profile="member_read",
            trusted=None, template_tool=None, template_resource=None, details=None):
        resource = args.get("resource") if template_resource is None else template_resource
        source_tool = template_tool or tool
        template = select_template(parent, "facturation", source_tool,
                                   None if template_tool else resource)
        # Context/history are fixed for all controlled variants in this family.
        history = int(hashlib.sha256(family.encode()).hexdigest()[:8], 16) % 2 == 1
        for language, request in (("fr", fr), ("en", en)):
            row = deepcopy(template)
            ctx = context(row)
            ctx.update(current_invoice_id=None, current_resource=None, current_identifier=None,
                       previous_result_type=None, previous_result_count=0,
                       previous_result_identifiers=[], interface_language="en" if language == "fr" else "fr")
            ctx.pop("shortcut_search_hint", None)
            ctx.update(trusted or {})
            row["messages"][0]["content"] = row["messages"][0]["content"].split("Trusted context: ", 1)[0] + "Trusted context: " + json.dumps(ctx, ensure_ascii=False)
            target = {"name": tool, "arguments": deepcopy(args)}
            if tool == "clarify":
                target["arguments"]["language"] = language
            if history:
                greeting = "Thank you for your help." if language == "fr" else "Merci pour votre aide."
                request = "Earlier user messages (background only): " + json.dumps([greeting], ensure_ascii=False) + "\nCurrent request: " + request
            row["messages"] = [row["messages"][0], {"role": "user", "content": request},
                {"role": "assistant", "content": None, "tool_calls": [{"type": "function", "function": target}]}]
            row.update(application="facturation", language=language, capability_profile=profile,
                       curriculum_category=category, contrast_family=family, contrast=deepcopy(details or {}))
            result.append(row)

    # True resource x date-mode x optional-state x language matrices. Dates,
    # literals, wording, history and context stay fixed across optional states.
    for i, (tool, resource, fr_label, en_label) in enumerate(DOCUMENTS):
        for j, mode in enumerate(DOCUMENT_MODES):
            day = matrix_day(i, j)
            customer, product = f"SYN-Atelier Rivage {41+i+j}", f"SYN-Panneau Frêne {73+i+j}"
            family = f"document-{i}-{mode}"
            for state in OPTIONAL_STATES:
                args = {"resource": resource} if resource else {}
                args.update(bounds(day, mode))
                fr = "Retrouve les " + fr_label
                en = "Locate the " + en_label
                if mode != "none":
                    fr += (" datées " if fr_label.startswith("factures") else " datés ") + date_words(day, mode, "fr", (i+j) % 2 == 0)
                    en += " dated " + date_words(day, mode, "en", (i+j) % 2 == 0)
                if state == "first":
                    args["client_name"] = customer
                    fr += f", pour le client {customer}"
                    en += f", for customer {customer}"
                elif state == "second":
                    args["product_name"] = product
                    fr += f", contenant l’article {product}"
                    en += f", containing article {product}"
                elif state == "limit":
                    args["limit"] = 2 + (i+j) % 4
                    fr += f", avec au maximum {args['limit']} résultats"
                    en += f", with at most {args['limit']} results"
                add(tool, args, fr + ".", en + ".", "date_optional_document", family,
                    details={"mode": mode, "literal_date": day.isoformat(), "optional_state": state,
                             "iso_literal": (i+j) % 2 == 0})

    for i, (resource, fr_label, en_label, fr_verb, en_verb) in enumerate(OPERATIONS):
        for j, mode in enumerate(OPERATION_MODES):
            day = matrix_day(i, j)
            product, location = f"SYN-Profil Noyer {91+i+j}", f"SYN-Dépôt Ardoise {111+i+j}"
            family = f"operation-{resource}-{mode}"
            for state in OPTIONAL_STATES:
                args = {"resource": resource, **bounds(day, mode)}
                fr, en = "Recherche les " + fr_label, "Find the " + en_label
                if mode != "none":
                    fr += f" {fr_verb} " + date_words(day, mode, "fr", (i+j) % 2 != 0)
                    en += f" {en_verb} " + date_words(day, mode, "en", (i+j) % 2 != 0)
                if state == "first":
                    args["product_name"] = product
                    fr += f", pour le produit {product}"
                    en += f", for product {product}"
                elif state == "second":
                    args["location_name"] = location
                    fr += f", dans le dépôt {location}"
                    en += f", at location {location}"
                elif state == "limit":
                    args["limit"] = 2 + (i+j) % 4
                    fr += f", au maximum {args['limit']} correspondances"
                    en += f", at most {args['limit']} matches"
                add("search_operations", args, fr + ".", en + ".", "date_optional_operation", family,
                    details={"mode": mode, "literal_date": day.isoformat(), "optional_state": state,
                             "iso_literal": (i+j) % 2 != 0})

    for i, (tool, resource, fr_label, en_label) in enumerate(DOCUMENTS):
        day = date(2046 + i, 3 + i, 4 + i)
        customer, product = f"SYN-Maison Bruyère {142+i}", f"SYN-Charnière Satin {173+i}"
        for limited in (False, True):
            args = {"resource": resource} if resource else {}
            args.update(bounds(day, "upper"), client_name=customer, product_name=product)
            fr_date_label = "datées" if fr_label.startswith("factures") else "datés"
            fr = f"Croise le client {customer} et l’article {product} pour les {fr_label} {fr_date_label} {date_words(day, 'upper', 'fr')}."
            en = f"Match both customer {customer} and article {product} in {en_label} dated {date_words(day, 'upper', 'en')}."
            if limited:
                args["limit"] = 4
                fr += " Garde au plus quatre correspondances."
                en += " Keep at most four matches."
            add(tool, args, fr, en, "mixed_document_filters", f"mixed-document-{i}",
                details={"mode": "upper", "literal_date": day.isoformat(), "limit_present": limited})

    for j, mode in enumerate(DOCUMENT_MODES):
        day = matrix_day(4, j)
        for limited in (False, True):
            for unpaid in (False, True):
                args = {**bounds(day, mode), "client_name": "SYN-Atelier Genêt 214", "product_name": "SYN-Rail Cuivré 257"}
                fr = "Recherche les factures clients de SYN-Atelier Genêt 214 contenant l’article SYN-Rail Cuivré 257"
                en = "Search customer invoices for SYN-Atelier Genêt 214 containing article SYN-Rail Cuivré 257"
                if mode != "none":
                    fr += " datées " + date_words(day, mode, "fr")
                    en += " dated " + date_words(day, mode, "en")
                if limited:
                    args["limit"] = 3
                    fr += ", au maximum trois résultats"
                    en += ", at most three results"
                if unpaid:
                    args["unpaid"] = True
                    fr += ", avec un solde restant à payer, y compris les factures partiellement réglées"
                    en += ", with an unpaid balance, including partially paid invoices"
                add("search_invoices", args, fr + ".", en + ".", "unpaid_optional_filters", f"unpaid-{mode}",
                    details={"mode": mode, "literal_date": day.isoformat(),
                             "limit_present": limited, "unpaid_present": unpaid})

    boundary_specs = (
        ("search_quotes", None, "devis", "quotes", date(2048, 3, 1), ("upper", "before")),
        ("search_documents", "proforma", "factures pro forma", "pro forma invoices", date(2047, 1, 1), ("upper", "before")),
        ("search_operations", "stock_balance", "fiches de stock mises à jour", "stock balance records updated", date(2044, 2, 29), ("lower", "after")),
        ("search_operations", "logistics_order", "dossiers logistiques créés", "logistics orders created", date(2047, 12, 31), ("lower", "after")),
    )
    for i, (tool, resource, fr_label, en_label, day, modes) in enumerate(boundary_specs):
        for mode in modes:
            args = {"resource": resource} if resource else {}
            args.update(bounds(day, mode))
            add(tool, args, f"Retrouve les {fr_label} {date_words(day, mode, 'fr')}.",
                f"Locate the {en_label} {date_words(day, mode, 'en')}.",
                "exclusive_boundary", f"boundary-{i}",
                details={"mode": mode, "literal_date": day.isoformat()})

    remarks = ("SYN-Révision technique effectuée sans observation", "SYN-Delivery inspection completed with no reservation")
    for i, remark in enumerate(remarks):
        identifier, due = 99503 + i * 13, (date(2047, 10, 19), date(2048, 4, 7))[i].isoformat()
        quoted = False
        value = remark
        for fields in ("remark_only", "due_only", "both"):
            changes, fr_lines, en_lines = {}, [], []
            if fields != "due_only":
                changes["remarque"] = remark
                fr_lines.append("Remarque : " + value)
                en_lines.append("Remark: " + value)
            if fields != "remark_only":
                changes["date_echeance"] = due
                fr_lines.append("Date d’échéance : " + due)
                en_lines.append("Due date: " + due)
            add("prepare_change", {"resource": "proforma", "identifier": identifier,
                "operation": "update", "changes": changes},
                f"Prépare un aperçu de ces modifications pour la pro forma sélectionnée {identifier} :\n" + "\n".join(fr_lines),
                f"Prepare a preview of these changes for selected pro forma {identifier}:\n" + "\n".join(en_lines),
                "literal_field_copy", f"literal-{i}",
                profile="member_edit", trusted={"previous_result_type": "proforma",
                "previous_result_count": 1, "previous_result_identifiers": [identifier]},
                details={"fields": fields, "quoted": quoted, "literal": remark, "due_date": due})

    list_texts = (
        ("Affiche le répertoire des comptes utilisateurs, sans choisir une fiche.", "Show the user account directory without selecting a detail record."),
        ("Ouvre la page de la liste des utilisateurs autorisés.", "Open the page listing the user accounts I may access."),
    )
    for i, (fr, en) in enumerate(list_texts):
        identifier = 99611 + i * 7
        add("navigate", {"resource": "users"}, fr, en, "account_navigation", f"user-list-{i}",
            profile="staff_read", template_resource="users", details={"target": "list"})
        add("navigate", {"resource": "user", "identifier": identifier},
            f"Consulte la fiche du compte utilisateur {identifier}, déjà identifié dans mes résultats.",
            f"Open the detail record of user account {identifier}, already identified in my results.",
            "account_navigation", f"user-detail-{i}", profile="staff_read", template_resource="users",
            trusted={"previous_result_type": "user", "previous_result_count": 1,
                     "previous_result_identifiers": [identifier]}, details={"target": "detail"})

    for resource, fr_label, en_label in (("invoice", "factures", "invoices"), ("proforma", "pro formas", "pro forma invoices")):
        trusted = {"previous_result_type": resource, "previous_result_count": 2,
                   "previous_result_identifiers": [99719, 99743]}
        add("clarify", {"reason": "missing_details"},
            f"Dans les {fr_label} trouvées, je n’ai encore sélectionné aucune fiche à ouvrir.",
            f"Among the {en_label} found, I have not selected any record to open yet.",
            "explicit_result_choice", "choice-" + resource, template_tool="previous_results",
            trusted=trusted, details={"selection": "unspecified"})
        add("previous_results", {"operation": "open", "index": 2},
            f"Ouvre la deuxième fiche de cette liste de {fr_label}.",
            f"Open the second record in this list of {en_label}.",
            "explicit_result_choice", "choice-" + resource, trusted=trusted, details={"selection": "second"})

    for i, invoice in enumerate(("31476/46", "45821/49")):
        for limited in (False, True):
            args = {"invoice_number": invoice}
            fr, en = f"Recherche les écritures de règlement de la facture {invoice}.", f"Find the payment entries for invoice {invoice}."
            if limited:
                args["limit"] = 4
                fr += " Je souhaite au plus quatre écritures."
                en += " I need at most four entries."
            add("search_payments", args, fr, en, "payment_reference_limit", f"payment-invoice-{i}",
                details={"limit_present": limited})

    for status, fr_status, en_status in (("Annulé", "annulés", "cancelled"), ("Valide", "validés", "validated")):
        for state in ("none", "client", "product", "both"):
            args = {"status": status}
            fr, en = f"Recherche les règlements {fr_status}", f"Search {en_status} payments"
            if state in ("client", "both"):
                args["client_name"] = "SYN-Atelier Aigue-Marie 302"
                fr += " du client SYN-Atelier Aigue-Marie 302"
                en += " for customer SYN-Atelier Aigue-Marie 302"
            if state in ("product", "both"):
                args["product_name"] = "SYN-Raccord Néroli 343"
                fr += " liés à des factures contenant l’article SYN-Raccord Néroli 343"
                en += " linked to invoices containing article SYN-Raccord Néroli 343"
            add("search_payments", args, fr + ".", en + ".", "payment_party_filters", "payment-parties-" + status,
                details={"party_state": state, "status": status})

    if len(result) != ADDED_COUNT:
        raise ValueError("Declared supplement count changed")
    return result


def prepare(backend, interpreter, output):
    if output.exists():
        raise ValueError("Never overwrite a versioned curriculum")
    manifest, payloads, parents = retained()
    helper_hashes = checked_helpers(manifest)
    for relative, expected in native_expectations(manifest).items():
        if sha(backend / relative) != expected:
            raise ValueError("Reviewed native Facturation source changed")
    draft = additions(parents["train"])
    if SECRET.search(encode(draft)):
        raise ValueError("Sensitive or unsupported-language content in supplement")
    command = [str(interpreter), "-B", str(Path(__file__).resolve()), "--native-check", "--backend", str(backend)]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT / "training/scripts"))),
           "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(command, input=json.dumps(draft), text=True, capture_output=True, env=env)
    if result.returncode:
        raise RuntimeError("Native metadata check failed: " + result.stderr[-2500:])
    verified = json.loads(result.stdout)
    rows = verified["rows"]
    if len(rows) != len(draft) or any(function(a) != function(b) or current_request(a) != current_request(b)
                                    for a, b in zip(draft, rows)):
        raise ValueError("Native validation changed a request or target")
    for relative, digest in verified["native_sha256"].items():
        if sha(backend / relative) != digest:
            raise ValueError("Native source changed during metadata validation")
    r11_manifest, _, _ = prior.retained()
    prior.check_exclusions(r11_manifest, rows)
    new_keys = [key("facturation", current_request(row)) for row in rows]
    if len(set(new_keys)) != len(rows):
        raise ValueError("Supplement has repeated requests")
    if set(new_keys) & {key("facturation", current_request(row)) for row in parents["train"]}:
        raise ValueError("Supplement repeats retained training")
    payloads["train.jsonl"] += encode(rows).encode()
    summary = {
        "version": VERSION, "applications": ["facturation"], "languages": ["en", "fr"],
        "status": "PREPARATION ONLY; no numerical training or acceptance",
        "source_manifest_sha256": PARENT_SHA, "generator_sha256": sha(Path(__file__)),
        "helper_sha256": helper_hashes, "source_validation_sha256": manifest["files"]["valid.jsonl"],
        "counts": {"train": len(parents["train"]) + len(rows), "valid": len(parents["valid"]),
                   "retained_training_rows_byte_identical": 1047,
                   "retained_validation_rows_byte_identical": 133, "added": len(rows),
                   "added_categories": dict(Counter(row["curriculum_category"] for row in rows))},
        "native_metadata": {"facturation": {**manifest["native_metadata"]["facturation"], **verified["native_sha256"]}},
        "native_source_updates": deepcopy(NATIVE_UPDATES),
        "held_out": manifest["held_out"], "historical_regression_held_out": manifest["historical_regression_held_out"],
        "fresh_controls": manifest["fresh_controls"],
        "regression_applications": ["facturation", "management_projet", "design_workflow"],
        "training_policy": "Prepare Facturation only. Finish the active evaluation and bind the measured base. Require an explicitly axis-balanced bounded server pilot and same-base development/regression comparison before considering any longer run. No automatic full epoch or production activation.",
        "limitations": [
            "Development error families informed coverage; no evaluation request or target was copied into training.",
            "The four optional states isolate omission and individual filters; mixed-argument examples are separate, not a full power set.",
            "Request literals/history/context are controlled within a family; the actual native shortlist is recomputed and can differ when optional filters are mentioned. Complete model inputs are not identical.",
            "Date modes are balanced across literals at matrix level; correlated bilingual and controlled variants are not independent observations.",
            "Native metadata validation does not execute business operations or establish authorization or model accuracy.",
            "The existing pilot admission does not admit this new manifest; new reviewed admission and resource checks are still required.",
        ],
        "files": {name: hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()},
    }
    output.mkdir()
    for name, raw in payloads.items():
        (output / name).write_bytes(raw)
    (output / "manifest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--backend-python", type=Path)
    parser.add_argument("--native-check", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "training/datasets" / VERSION)
    args = parser.parse_args()
    if args.native_check:
        print(json.dumps(native_check("facturation", args.backend, json.load(sys.stdin)), ensure_ascii=False))
    else:
        if not args.backend_python:
            parser.error("--backend-python is required")
        print(json.dumps(prepare(args.backend, args.backend_python, args.output)["counts"]))
