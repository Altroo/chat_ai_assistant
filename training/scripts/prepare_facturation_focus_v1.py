"""Prepare a Facturation-only refinement from verified synthetic sources.

Retains every Facturation training/validation row from R11. Adds modest
counterfactual contrasts, without changing another app or any acceptance data.
This does not select weights, launch training, or establish model acceptance.
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

from prepare_shared_v5r6 import MONTHS, current_request, function, select_template
from prepare_shared_v5r8 import context, native_check
from prepare_coverage_contrasts_v1 import check_exclusions as legacy_exclusions
from prepare_coverage_contrasts_v1 import PARENT as EXCLUSION_PARENT
from build_shared_v5r3 import key
from build_dialogue_v1 import encode

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "training/datasets/shared-v5r11-en-fr"
PARENT_SHA = "02f2addad85051fd20a180b29c01239f67f8ceeb8265ace8b054d09f1f81ccdc"
VERSION = "facturation-focus-v1-en-fr"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def retained():
    if sha(PARENT / "manifest.json") != PARENT_SHA:
        raise ValueError("Reviewed R11 manifest changed")
    manifest = json.loads((PARENT / "manifest.json").read_text())
    payloads, parents = {}, {}
    for split, expected in (("train", 931), ("valid", 133)):
        path = PARENT / (split + ".jsonl")
        if sha(path) != manifest["files"][path.name]:
            raise ValueError("Reviewed R11 split changed")
        lines = path.read_bytes().splitlines(keepends=True)
        if any(not line.endswith(b"\n") for line in lines):
            raise ValueError("Complete newline-terminated rows required")
        selected = [line for line in lines if json.loads(line)["application"] == "facturation"]
        if len(selected) != expected:
            raise ValueError("Unexpected Facturation retained row count")
        payloads[path.name] = b"".join(selected)
        parents[split] = [json.loads(line) for line in selected]
    return manifest, payloads, parents


def check_exclusions(manifest, rows):
    # Bind both the actual R11 validation source and the legacy helper input.
    # Labels are not used: only normalized current-request keys are compared.
    validation = PARENT / "valid.jsonl"
    expected = manifest["files"]["valid.jsonl"]
    if sha(validation) != expected or sha(EXCLUSION_PARENT / "valid.jsonl") != expected:
        raise ValueError("Pinned validation exclusion input changed")
    excluded = {key(r["application"], current_request(r))
                for r in map(json.loads, validation.read_text().splitlines())}
    if any(key(r["application"], current_request(r)) in excluded for r in rows):
        raise ValueError("Frozen validation request overlap")
    return legacy_exclusions(manifest, rows)


def helpers(manifest):
    for relative, expected in manifest["helper_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError("Reviewed generation helper changed")
    extra = (
        "training/scripts/prepare_shared_v5r6.py", "training/scripts/prepare_shared_v5r8.py",
        "training/scripts/prepare_coverage_contrasts_v1.py", "training/scripts/prepare_shared_v5r5.py",
        "training/scripts/build_shared_v5r3.py", "training/scripts/build_dialogue_v1.py",
        "training/scripts/training_contracts.py", "training/scripts/build_dataset_v4.py",
        "src/chat_ai_assistant/calendar_context.py", "src/chat_ai_assistant/clarifications.py",
        "src/chat_ai_assistant/planning_messages.py", "src/chat_ai_assistant/contracts.py",
        "src/chat_ai_assistant/orchestrator.py", "src/chat_ai_assistant/routing.py",
        "src/chat_ai_assistant/selection_context.py")
    return {relative: sha(ROOT / relative)
            for relative in sorted(set(manifest["helper_sha256"]) | set(extra))}


def additions(parent):
    rows = []

    def add(tool, args, fr, en, category, *, profile="member_read", trusted=None,
            template_resource=None, template_tool=None, details=None):
        resource = args.get("resource") if template_resource is None else template_resource
        template = select_template(parent, "facturation", template_tool or tool,
                                   None if template_tool else resource)
        for language, request in (("fr", fr), ("en", en)):
            row = deepcopy(template)
            ctx = context(row)
            ctx.update(current_invoice_id=None, previous_result_type=None,
                       previous_result_count=0, previous_result_identifiers=[],
                       current_resource=None, current_identifier=None,
                       interface_language="en" if language == "fr" else "fr")
            ctx.pop("shortcut_search_hint", None)
            ctx.update(trusted or {})
            row["messages"][0]["content"] = row["messages"][0]["content"].split("Trusted context: ", 1)[0] + "Trusted context: " + json.dumps(ctx, ensure_ascii=False)
            # Half the bilingual scenarios have history; it never supplies authority.
            if (len(rows) // 2) % 2:
                greeting = "Thanks for your help." if language == "fr" else "Merci pour votre aide."
                request = "Earlier user messages (background only): " + json.dumps([greeting]) + "\nCurrent request: " + request
            target = {"name": tool, "arguments": deepcopy(args)}
            if tool == "clarify":
                target["arguments"]["language"] = language
            row["messages"] = [row["messages"][0], {"role": "user", "content": request},
                {"role": "assistant", "content": None, "tool_calls": [{"type": "function", "function": target}]}]
            row.update(application="facturation", language=language,
                       capability_profile=profile, curriculum_category=category,
                       contrast=deepcopy(details or {}))
            rows.append(row)

    documents = (
        ("search_invoices", None, "factures clients", "customer invoices"),
        ("search_quotes", None, "devis", "quotations"),
        ("search_documents", "proforma", "factures pro forma", "pro forma invoices"),
        ("search_documents", "credit_note", "factures d’avoir", "credit notes"),
        ("search_documents", "delivery_note", "bons de livraison", "delivery notes"))
    for i, (tool, resource, fr_label, en_label) in enumerate(documents):
        for j, operator in enumerate(("lower", "upper", "day", "after", "before", "month")):
            day = date(2037 + (i + j) % 4, 1 + (i * 3 + j * 5) % 12, (3, 8, 17, 26, 7, 21)[(i + j) % 6])
            args = {"resource": resource} if resource else {}
            lower = day + timedelta(days=1) if operator == "after" else day
            upper = day - timedelta(days=1) if operator == "before" else day
            if operator == "month":
                lower = day.replace(day=1)
                upper = day.replace(day=calendar.monthrange(day.year, day.month)[1])
            if operator in ("lower", "day", "after", "month"):
                args["date_from"] = lower.isoformat()
            if operator in ("upper", "day", "before", "month"):
                args["date_to"] = upper.isoformat()
            customer, product = f"SYN-Atelier Acacia {i * 10 + j + 40}", f"SYN-Panneau Érable {i * 10 + j + 70}"
            qualifiers_fr, qualifiers_en = [], []
            if (i + j) % 3 != 1:
                args["client_name"] = customer
                qualifiers_fr.append(f"pour le client {customer}")
                qualifiers_en.append(f"for customer {customer}")
            if (i + j) % 3 != 0:
                args["product_name"] = product
                qualifiers_fr.append(f"contenant le produit {product}")
                qualifiers_en.append(f"containing product {product}")
            if tool == "search_invoices" and j % 2 == 0:
                args["unpaid"] = True
                qualifiers_fr.append("dont le solde reste à payer")
                qualifiers_en.append("whose balance remains unpaid")
            if j % 2:
                args["limit"] = 2 + (i + j) % 4
                qualifiers_fr.append(f"au maximum {args['limit']} résultats")
                qualifiers_en.append(f"at most {args['limit']} results")
            written = {lang: f"{day.day} {MONTHS[lang][day.month-1]} {day.year}" for lang in ("fr", "en")}
            dates_fr = {"lower": f"le {written['fr']} ou après", "upper": f"au plus tard le {written['fr']}",
                        "day": f"le {written['fr']} uniquement", "after": f"strictement après le {written['fr']}",
                        "before": f"strictement avant le {written['fr']}", "month": f"pendant {MONTHS['fr'][day.month-1]} {day.year}"}
            dates_en = {"lower": f"on {written['en']} or later", "upper": f"no later than {written['en']}",
                        "day": f"on {written['en']} only", "after": f"strictly after {written['en']}",
                        "before": f"strictly before {written['en']}", "month": f"during {MONTHS['en'][day.month-1]} {day.year}"}
            add(tool, args,
                f"Recherche les {fr_label} datés {dates_fr[operator]}, " + ", ".join(qualifiers_fr) + ".",
                f"Find the {en_label} dated {dates_en[operator]}, " + ", ".join(qualifiers_en) + ".",
                "document_date_contrast", details={"operator": operator, "literal_date": day.isoformat()})

    operations = (
        ("stock_balance", "fiches de stock", "stock balance records", "mises à jour", "updated"),
        ("stock_movement", "mouvements de stock", "stock movements", "créés", "created"),
        ("stock_receipt", "réceptions de stock", "stock receipts", "créées", "created"),
        ("stock_inventory", "inventaires", "stock inventories", "créés", "created"),
        ("logistics_order", "dossiers logistiques", "logistics orders", "créés", "created"))
    for i, (resource, fr_label, en_label, fr_verb, en_verb) in enumerate(operations):
        for j, operator in enumerate(("lower", "upper", "day")):
            day = date(2037 + j, 2 + i * 2, (4, 9, 23)[(i+j) % 3])
            args = {"resource": resource, "limit": 2 + j}
            if operator in ("lower", "day"):
                args["date_from"] = day.isoformat()
            if operator in ("upper", "day"):
                args["date_to"] = day.isoformat()
            product, location = f"SYN-Rail Chêne {81+i+j}", f"SYN-Entrepôt Est {61+i+j}"
            fr_bits, en_bits = [], []
            if (i+j) % 3 != 1:
                args["product_name"] = product
                fr_bits.append(f"pour le produit {product}")
                en_bits.append(f"for product {product}")
            if (i+j) % 3 != 0:
                args["location_name"] = location
                fr_bits.append(f"dans le dépôt {location}")
                en_bits.append(f"at location {location}")
            fr_day = f"{day.day} {MONTHS['fr'][day.month-1]} {day.year}"
            en_day = f"{day.day} {MONTHS['en'][day.month-1]} {day.year}"
            fr_date = {"lower": f"depuis le {fr_day}", "upper": f"jusqu’au {fr_day} inclus", "day": f"uniquement le {fr_day}"}[operator]
            en_date = {"lower": f"since {en_day}", "upper": f"up to and including {en_day}", "day": f"on {en_day} only"}[operator]
            add("search_operations", args,
                f"Retrouve au maximum {args['limit']} {fr_label} {fr_verb} {fr_date}, " + ", ".join(fr_bits) + ".",
                f"Return up to {args['limit']} {en_label} {en_verb} {en_date}, " + ", ".join(en_bits) + ".",
                "operation_filter_contrast", details={"operator": operator, "literal_date": day.isoformat()})

    # Explicitly distinguish the staff list from one already identified staff record.
    for i, (fr, en) in enumerate((
        ("Affiche la liste complète des utilisateurs autorisés.", "Open the list of users I can access."),
        ("Je veux la page qui regroupe les comptes utilisateurs.", "Take me to the page listing user accounts."),
        ("Reviens à la liste des comptes, pas à une fiche particulière.", "Return to the user account list, without opening a particular account."))):
        add("navigate", {"resource": "users"}, fr, en, "user_list",
            profile="staff_read", template_resource="users")
        identifier = 98113 + i * 7
        add("navigate", {"resource": "user", "identifier": identifier},
            f"Ouvre la fiche de l’utilisateur identifié {identifier} dans mes résultats.",
            f"Open the detail page for identified user {identifier} from my results.",
            "user_detail", profile="staff_read", template_resource="users",
            trusted={"previous_result_type": "user", "previous_result_count": 1,
                     "previous_result_identifiers": [identifier]})

    for i, remark in enumerate(("SYN-Contrôle technique terminé sans réserve",
                                "SYN-Delivery checked and ready for collection",
                                "SYN-Échantillon accepté par le responsable",
                                "SYN-Final inspection scheduled for Thursday")):
        identifier = 98203 + i * 11
        add("prepare_change", {"resource": "proforma", "identifier": identifier, "operation": "update",
                             "changes": {"remarque": remark}},
            f"Prépare la modification de la Remarque de la pro forma sélectionnée {identifier} : «{remark}».",
            f'Prepare the Remark change for selected pro forma {identifier} to "{remark}".',
            "verbatim_remark", profile="member_edit",
            trusted={"previous_result_type": "proforma", "previous_result_count": 1,
                     "previous_result_identifiers": [identifier]})

    for resource, fr_label, en_label in (("invoice", "facture", "invoice"), ("quote", "devis", "quote"), ("proforma", "pro forma", "pro forma")):
        add("clarify", {"reason": "missing_details"},
            f"Je veux ouvrir une {fr_label} de cette liste, mais je dois encore choisir l’élément.",
            f"I would like to open a {en_label} in this list, but I still need to select the item.",
            "unselected_record", template_tool="previous_results",
            trusted={"previous_result_type": resource, "previous_result_count": 2,
                     "previous_result_identifiers": [98461, 98403]})
    return rows


def prepare(backend, interpreter, output):
    if output.exists():
        raise ValueError("Never overwrite a versioned curriculum")
    manifest, payloads, parents = retained()
    helper_sha256 = helpers(manifest)
    for relative, expected in manifest["native_metadata"]["facturation"].items():
        if sha(backend / relative) != expected:
            raise ValueError("Reviewed native Facturation source changed")
    draft = additions(parents["train"])
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
    check_exclusions(manifest, rows)
    original_keys = {key("facturation", current_request(row)) for row in parents["train"]}
    if original_keys & {key("facturation", current_request(row)) for row in rows}:
        raise ValueError("Supplement repeats retained training")
    payloads["train.jsonl"] += encode(rows).encode()
    summary = {"version": VERSION, "applications": ["facturation"], "languages": ["en", "fr"],
        "status": "PREPARATION ONLY; no numerical training or acceptance",
        "source_manifest_sha256": PARENT_SHA, "generator_sha256": sha(Path(__file__)),
        "helper_sha256": helper_sha256, "source_validation_sha256": manifest["files"]["valid.jsonl"],
        "counts": {"train": len(parents["train"]) + len(rows), "valid": len(parents["valid"]),
                   "retained_training_rows_byte_identical": len(parents["train"]),
                   "retained_validation_rows_byte_identical": len(parents["valid"]),
                   "added": len(rows), "added_categories": dict(Counter(r["curriculum_category"] for r in rows))},
        "native_metadata": {"facturation": {**manifest["native_metadata"]["facturation"], **verified["native_sha256"]}},
        "held_out": manifest["held_out"], "historical_regression_held_out": manifest["historical_regression_held_out"],
        "fresh_controls": manifest["fresh_controls"],
        "regression_applications": ["facturation", "management_projet", "design_workflow"],
        "training_policy": "Optimize Facturation only using one shared model. Do not oversample other applications. Finish the active evaluation and bind the measured base before a bounded server rehearsal and functional comparison. Preserve other-app regressions; no automatic activation.",
        "limitations": ["Development failure categories informed this supplement; no evaluation request was copied.",
                       "Bilingual contrasts are correlated training data, not independent evaluation evidence.",
                       "Facturation-only updates may degrade other applications; regression testing remains mandatory."],
        "files": {name: hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()}}
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
