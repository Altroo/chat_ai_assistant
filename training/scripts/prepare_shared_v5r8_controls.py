"""Freeze new EN/FR controls before R8 training. Never optimizer/selection input.

Authored from verified capabilities, using training metadata only. These are
implementation-team controls, not a blind external certification.
"""
import argparse
from copy import deepcopy
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import prepare_shared_v5r8 as shared
from prepare_shared_v5r6 import function, current_request
from build_shared_v5r3 import key

ROOT = shared.ROOT


def scenarios():
    """Distinct compositions and phrasing; bilingual pairs stay together."""
    return [
        ("facturation", "cancelled-payments", "search_payments",
         {"client_name": "Client Fictif Albatre", "product_name": "SYN-PATINE-715", "status": "Annulé", "limit": 3},
         "Pour Client Fictif Albatre et l’article SYN-PATINE-715, je cherche trois règlements annulés.",
         "I need three cancelled payments for Client Fictif Albatre involving article SYN-PATINE-715.", {}),
        ("facturation", "archived-service", "search_articles",
         {"query": "SYN-LAQUAGE-842", "type_article": "Service", "archived": True},
         "Dans le catalogue archivé, recherche SYN-LAQUAGE-842 parmi les services, par référence ou désignation.",
         "Search the archived catalogue for SYN-LAQUAGE-842 among services, by reference or designation.", {}),
        ("facturation", "invoice-window", "search_invoices",
         {"client_name": "Client Fictif Buis", "product_name": "SYN-TRAVERSE-926", "date_from": "2022-06-09", "date_to": "2022-06-21"},
         "Les factures émises entre le 9 et le 21 juin 2022 inclus pour Client Fictif Buis, avec SYN-TRAVERSE-926 sur une ligne.",
         "Invoices issued between 9 and 21 June 2022 inclusive to Client Fictif Buis, with SYN-TRAVERSE-926 on a line.", {}),
        ("facturation", "quote-after-boundary", "search_quotes", {"date_from": "2024-03-01", "limit": 4},
         "Quatre devis au maximum, datés strictement après le 29 février 2024.",
         "No more than four quotes, dated strictly after 29 February 2024.", {}),
        ("facturation", "logistics-location", "search_operations",
         {"resource": "logistics_order", "product_name": "SYN-CORNIERE-337", "location_name": "Depot Fictif K", "date_to": "2025-11-03"},
         "Retrouve les dossiers logistiques avec SYN-CORNIERE-337 destinés à l’emplacement Depot Fictif K, au plus tard le 3 novembre 2025.",
         "Find logistics orders with SYN-CORNIERE-337 for location Depot Fictif K, no later than 3 November 2025.", {}),
        ("facturation", "unpaid-customer", "search_invoices", {"client_name": "Client Fictif Bruyere", "unpaid": True, "limit": 3},
         "Trois factures restant à payer par Client Fictif Bruyere, s’il te plaît.",
         "Three invoices still awaiting payment from Client Fictif Bruyere, please.", {}),
        ("facturation", "literal-invoice-edit", "prepare_change",
         {"resource": "invoice", "identifier": 81037, "operation": "update",
          "changes": {"remarque": "SYN-Dossier relu, accord a confirmer.", "termes_paiement": "SYN-Paiement sous 45 jours."}},
         "Modifie la facture ID 81037 : Remarque « SYN-Dossier relu, accord a confirmer. » et Conditions de paiement « SYN-Paiement sous 45 jours. ».",
         "Update invoice ID 81037: Remark “SYN-Dossier relu, accord a confirmer.” and Payment terms “SYN-Paiement sous 45 jours.”.",
         {"current_invoice_id": 81037}),
        ("facturation", "missing-year", "clarify", {"reason": "missing_details"},
         "Je cherche les factures de novembre, mais je ne sais plus de quelle année.",
         "I am looking for the November invoices, but I do not remember which year.", {}),
        ("management_projet", "supplier-quote-cutoff", "search_records",
         {"resource": "quote", "supplier_name": "Fournisseur Fictif Jasmin", "date_to": "2024-02-28"},
         "Retrouve les devis du fournisseur Fournisseur Fictif Jasmin antérieurs au 29 février 2024.",
         "Retrieve quotes from supplier Fournisseur Fictif Jasmin earlier than 29 February 2024.", {}),
        ("management_projet", "project-expenses", "financial_summary",
         {"metric": "expenses", "period": "previous_month", "project_name": "Projet Fictif Promenade"},
         "Pour Projet Fictif Promenade, quel est le total des dépenses du mois dernier ?",
         "For Projet Fictif Promenade, what is the total expense amount for last month?", {}),
        ("management_projet", "supplier-revenue-total", "clarify", {"reason": "unsupported"},
         "Calcule les encaissements totaux uniquement pour le fournisseur Fournisseur Fictif Pierre.",
         "Calculate total receipts exclusively for supplier Fournisseur Fictif Pierre.", {}),
        ("management_projet", "missing-fourth-customer", "clarify", {"reason": "missing_details"},
         "Modifie le quatrième client trouvé : Téléphone « 0500000777 » et Ville « Ouarzazate ».",
         "Update the fourth customer found: Phone “0500000777” and City “Ouarzazate”.",
         {"previous_result_type": "client", "previous_result_count": 3, "previous_result_identifiers": [83017, 83092, 83046]}),
        ("management_projet", "current-project-pdf", "project_report", {"identifier": 82063},
         "J’ai besoin du PDF du projet que je consulte actuellement.",
         "I need the PDF of the project I am currently viewing.",
         {"current_resource": "project", "current_identifier": 82063}),
        ("management_projet", "expense-range", "search_records",
         {"resource": "expense", "project_name": "Projet Fictif Rivage", "date_from": "2023-12-28", "date_to": "2024-01-05", "limit": 2},
         "Seulement deux dépenses de Projet Fictif Rivage, du 28 décembre 2023 au 5 janvier 2024 inclus.",
         "Only two expenses for Projet Fictif Rivage, from 28 December 2023 through 5 January 2024.", {}),
        ("management_projet", "read-only-change", "clarify", {"reason": "unsupported"},
         "Modifie la ville du client affiché en « Khouribga ».",
         "Change the displayed customer’s City to “Khouribga”.",
         {"capabilities": ["read"], "current_resource": "client", "current_identifier": 84039}),
        ("management_projet", "expenses-navigation", "navigate", {"resource": "expenses"},
         "Quitte cette fiche et ouvre la liste des dépenses.",
         "Leave this record and open the expenses list.", {}),
        ("design_workflow", "done-assignee", "search_records",
         {"resource": "task", "status": "done", "project_name": "Projet Fictif Esquisse", "assignee_name": "Demo Ines"},
         "Quelles tâches terminées du projet Projet Fictif Esquisse sont assignées à Demo Ines ?",
         "Which completed tasks in project Projet Fictif Esquisse are assigned to Demo Ines?", {}),
        ("design_workflow", "task-two-fields", "prepare_change",
         {"resource": "task", "identifier": 85071, "operation": "update", "changes": {"priority": "medium", "title": "SYN-Revoir la coupe du hall"}},
         "Sur la tâche affichée, modifie la priorité en moyenne et le titre en « SYN-Revoir la coupe du hall ».",
         "For the displayed task, set Priority to medium and Title to “SYN-Revoir la coupe du hall”.",
         {"current_resource": "task", "current_identifier": 85071}),
        ("design_workflow", "project-priority-date", "prepare_change",
         {"resource": "project", "identifier": 85082, "operation": "update", "changes": {"priority": "low", "target_end_date": "2029-10-17"}},
         "Modifie le projet affiché : priorité basse et date cible au 17 octobre 2029.",
         "Update the displayed project: low Priority and Target date 17 October 2029.",
         {"current_resource": "project", "current_identifier": 85082}),
        ("design_workflow", "permanent-delete", "clarify", {"reason": "unsupported"},
         "Efface définitivement le projet affiché, je ne veux pas l’archiver.",
         "Permanently delete the displayed project; I do not want to archive it.",
         {"current_resource": "project", "current_identifier": 85096}),
        ("design_workflow", "third-result", "previous_results", {"operation": "open", "index": 3},
         "Ouvre la tâche en troisième position dans les résultats.",
         "Open the task in third position in the results.",
         {"previous_result_type": "task", "previous_result_count": 4, "previous_result_identifiers": [86034, 86098, 86042, 86073]}),
        ("design_workflow", "leap-month-time", "time_report",
         {"project_name": "Projet Fictif Verriere", "date_from": "2024-02-01", "date_to": "2024-02-29"},
         "Affiche le temps de travail du projet Projet Fictif Verriere pour février 2024.",
         "Show working time for Projet Fictif Verriere for February 2024.", {}),
        ("design_workflow", "archived-project", "search_records", {"resource": "project", "project_name": "Projet Fictif Cour", "archived": True},
         "Recherche le projet archivé nommé Projet Fictif Cour.",
         "Find the archived project named Projet Fictif Cour.", {}),
        ("design_workflow", "read-only-priority", "clarify", {"reason": "unsupported"},
         "Mets la priorité de la tâche affichée à urgente.",
         "Set the displayed task Priority to urgent.",
         {"capabilities": ["read"], "current_resource": "task", "current_identifier": 87016}),
    ]


def prepare(backends_root, interpreters, output=None):
    output = output or ROOT / "training/datasets/shared-v5r8-fresh-en-fr"
    if output.exists():
        raise ValueError("Never overwrite frozen controls")
    parent = ROOT / "training/datasets/shared-v5r7-en-fr"
    assert shared.sha(parent / "manifest.json") == shared.PARENT_HASH
    parent_manifest = json.loads((parent / "manifest.json").read_text())
    assert shared.sha(parent / "train.jsonl") == parent_manifest["files"]["train.jsonl"]
    templates = list(map(json.loads, (parent / "train.jsonl").read_text().splitlines()))
    native_inputs = []
    for app, label, tool, args, fr, en, overrides in scenarios():
        template = next(r for r in templates if r["application"] == app)
        for language, prompt in (("fr", fr), ("en", en)):
            row = deepcopy(template)
            trusted = shared.context(row)
            trusted.update(current_resource=None, current_identifier=None, current_invoice_id=None,
                previous_result_type=None, previous_result_count=0, previous_result_identifiers=[],
                interface_language="en" if language == "fr" else "fr",
                capabilities=["read", "print", "create", "update", "delete"] if app == "management_projet" else ["read", "create", "update", "archive", "mutate", "report"])
            trusted.pop("shortcut_search_hint", None)
            trusted.update(overrides)
            if app == "facturation":
                trusted.pop("capabilities", None)
            arguments = {**args, **({"language": language} if tool == "clarify" else {})}
            row.update(application=app, language=language, control_id="r8-fresh-" + app + "-" + label + "-" + language,
                       curriculum_category=label, capability_profile="member_edit")
            row["messages"] = [{"role": "system", "content": row["messages"][0]["content"].split("Trusted context: ", 1)[0] +
                "Trusted context: " + json.dumps(trusted, ensure_ascii=False)}, {"role": "user", "content": prompt},
                {"role": "assistant", "content": None, "tool_calls": [{"type": "function", "function": {"name": tool, "arguments": arguments}}]}]
            native_inputs.append(row)
    verified, proofs = [], {}
    for app, interpreter in interpreters.items():
        backend = backends_root / app / (app + "_backend")
        proc = subprocess.run([str(interpreter), "-B", str(ROOT / "training/scripts/prepare_shared_v5r8.py"),
            "--native-check", app, "--backend", str(backend)], input=json.dumps([r for r in native_inputs if r["application"] == app]),
            text=True, capture_output=True, env={**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT / "training/scripts"),
            "PYTHONDONTWRITEBYTECODE": "1"}, check=True)
        value = json.loads(proc.stdout)
        verified.extend(value["rows"]); proofs[app] = value["native_sha256"]
    excluded = set()
    for version in ("shared-v5r7-en-fr", "shared-v5r8-en-fr"):
        folder = ROOT / "training/datasets" / version
        manifest = json.loads((folder / "manifest.json").read_text())
        for split in ("train.jsonl", "valid.jsonl"):
            assert shared.sha(folder / split) == manifest["files"][split]
            for row in map(json.loads, (folder / split).read_text().splitlines()):
                excluded.add(key(row["application"], current_request(row)))
    for version, binding in (("shared-dialogue-v1-en-fr", "historical_evaluation_manifest_sha256"),
                             ("shared-dialogue-v2-en-fr", "evaluation_manifest_sha256")):
        folder = ROOT / "training/datasets" / version
        assert shared.sha(folder / "manifest.json") == parent_manifest[binding]
        manifest = json.loads((folder / "manifest.json").read_text())
        for name in manifest["inputs"]:
            assert shared.sha(folder / name) == manifest["files"][name]
            for row in map(json.loads, (folder / name).read_text().splitlines()):
                excluded.add(key(shared.context(row)["application"], current_request({"messages": row["messages"] + [{}]})))
    snapshots = []
    for row in verified:
        assert key(row["application"], current_request(row)) not in excluded
        f = function(row)
        tools = [t for t in row["tools"] if t["function"]["name"] != "clarify"]
        snapshots.append({"id": row["control_id"], "category": row["curriculum_category"], "language": row["language"],
            "messages": row["messages"][:-1], "expected": {"tool": f["name"], "arguments": f["arguments"]},
            "trusted_context": shared.context(row), "offered_tool_schemas": tools,
            "offered_tools": [t["function"]["name"] for t in tools]})
    assert len(snapshots) == len({r["id"] for r in snapshots}) == 48
    payload = shared.encode(snapshots)
    assert not shared.SECRET.search(payload)
    output.mkdir()
    (output / "controls.eval.jsonl").write_text(payload)
    manifest = {"version": output.name, "count": len(snapshots), "languages": ["en", "fr"],
        "applications": ["facturation", "management_projet", "design_workflow"],
        "generator_sha256": shared.sha(Path(__file__)), "native_checker_sha256": shared.sha(ROOT / "training/scripts/prepare_shared_v5r8.py"),
        "training_manifest_sha256": shared.sha(ROOT / "training/datasets/shared-v5r8-en-fr/manifest.json"),
        "source_training_manifest_sha256": shared.PARENT_HASH, "native_metadata": proofs,
        "by_application": dict(Counter(r["trusted_context"]["application"] for r in snapshots)),
        "files": {"controls.eval.jsonl": hashlib.sha256(payload.encode()).hexdigest()},
        "policy": "Frozen before any R8 baseline or optimization. Never training or checkpoint-selection input. Original 438 regressions remain unchanged and reported separately. Native metadata with database access prohibited. New implementation-team scenarios, not blind external certification. Bilingual pairs share scenarios; semantic overlap with trained capabilities is expected. No model accuracy has yet been measured."}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backends-root", type=Path, required=True)
    parser.add_argument("--facturation-python", type=Path, required=True)
    parser.add_argument("--management-python", type=Path, required=True)
    parser.add_argument("--workflow-python", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.backends_root, {"facturation": args.facturation_python, "management_projet": args.management_python,
                                         "design_workflow": args.workflow_python})
    print(json.dumps({k: result[k] for k in ("count", "by_application")}))
