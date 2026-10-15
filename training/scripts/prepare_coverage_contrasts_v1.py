"""Prepare synthetic EN/FR coverage contrasts; never train or alter frozen splits.

The supplement is generated from verified native capabilities and existing
training templates. Development failures identify coverage categories, not rows
to copy. Frozen requests are read only to reject overlap.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from jsonschema import validate
from prepare_shared_v5r6 import select_template, function, current_request
from prepare_shared_v5r8 import context, native_check, validate_semantics, SECRET
from build_shared_v5r3 import key
from build_dialogue_v1 import encode

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "training/datasets/shared-v5r9-en-fr"
PARENT_SHA = "74fb992ed98e326ff518cdd4302f36205230c41c3b41b34515ef0c823b2763e5"
VERSION = "coverage-contrasts-v1-en-fr"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parent_rows():
    if sha(PARENT / "manifest.json") != PARENT_SHA:
        raise ValueError("Reviewed parent manifest changed")
    manifest = json.loads((PARENT / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if sha(PARENT / name) != expected:
            raise ValueError("Parent split changed")
    return manifest, list(map(json.loads, (PARENT / "train.jsonl").read_text().splitlines()))


def additions(parent):
    rows = []

    def add(app, tool, args, fr, en, category, trusted=None, template_tool=None):
        template = select_template(parent, app, template_tool or tool,
                                   args.get("resource") if not template_tool else None)
        for lang, request in (("fr", fr), ("en", en)):
            row = deepcopy(template)
            ctx = context(row)
            ctx.update(current_resource=None, current_identifier=None, current_invoice_id=None,
                       previous_result_type=None, previous_result_count=0,
                       previous_result_identifiers=[], interface_language="en" if lang == "fr" else "fr")
            ctx.pop("shortcut_search_hint", None)
            ctx.update(trusted or {})
            row["messages"][0]["content"] = row["messages"][0]["content"].split("Trusted context: ", 1)[0] + "Trusted context: " + json.dumps(ctx, ensure_ascii=False)
            target = {"name": tool, "arguments": deepcopy(args)}
            if tool == "clarify":
                target["arguments"]["language"] = lang
            greeting = "Hello" if lang == "fr" else "Bonjour"
            row["messages"] = [row["messages"][0],
                {"role": "user", "content": "Earlier user messages (background only): " + json.dumps([greeting]) + "\nCurrent request: " + request},
                {"role": "assistant", "content": None, "tool_calls": [{"type": "function", "function": target}]}]
            row.update(language=lang, curriculum_category=category)
            if app == "facturation":
                row["capability_profile"] = "member_edit"
            rows.append(row)

    # Custom periods must preserve both bounds and the requested currency.
    for currency in ("MAD", "EUR", "USD"):
        for start, end in (("2034-02-04", "2034-03-19"), ("2036-09-07", "2036-10-23")):
            for metric, fr_metric, en_metric in (
                ("invoiced_net_ttc", "montant facturé TTC après déduction des avoirs", "invoiced total including tax minus credit notes"),
                ("collected", "montant encaissé", "collected payments")):
                add("facturation", "financial_summary",
                    {"metric": metric, "period": "custom", "currency": currency, "date_from": start, "date_to": end},
                    f"Quel est le {fr_metric} en {currency}, du {start} au {end} inclus ?",
                    f"Give the {en_metric} in {currency} between {start} and {end}, inclusive.",
                    "custom_currency_summary")

    # Natural product/place phrasing, retaining native date meaning for each resource.
    operations = (
        ("stock_balance", "fiches de stock", "stock balance records", "mises à jour", "updated"),
        ("stock_movement", "mouvements de stock", "stock movements", "créés", "created"),
        ("stock_receipt", "réceptions de stock", "stock receipts", "créées", "created"),
        ("stock_inventory", "inventaires", "stock inventories", "créés", "created"),
        ("logistics_order", "dossiers logistiques", "logistics orders", "créés", "created"))
    for i, (resource, fr_label, en_label, fr_date, en_date) in enumerate(operations):
        product, location = f"SYN-PARQUET-{71+i}", f"SYN-Atelier-{91+i}"
        day = date(2034, 4 + i, 9 + i).isoformat()
        for variant in range(2):
            args = {"resource": resource, "product_name": product, "location_name": location, "date_from": day, "limit": 3}
            fr = (f"Trois {fr_label} au maximum pour {product} à {location}, {fr_date} depuis le {day}."
                  if not variant else f"À {location}, retrouve jusqu’à trois {fr_label} concernant {product}, {fr_date} à partir du {day}.")
            en = (f"Find up to three {en_label} for {product} at {location}, {en_date} since {day}."
                  if not variant else f"At {location}, show at most three {en_label} involving {product}, {en_date} on or after {day}.")
            add("facturation", "search_operations", args, fr, en, "natural_product_location")

    for resource, fr_label, en_label in (
        ("proforma", "factures pro forma", "pro forma invoices"),
        ("credit_note", "factures d’avoir", "credit notes"),
        ("delivery_note", "bons de livraison", "delivery notes")):
        for bound, fr_bound, en_bound in (
            ("date_from", "le 14 août 2035 ou après", "on or after 14 August 2035"),
            ("date_to", "le 14 août 2035 ou avant", "on or before 14 August 2035")):
            add("facturation", "search_documents",
                {"resource": resource, "client_name": "SYN-Magnolia-74", bound: "2035-08-14", "limit": 4},
                f"Retrouve au plus quatre {fr_label} du client SYN-Magnolia-74 datés {fr_bound}.",
                f"Find at most four {en_label} for customer SYN-Magnolia-74 dated {en_bound}.",
                "inclusive_document_bound")

    for index, (fr_due, en_due) in enumerate((
        ("restent à payer", "still await payment"), ("ne sont pas entièrement réglées", "are not fully paid"))):
        customer = f"SYN-Noyer-{84+index}"
        add("facturation", "search_invoices",
            {"client_name": customer, "unpaid": True, "date_from": "2035-01-16"},
            f"Quelles factures du client {customer} datées depuis le 16 janvier 2035 {fr_due} ?",
            f"Which invoices for customer {customer} dated since 16 January 2035 {en_due}?",
            "unpaid_open_interval")

    for index, remark in enumerate(("SYN-Verification finale approuvee", "SYN-Delivery review completed")):
        identifier = 97021 + index
        add("facturation", "prepare_change",
            {"resource": "proforma", "identifier": identifier, "operation": "update",
             "changes": {"remarque": remark, "date_echeance": "2035-11-17"}},
            f"Pour la pro forma {identifier} sélectionnée, mets la Remarque à {remark} et la Date d’échéance au 2035-11-17. Prépare la confirmation.",
            f"For selected pro forma {identifier}, set Remark to {remark} and Due date to 2035-11-17. Prepare confirmation.",
            "verbatim_remark", {"previous_result_type": "proforma", "previous_result_count": 1,
                                "previous_result_identifiers": [identifier]})

    for resource, status, fr_label, en_label in (
        ("task", "done", "tâches", "tasks"), ("project", "completed", "projets", "projects")):
        for fr_status, en_status in (("terminés", "completed"), ("achevés", "finished")):
            adjective = fr_status[:-1] + "es" if resource == "task" else fr_status
            add("design_workflow", "search_records", {"resource": resource, "status": status},
                f"Je voudrais retrouver les {fr_label} {adjective}.",
                f"Show the {en_status} {en_label}.", "resource_completion_status")

    for start, end in (("2034-05-08", "2034-06-21"), ("2035-10-03", "2035-11-12")):
        add("management_projet", "financial_summary",
            {"metric": "revenue", "period": "custom", "date_from": start, "date_to": end},
            f"Additionne les encaissements du {start} au {end}, pour tous les projets.",
            f"Total the receipts from {start} through {end}, across all projects.",
            "custom_receipts")

    for fr, en in (
        ("Je veux ouvrir une facture parmi les résultats, mais je dois encore choisir laquelle.",
         "I want to open an invoice from these results, but still need to choose one."),
        ("Quelle facture ouvrir parmi ces résultats ? Je n’ai pas encore fait mon choix.",
         "Which invoice should I open from these results? I have not made my choice yet.")):
        add("facturation", "clarify", {"reason": "missing_details"}, fr, en,
            "unchosen_invoice", {"previous_result_type": "invoice", "previous_result_count": 3,
                                 "previous_result_identifiers": [98051, 98029, 98084]},
            template_tool="previous_results")
    return rows


def check_exclusions(manifest, rows):
    excluded = {key(r["application"], current_request(r)) for r in
                map(json.loads, (PARENT / "valid.jsonl").read_text().splitlines())}
    files = {**manifest["held_out"], **manifest["historical_regression_held_out"]}
    for relative, proof in files.items():
        path = ROOT / relative
        if sha(path) != proof["sha256"]:
            raise ValueError("Frozen exclusion file changed")
        for row in map(json.loads, path.read_text().splitlines()):
            app = row.get("trusted_context", {}).get("application") or context(row)["application"]
            excluded.add(key(app, current_request({"messages": row["messages"] + [{}]})))
    seen = set()
    for row in rows:
        prompt = key(row["application"], current_request(row))
        if prompt in excluded or prompt in seen:
            raise ValueError("Frozen request overlap or duplicate supplement request")
        seen.add(prompt)
        target = function(row)
        schema = next(t["function"]["parameters"] for t in row["tools"] if t["function"]["name"] == target["name"])
        validate(target["arguments"], schema)
        validate_semantics(row["application"], target["name"], target["arguments"])
    if SECRET.search(encode(rows)):
        raise ValueError("Unexpected language or sensitive pattern")
    return {relative: proof["sha256"] for relative, proof in files.items()}


def prepare(backends_root, interpreters, output):
    if output.exists():
        raise ValueError("Never overwrite versioned training preparation")
    manifest, parent = parent_rows()
    draft = additions(parent)
    rows, native = [], {}
    for app in ("facturation", "management_projet", "design_workflow"):
        backend = backends_root / app / (app + "_backend")
        command = [str(interpreters[app]), "-B", str(Path(__file__).resolve()), "--native-check", app, "--backend", str(backend)]
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT / "training/scripts"), "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run(command, input=json.dumps([r for r in draft if r["application"] == app]), text=True, capture_output=True, env=env)
        if result.returncode:
            raise RuntimeError(app + " native metadata check failed: " + result.stderr[-3000:])
        value = json.loads(result.stdout)
        rows.extend(value["rows"])
        native[app] = value["native_sha256"]
    excluded = check_exclusions(manifest, rows)
    parent_keys = {key(r["application"], current_request(r)) for r in parent}
    if any(key(r["application"], current_request(r)) in parent_keys for r in rows):
        raise ValueError("Supplement repeats an existing training request")
    raw = encode(rows)
    result = {"version": VERSION, "status": "PREPARATION ONLY; supplement not trained or accepted",
        "languages": ["en", "fr"], "source_manifest_sha256": PARENT_SHA,
        "generator_sha256": sha(Path(__file__)), "native_metadata": native,
        "helper_sha256": {name: sha(ROOT / name) for name in (
            "training/scripts/prepare_shared_v5r6.py", "training/scripts/prepare_shared_v5r8.py",
            "training/scripts/prepare_shared_v5r5.py", "training/scripts/build_shared_v5r3.py",
            "training/scripts/build_dialogue_v1.py", "training/scripts/training_contracts.py",
            "training/scripts/build_dataset_v4.py", "src/chat_ai_assistant/calendar_context.py",
            "src/chat_ai_assistant/clarifications.py", "src/chat_ai_assistant/planning_messages.py",
            "src/chat_ai_assistant/contracts.py", "src/chat_ai_assistant/orchestrator.py",
            "src/chat_ai_assistant/routing.py", "src/chat_ai_assistant/selection_context.py")},
        "counts": {"train": len(rows), "by_application": dict(Counter(r["application"] for r in rows)),
                   "categories": dict(Counter(r["curriculum_category"] for r in rows))},
        "excluded_files_sha256": excluded, "files": {"train.jsonl": hashlib.sha256(raw.encode()).hexdigest()},
        "limitations": ["Coverage categories were informed by development failures. No frozen request was copied.",
                       "Correlated bilingual contrasts are not independent evaluation samples.",
                       "No validation or acceptance split is altered. Cumulative assembly and numerical rehearsal remain pending."]}
    output.mkdir()
    (output / "train.jsonl").write_text(raw)
    (output / "manifest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-check", choices=("facturation", "management_projet", "design_workflow"))
    parser.add_argument("--backend", type=Path)
    parser.add_argument("--backends-root", type=Path)
    parser.add_argument("--facturation-python", type=Path)
    parser.add_argument("--management-python", type=Path)
    parser.add_argument("--workflow-python", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "training/datasets" / VERSION)
    args = parser.parse_args()
    if args.native_check:
        print(json.dumps(native_check(args.native_check, args.backend, json.load(sys.stdin)), ensure_ascii=False))
    else:
        if not all((args.backends_root, args.facturation_python, args.management_python, args.workflow_python)):
            parser.error("Preparation requires native backend locations and interpreters")
        result = prepare(args.backends_root, {"facturation": args.facturation_python,
            "management_projet": args.management_python, "design_workflow": args.workflow_python}, args.output)
        print(json.dumps(result["counts"]))
