"""Append native-verified EN/FR coverage; retain every R7 training/validation byte.

Uses only prior TRAINING templates and verified application metadata. Frozen
regression prompts are read only for exclusion, never to generate labels.
No model weights, production data or optimizer are accessed by this command.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import re
import sys
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
from prepare_shared_v5r6 import function, select_template, current_request, FACT_DATES, MONTHS
from build_shared_v5r3 import key
from build_dialogue_v1 import encode
from prepare_shared_v5r5 import ARMS

PARENT_HASH = "d947026043133fbedc6afb7b21bd9a2a8feb32e8150ad3cf48fc0670f90987ec"
SECRET = re.compile(r"[\u0600-\u06ff]|BEGIN.{0,12}PRIVATE KEY|Bearer\s+\S+|(?:password|api_key|secret)\s*[:=]", re.I)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def context(row):
    return json.loads(row["messages"][0]["content"].split("Trusted context: ", 1)[1])


def additions(parent):
    result = []

    def add(app, tool, args, fr, en, category, ctx=None, template_tool=None, template_resource=None):
        resource = args.get("resource")
        source_tool = template_tool or tool
        source_resource = resource if template_resource is None else template_resource
        template = select_template(parent, app, source_tool, source_resource)
        for language, prompt in (("fr", fr), ("en", en)):
            row = deepcopy(template)
            trusted = context(row)
            trusted.update(current_resource=None, current_identifier=None, current_invoice_id=None,
                           previous_result_type=None, previous_result_count=0, previous_result_identifiers=[],
                           interface_language="en" if language == "fr" else "fr")
            trusted.pop("shortcut_search_hint", None)
            trusted.update(ctx or {})
            row["messages"][0]["content"] = row["messages"][0]["content"].split("Trusted context: ", 1)[0] + "Trusted context: " + json.dumps(trusted, ensure_ascii=False)
            target = {"name": tool, "arguments": deepcopy(args)}
            if tool == "clarify":
                target["arguments"]["language"] = language
            greeting = ARMS[int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16) % len(ARMS)]
            row["messages"] = [row["messages"][0], {"role": "user", "content":
                ("Earlier user messages (background only): " + json.dumps([greeting], ensure_ascii=False) +
                "\nCurrent request: " if greeting else "") + prompt},
                {"role": "assistant", "content": None, "tool_calls": [{"type": "function", "function": target}]}]
            row.update(language=language, curriculum_category=category)
            if app == "facturation":
                row["capability_profile"] = "staff_edit" if tool == "search_users" else "member_edit"
            result.append(row)

    # Compound filters with distinct lower/upper/exclusive/single-day semantics.
    # Calendar arithmetic determines labels, not previously failed evaluations.
    for index, (tool, resource, en_label, fr_label) in enumerate(FACT_DATES):
        customer = f"SYN-Lentisque-{index+21}"
        product = f"SYN-EQUERRE-{index+31}"
        location = f"SYN-Entrepot-{index+41}"
        day = (date(2032, 3, 1), date(2033, 1, 1), date(2032, 2, 29), date(2033, 4, 30))[index] if index < 4 else date(2031 + index % 3, 1 + (index * 7) % 12, 8 + index)
        for mode in ("since", "through", "before", "after", "day"):
            args = {"resource": resource} if resource else {}
            limit = 2 + index % 3
            args["limit"] = limit
            if tool in ("search_invoices", "search_quotes", "search_documents", "search_payments"):
                args.update(client_name=customer, product_name=product)
                fr_filter = f"pour le client {customer}, avec l’article {product}"
                en_filter = f"for customer {customer}, containing article {product}"
                if tool == "search_invoices":
                    args["unpaid"] = True
                    fr_filter += ", dont le solde reste impayé"
                    en_filter += ", with an unpaid balance"
            elif tool == "search_operations":
                args.update(product_name=product, location_name=location)
                fr_filter = f"avec l’article {product}, à l’emplacement {location}"
                en_filter = f"for article {product}, at location {location}"
            elif tool == "search_articles":
                args.update(query=product, type_article="Service")
                fr_filter = f"de type Service, dont la référence ou la désignation contient {product}"
                en_filter = f"of type Service, with {product} in their reference or designation"
            else:
                args["name"] = "SYN-Amelie Exemple"
                fr_filter = "au nom de SYN-Amelie Exemple"
                en_filter = "named SYN-Amelie Exemple"
            if mode in ("since", "day"):
                args["date_from"] = day.isoformat()
            if mode in ("through", "day"):
                args["date_to"] = day.isoformat()
            if mode == "before":
                args["date_to"] = (day - timedelta(days=1)).isoformat()
            if mode == "after":
                args["date_from"] = (day + timedelta(days=1)).isoformat()
            fr_date = f"{day.day} {MONTHS['fr'][day.month-1]} {day.year}"
            en_date = f"{day.day} {MONTHS['en'][day.month-1]} {day.year}"
            fr_bound = {"since": f"depuis le {fr_date} inclus, sans date de fin",
                        "through": f"jusqu’au {fr_date} inclus, sans date de début",
                        "before": f"strictement avant le {fr_date}",
                        "after": f"strictement après le {fr_date}",
                        "day": f"uniquement à la date du {fr_date}"}[mode]
            en_bound = {"since": f"from {en_date} inclusive, with no end date",
                        "through": f"up to {en_date} inclusive, with no start date",
                        "before": f"strictly before {en_date}",
                        "after": f"strictly after {en_date}",
                        "day": f"only on {en_date}"}[mode]
            add("facturation", tool, args,
                f"Recherche {limit} {fr_label} maximum {fr_filter}, datés {fr_bound}.",
                f"Search for at most {limit} {en_label} {en_filter}, dated {en_bound}.",
                "compound_date_" + mode)

    # Discover records from descriptions before proposing any mutation.
    for i, (tool, resource, fr_label, en_label) in enumerate((
        ("search_invoices", None, "factures", "invoices"),
        ("search_quotes", None, "devis", "quotes"),
        ("search_documents", "proforma", "factures pro forma", "pro forma invoices"),
        ("search_documents", "credit_note", "factures d’avoir", "credit notes"),
        ("search_documents", "delivery_note", "bons de livraison", "delivery notes"),
    )):
        customer, product = f"SYN-Neflier-{51+i}", f"SYN-TASSEAU-{61+i}"
        args = {"client_name": customer, "product_name": product}
        if resource:
            args["resource"] = resource
        for prefix, en_prefix in (("/voir", "/view"), ("/modifier", "/edit"), ("/supprimer", "/delete")):
            add("facturation", tool, args,
                f"{prefix} les {fr_label} du client {customer} contenant {product} ; je dois choisir le document.",
                f"{en_prefix} the {en_label} for customer {customer} containing {product}; I still need to choose the document.",
                "descriptive_shortcut")

    # Supplier-specific aggregates are unsupported by the actual MP summary tool.
    # Contrasts distinguish supported item searches and project summaries.
    for i, (metric, resource, fr_label, en_label) in enumerate((
        ("expenses", "expense", "dépenses", "expenses"),
        ("estimates", "quote", "devis", "quotes"),
    )):
        supplier = f"Fournisseur Synthese-{81+i}"
        project = f"Projet Synthese-{91+i}"
        for period, fr_period, en_period in (("previous_month", "du mois dernier", "from last month"),
                                            ("current_year", "de cette année", "from this year")):
            add("management_projet", "clarify", {"reason": "unsupported"},
                f"Calcule la somme des {fr_label} {fr_period} uniquement pour le fournisseur {supplier}.",
                f"Calculate the sum of {en_label} {en_period} for supplier {supplier} only.",
                "unsupported_supplier_total", template_tool="search_records", template_resource=resource)
            if metric == "expenses":
                add("management_projet", "financial_summary", {"metric": metric, "period": period, "project_name": project},
                    f"Calcule le total des {fr_label} {fr_period} pour le projet {project}.",
                    f"Calculate total {en_label} {en_period} for project {project}.",
                    "supported_project_total")
            else:
                add("management_projet", "clarify", {"reason": "unsupported"},
                    f"Calcule le total des {fr_label} {fr_period} pour le projet {project}.",
                    f"Calculate total {en_label} {en_period} for project {project}.",
                    "unsupported_dated_estimate", template_tool="financial_summary")
        if metric == "estimates":
            add("management_projet", "financial_summary", {"metric": "estimates", "project_name": project},
                f"Quel est le montant estimé total du projet {project}, toutes dates confondues ?",
                f"What is the all-time total estimated amount for project {project}?",
                "supported_estimate_total")
        add("management_projet", "search_records", {"resource": resource, "supplier_name": supplier, "limit": 4},
            f"Affiche quatre {fr_label} du fournisseur {supplier}, sans faire de total.",
            f"Show four {en_label} from supplier {supplier}, without calculating a total.",
            "supplier_records_not_total")
    for metric, fr_label, en_label in (("service_fees", "frais de service", "service fees"),
                                      ("profit", "bénéfices", "profit")):
        add("management_projet", "financial_summary",
            {"metric": metric, "period": "previous_year", "project_name": "Projet Synthese-Grenat"},
            f"Le projet Projet Synthese-Grenat : total des {fr_label} de l’année précédente.",
            f"For Projet Synthese-Grenat, give the total {en_label} for the preceding year.",
            "previous_year_metric")

    # Every ordinal position is contrasted against shuffled, non-sequential IDs.
    # Two requested fields and an optional distracting current page are included.
    ordinals = (("premier", "first"), ("deuxième", "second"), ("troisième", "third"),
                ("quatrième", "fourth"), ("cinquième", "fifth"))
    for position, (fr_ord, en_ord) in enumerate(ordinals):
        ids = [73015, 42068, 89023, 51094, 26037]
        ids = ids[position:] + ids[:position]
        address = f"SYN-Impasse des Artisans {120+position}, étage 2"
        city = ("Azrou", "Berkane", "Sefrou", "Tiznit", "Asilah")[position]
        ctx = {"previous_result_type": "client", "previous_result_count": len(ids), "previous_result_identifiers": ids}
        for current in (False, True):
            used = {**ctx, **({"current_resource": "project", "current_identifier": 99081} if current else {})}
            add("management_projet", "prepare_change",
                {"resource": "client", "identifier": ids[position], "operation": "update",
                 "changes": {"adresse": address, "ville": city}},
                f"Dans la sélection de clients, modifie le {fr_ord} : Adresse « {address} », Ville « {city} ».",
                f"In the customer selection, update the {en_ord}: Address “{address}”, City “{city}”.",
                "ordinal_multifield_with_page" if current else "ordinal_multifield", used)
        add("management_projet", "clarify", {"reason": "missing_details"},
            f"Dans la sélection de clients, modifie le {fr_ord} : Adresse « {address} », Ville « {city} ».",
            f"In the customer selection, update the {en_ord}: Address “{address}”, City “{city}”.",
            "ordinal_out_of_range", {"previous_result_type": "client" if position else None,
                "previous_result_count": position, "previous_result_identifiers": ids[:position]},
            template_tool="prepare_change", template_resource="client")

    # Native Priority values are low/medium/high/urgent, on projects AND tasks.
    for r_index, (resource, fr_resource, en_resource, title_key, fr_title, en_title) in enumerate((
        ("project", "projet", "project", "name", "Nom", "Name"),
        ("task", "tâche", "task", "title", "Titre", "Title"),
    )):
        for i, (priority, fr_priority) in enumerate((("low", "basse"), ("medium", "moyenne"),
                                                    ("high", "haute"), ("urgent", "urgente"))):
            identifier = 71001 + 10*r_index + i
            value = f"SYN-Relecture des plans - lot {200+10*r_index+i}"
            for multifield in (False, True):
                changes = {"priority": priority}
                fr_extra = f" et {fr_title} en « {value} »" if multifield else ""
                en_extra = f" and {en_title} to “{value}”" if multifield else ""
                if multifield:
                    changes[title_key] = value
                add("design_workflow", "prepare_change",
                    {"resource": resource, "identifier": identifier, "operation": "update", "changes": changes},
                    f"Modifie la priorité du document {fr_resource} ID {identifier} en {fr_priority}{fr_extra}.",
                    f"Update {en_resource} ID {identifier}: Priority to {priority}{en_extra}.",
                    "priority_and_literal" if multifield else "priority_enum",
                    {"current_resource": resource, "current_identifier": identifier})

    # Literal copying includes multiple words, punctuation and two editable fields.
    for i, (resource, fr_resource, en_resource) in enumerate((
        ("quote", "devis", "quote"), ("proforma", "facture pro forma", "pro forma invoice"),
        ("delivery_note", "bon de livraison", "delivery note"),
    )):
        identifier = 72080+i
        for quoted in (True, False):
            value = f"SYN-Revision du dossier terminee {300+i}"
            due = f"2034-09-{12+i}"
            fr_value = f"« {value} »" if quoted else value
            en_value = f"“{value}”" if quoted else value
            add("facturation", "prepare_change",
                {"resource": resource, "identifier": identifier, "operation": "update",
                 "changes": {"remarque": value, "date_echeance": due}},
                f"Pour le document {fr_resource} ID {identifier}, modifie Remarque en {fr_value} et Date d’échéance au {due}.",
                f"For {en_resource} ID {identifier}, update Remark to {en_value} and Due date to {due}.",
                "literal_multifield_quoted" if quoted else "literal_multifield_unquoted")

    # Current page references and explicitly unchosen selections.
    for app, resource, fr_resource, en_resource in (
        ("management_projet", "payment_schedule", "échéance de paiement", "payment schedule"),
        ("management_projet", "expense", "dépense", "expense"),
        ("design_workflow", "project", "projet", "project"),
        ("design_workflow", "task", "tâche", "task"),
    ):
        add(app, "get_record", {"resource": resource},
            f"Je parle de la fiche {fr_resource} affichée : donne-moi ses détails.",
            f"I mean the {en_resource} record displayed on this page: give me its details.",
            "current_page_reference", {"current_resource": resource, "current_identifier": 74001})
    for app, resource in (("facturation", "invoice"), ("management_projet", "client"), ("design_workflow", "task")):
        add(app, "clarify", {"reason": "missing_details"},
            "Ouvre un résultat, mais je n’ai pas encore décidé lequel.",
            "Open a result, but I have not decided which one yet.",
            "unselected_navigation",
            {"previous_result_type": resource, "previous_result_count": 3, "previous_result_identifiers": [76008, 76003, 76091]},
            template_tool="previous_results", template_resource=None)
    return result


def validate_semantics(application, tool, args):
    """Pure financial constraints verified against MP native financial_summary."""
    if application == "management_projet" and tool == "financial_summary":
        metric, period = args["metric"], args.get("period", "all_time")
        if metric in ("budget", "estimates") and period != "all_time":
            raise ValueError("Native budget/estimates has no period filtering")
        if metric == "estimates" and not (args.get("project_name") or args.get("project_id")):
            raise ValueError("Native estimates requires one project")
        if period == "custom":
            if not (args.get("date_from") and args.get("date_to")):
                raise ValueError("Custom period requires both dates")
        elif args.get("date_from") or args.get("date_to"):
            raise ValueError("Date bounds require custom period")
    for name in ("date_from", "date_to"):
        if name in args:
            date.fromisoformat(args[name])
    if args.get("date_from") and args.get("date_to") and args["date_from"] > args["date_to"]:
        raise ValueError("Reversed date bounds")


def native_check(application, backend, rows):
    """Use actual permission shortlist and schema. Fail closed on any DB access."""
    import os
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(backend))
    os.environ["DJANGO_SETTINGS_MODULE"] = application + "_backend." + (
        "settings_test" if application == "design_workflow" else "settings_ai_test")
    from django.db.backends.base.base import BaseDatabaseWrapper
    def forbidden(*args, **kwargs):
        raise RuntimeError("Native metadata check must not query a database")
    BaseDatabaseWrapper.ensure_connection = forbidden
    import django
    django.setup()
    from chat_ai.tools import registry
    import chat_ai.tools
    from chat_ai_assistant.clarifications import CLARIFICATION_SCHEMA
    from training_contracts import CLARIFICATION_DESCRIPTION
    from chat_ai_assistant.calendar_context import with_calendar_context
    if application == "facturation":
        from chat_ai_assistant.orchestrator import SYSTEM
        from chat_ai_assistant.routing import shortlist
        from chat_ai.shortcut_catalog import shortcut_search_hint
        from build_dataset_v4 import PROFILES, validate_business_action
    else:
        from chat_ai.planner import SYSTEM, shortlist
    output = []
    for source in rows:
        row = deepcopy(source)
        trusted = context(row)
        request = current_request(row)
        caps = PROFILES[row["capability_profile"]] if application == "facturation" else trusted["capabilities"]
        if application == "facturation":
            hint = shortcut_search_hint(request)
            if hint != request:
                trusted["shortcut_search_hint"] = hint
        trusted = with_calendar_context(trusted)
        selected = shortlist(trusted.get("shortcut_search_hint") or request, registry().permitted(set(caps)), trusted)
        row["tools"] = [t.schema() for t in selected] + [{"type": "function", "function": {
            "name": "clarify", "description": CLARIFICATION_DESCRIPTION, "parameters": CLARIFICATION_SCHEMA}}]
        row["messages"][0]["content"] = SYSTEM + "\nTrusted context: " + json.dumps(trusted, ensure_ascii=False)
        target = function(row)
        schema = next((t["function"]["parameters"] for t in row["tools"] if t["function"]["name"] == target["name"]), None)
        if schema is None:
            raise ValueError("Native shortlist excludes target: " + request)
        validate(target["arguments"], schema)
        if application == "facturation":
            validate_business_action(target["name"], target["arguments"], trusted, request)
        validate_semantics(application, target["name"], target["arguments"])
        if application == "design_workflow" and target["name"] == "search_records":
            from chat_ai.resources import RESOURCES
            args = target["arguments"]
            if args.get("status"):
                field = RESOURCES[args["resource"]].model._meta.get_field("status")
                assert args["status"] in dict(field.choices)
        if target["name"] == "prepare_change" and application != "facturation":
            from chat_ai.resources import RESOURCES
            args = target["arguments"]
            assert set(args.get("changes", {})) <= set(RESOURCES[args["resource"]].editable)
            if application == "management_projet":
                from chat_ai.targets import trusted_target
                from datetime import datetime, timezone
                now = datetime(2035, 1, 1, tzinfo=timezone.utc)
                state = {"resource": trusted["previous_result_type"], "ids": trusted["previous_result_identifiers"],
                         "expires_at": "2035-01-02T00:00:00+00:00"}
                assert trusted_target(args["resource"], args["identifier"], instruction=request,
                    context={"resource": trusted["current_resource"], "identifier": trusted["current_identifier"]},
                    state=state, now=now), request
            if application == "design_workflow" and "priority" in args.get("changes", {}):
                field = RESOURCES[args["resource"]].model._meta.get_field("priority")
                assert args["changes"]["priority"] in dict(field.choices)
        output.append(row)
    native = Path(chat_ai.tools.__file__).parent
    files = [p for p in native.glob("*.py")]
    if application == "design_workflow":
        files.append(backend / "design_workflow/models.py")
    return {"rows": output, "native_sha256": {str(p.relative_to(backend)): sha(p) for p in files}}


def assemble(parent_dir, extra, native_proof):
    manifest = json.loads((parent_dir / "manifest.json").read_text())
    assert sha(parent_dir / "manifest.json") == PARENT_HASH
    for name in ("train.jsonl", "valid.jsonl"):
        assert sha(parent_dir / name) == manifest["files"][name]
    raw = (parent_dir / "train.jsonl").read_text()
    original = list(map(json.loads, raw.splitlines()))
    valid = list(map(json.loads, (parent_dir / "valid.jsonl").read_text().splitlines()))
    excluded = {key(r["application"], current_request(r)) for r in valid}
    for version in ("shared-dialogue-v1-en-fr", "shared-dialogue-v2-en-fr"):
        folder = ROOT / "training/datasets" / version
        expected_manifest = manifest["historical_evaluation_manifest_sha256" if version.endswith("v1-en-fr") else "evaluation_manifest_sha256"]
        assert sha(folder / "manifest.json") == expected_manifest, "Frozen exclusion manifest changed"
        frozen = json.loads((folder / "manifest.json").read_text())
        for name in frozen["inputs"]:
            assert sha(folder / name) == frozen["files"][name]
            for row in map(json.loads, (folder / name).read_text().splitlines()):
                app = context(row)["application"]
                excluded.add(key(app, current_request({"messages": row["messages"] + [{}]})))
    prior_inputs = {json.dumps({"messages": r["messages"][:-1], "tools": r["tools"]}, sort_keys=True) for r in original}
    extra_inputs = [json.dumps({"messages": r["messages"][:-1], "tools": r["tools"]}, sort_keys=True) for r in extra]
    assert len(extra_inputs) == len(set(extra_inputs)) and not prior_inputs.intersection(extra_inputs)
    assert not any(key(r["application"], current_request(r)) in excluded for r in extra)
    for row in extra:
        target = function(row)
        schema = next(t["function"]["parameters"] for t in row["tools"] if t["function"]["name"] == target["name"])
        validate(target["arguments"], schema)
    payloads = {"train.jsonl": raw + encode(extra), "valid.jsonl": (parent_dir / "valid.jsonl").read_text()}
    assert not SECRET.search("".join(payloads.values()))
    info = {**manifest, "version": "shared-v5r8-en-fr", "status": "PREPARED ONLY; not trained or evaluated",
        "parent_manifest_sha256": PARENT_HASH, "generator_sha256": sha(Path(__file__)),
        "native_metadata": native_proof,
        "helper_sha256": {name: sha(ROOT / name) for name in (
            "training/scripts/prepare_shared_v5r6.py", "training/scripts/prepare_shared_v5r5.py",
            "training/scripts/build_shared_v5r3.py", "training/scripts/build_dialogue_v1.py",
            "training/scripts/training_contracts.py", "training/scripts/build_dataset_v4.py",
            "src/chat_ai_assistant/calendar_context.py", "src/chat_ai_assistant/clarifications.py",
            "src/chat_ai_assistant/planning_messages.py", "src/chat_ai_assistant/contracts.py",
            "src/chat_ai_assistant/orchestrator.py", "src/chat_ai_assistant/routing.py",
            "src/chat_ai_assistant/selection_context.py")},
        "counts": {"train": len(original)+len(extra), "valid": len(valid),
            "retained_parent_rows_byte_identical": len(original), "added": len(extra),
            "by_application": dict(Counter(r["application"] for r in original+extra)),
            "added_categories": dict(Counter(r["curriculum_category"] for r in extra))},
        "training_policy": "Retain all R7 rows and validation bytes. Append native-verified synthetic coverage for compound filters, date boundaries, unsupported supplier aggregates, saved selection and all priority values. No held-out target creates a training row. Correlated bilingual/template/context variants are not independent samples. Server-only continuation, no automatic activation.",
        "limitations": ["Original frozen evaluations are regressions after repeated development use, not unseen certification.",
            "Exact request exclusion does not establish exhaustive semantic independence.",
            "Native-equivalent article query/product_name aliases remain subject to the unchanged exact-argument scorer. No historical score was changed."]}
    info["files"] = {name: hashlib.sha256(payload.encode()).hexdigest() for name,payload in payloads.items()}
    return payloads, info


def prepare(backends_root, interpreters, output=None):
    import os
    import subprocess
    output = output or ROOT / "training/datasets/shared-v5r8-en-fr"
    if output.exists():
        raise ValueError("Never overwrite a versioned preparation")
    parent = ROOT / "training/datasets/shared-v5r7-en-fr"
    assert sha(parent / "manifest.json") == PARENT_HASH
    original = list(map(json.loads, (parent / "train.jsonl").read_text().splitlines()))
    draft = additions(original)
    extra, proofs = [], {}
    for app in ("facturation", "management_projet", "design_workflow"):
        backend = backends_root / app / (app + "_backend")
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT / "training/scripts"),
               "PYTHONDONTWRITEBYTECODE": "1"}
        proc = subprocess.run([str(interpreters[app]), "-B", str(Path(__file__).resolve()),
            "--native-check", app, "--backend", str(backend)],
            input=json.dumps([r for r in draft if r["application"] == app]), text=True,
            capture_output=True, env=env, check=True)
        value = json.loads(proc.stdout)
        extra.extend(value["rows"])
        proofs[app] = value["native_sha256"]
    payloads, manifest = assemble(parent, extra, proofs)
    manifest["version"] = output.name
    output.mkdir()
    for name, payload in payloads.items():
        with (output / name).open("x") as stream:
            stream.write(payload)
    with (output / "manifest.json").open("x") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-check", choices=("facturation", "management_projet", "design_workflow"))
    parser.add_argument("--backend", type=Path)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--backends-root", type=Path)
    parser.add_argument("--facturation-python", type=Path)
    parser.add_argument("--management-python", type=Path)
    parser.add_argument("--workflow-python", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.native_check:
        print(json.dumps(native_check(args.native_check, args.backend, json.load(sys.stdin)), ensure_ascii=False))
    elif args.prepare:
        if not all((args.backends_root, args.facturation_python, args.management_python, args.workflow_python)):
            parser.error("Preparation requires the backend root and all three native Python interpreters.")
        result = prepare(args.backends_root, {"facturation": args.facturation_python,
            "management_projet": args.management_python, "design_workflow": args.workflow_python}, args.output)
        print(json.dumps(result["counts"]))
    else:
        parser.error("Choose --prepare or --native-check.")
