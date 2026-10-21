"""Prepare TRAIN-only argument contrasts with frozen, input-only exclusions.

No model is loaded. Existing replay and validation bytes remain unchanged.
Development inputs prevent duplication; their answers never supply labels.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import date, timedelta
from difflib import SequenceMatcher
from functools import cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unicodedata

VERSION = "facturation-argument-coverage-v2-en-fr"
BASE_SHA = "1fc45ecdca5b89b78906a1c29fc5cf90a9e01580de6b6cb06fcfa317c969be4b"
BASE_MANIFEST_SHA = "bfabe880b969467a9f55750790bd618ac9476e9f47ae409b20cfa7cb5864785c"
SOURCE_SHA = "05e792a632ba37cdbb71845e57c0444f4feb4c94851addc5ec84a9674da0cb0d"
VALID_SHA = "8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487"
HELPER_SHA = "3d7f2eee56c328593d8ccfbd01c4aea1e637da0b6a4d13079ee48d5489d27d43"
FAMILIES = {"literal_field_boundaries": 32, "unpaid_filter_presence": 16,
            "inclusive_exclusive_dates": 16, "available_payment_tool": 16}
PARENTS = {
    "remark": {("en", "proforma"): 437, ("fr", "proforma"): 438,
               ("en", "quote"): 443, ("fr", "quote"): 444},
    "invoices": {"en": 449, "fr": 86},
    "payments": {"en": 53, "fr": 49},
    "denied": {"en": 497, "fr": 499},
    "latest": 198,
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def rows(raw):
    return [json.loads(line) for line in raw.splitlines()]


@cache
def helper():
    path = Path(__file__).with_name("prepare_facturation_semantic_contrasts_v1.py")
    if sha(path.read_bytes()) != HELPER_SHA:
        raise ValueError("Reviewed semantic helper changed")
    spec = importlib.util.spec_from_file_location("argument_coverage_helper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def input_only(row):
    """Exclude answers before copying, including supervised assistant tool calls."""
    messages = row["messages"]
    if messages and messages[-1]["role"] == "assistant":
        messages = messages[:-1]
    if not messages or messages[-1]["role"] != "user":
        raise ValueError("Input must end with the current user request")
    tools = row["offered_tool_schemas"] if "offered_tool_schemas" in row else row["tools"]
    names = [tool["function"]["name"] for tool in tools]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate offered tool")
    # The runtime may inject clarify. It must not hide otherwise identical inputs.
    tools = sorted((deepcopy(t) for t in tools if t["function"]["name"] != "clarify"),
                   key=lambda t: t["function"]["name"])
    messages = deepcopy(messages)
    prefix, text = helper().helper().current_request(messages[-1]["content"])
    if prefix:
        history, _ = json.JSONDecoder().raw_decode(
            messages[-1]["content"][len("Earlier user messages (background only): "):])
        if len(history) == 1 and history[0] in helper().helper().NEUTRAL_HISTORY:
            messages[-1]["content"] = text
    return {"messages": messages, "tools": tools}


def request_pattern(row):
    text = input_only(row)["messages"][-1]["content"]
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "<date>", text)
    text = re.sub(r"\b\d+\b", "<number>", text)
    return re.sub(r"\s+", " ", text).strip()


def exclusions(original, generated, excluded):
    """Strictly guard new rows, and disclose stronger-check legacy collisions."""
    old_keys = {encoded(input_only(row)) for row in original}
    excluded_keys = {encoded(input_only(row)) for row in excluded}
    patterns = {request_pattern(row) for row in excluded}
    seen = set(old_keys)
    for row in generated:
        key = encoded(input_only(row))
        pattern = request_pattern(row)
        if key in seen or key in excluded_keys:
            raise ValueError("New TRAIN input overlaps replay or evaluation input")
        if any(m.quick_ratio() >= 0.90 and m.ratio() >= 0.90
               for m in (SequenceMatcher(None, pattern, other, autojunk=False) for other in patterns)):
            raise ValueError("New TRAIN request is a near duplicate of an evaluation input")
        seen.add(key)
    return {"input_rows_checked": len(excluded),
            "legacy_exact_overlap_under_stronger_normalization": len(old_keys & excluded_keys),
            "new_exact_overlap": 0, "new_near_duplicate_overlap": 0,
            "near_duplicate_ratio_threshold": 0.90,
            "clarify_injection_and_tool_order_normalized": True,
            "evaluation_answers_consulted": False}


def generate(source):
    old = helper()
    result = []

    def add(n, family, language, request, name, arguments, factors):
        parent = source[n - 1]
        old.target(parent)
        old.trusted_context(parent)
        row = old.make(parent, n, family, language, request, arguments,
                       tool=name, factors=factors)
        row["augmentation"]["version"] = VERSION
        result.append(row)

    notes = {
        "en": ("SYN-Packaging checked and accepted",
               "SYN-Ready after inspection, keep the delivery label",
               "SYN-Inspection complete with no missing parts",
               "SYN-Wait for the approved packing instructions"),
        "fr": ("SYN-Emballage contrôlé et accepté",
               "SYN-Prêt après inspection, garder l’étiquette de livraison",
               "SYN-Inspection terminée sans pièce manquante",
               "SYN-Attendre les consignes d’emballage approuvées"),
    }
    for (language, resource), n in PARENTS["remark"].items():
        parent_call = old.target(source[n - 1])
        if (parent_call["name"] != "prepare_change"
                or parent_call["arguments"]["resource"] != resource
                or parent_call["arguments"]["operation"] != "update"):
            raise ValueError("Unexpected verified update parent")
        label = {"en": {"quote": "quote", "proforma": "pro forma invoice"},
                 "fr": {"quote": "devis", "proforma": "facture pro forma"}}[language][resource]
        for style in range(4):
            for variant in range(2):
                ordinal = len(result)
                identifier = 84001 + ordinal
                due = (date(2035, 5, 12) + timedelta(days=ordinal * 3)).isoformat()
                note = notes[language][(style + variant) % 4]
                quoted = json.dumps(note, ensure_ascii=False)
                if language == "en":
                    requests = (
                        f"On {label} ID {identifier}, change Remark to {note} and Due date to {due}.",
                        f"For {label} ID {identifier}, use {quoted} as Remark and {due} as Due date.",
                        f"Move Due date to {due} and set Remark to {quoted} on {label} ID {identifier}.",
                        f"Update these fields on {label} ID {identifier}: Remark: {quoted}; Due date: {due}.",
                    )
                else:
                    requests = (
                        f"Sur le document {label} ID {identifier}, remplace Remarque par {note} et Date d’échéance par {due}.",
                        f"Pour le document {label} ID {identifier}, utilise {quoted} comme Remarque et {due} comme Date d’échéance.",
                        f"Déplace Date d’échéance au {due} et mets Remarque à {quoted} sur le document {label} ID {identifier}.",
                        f"Mets à jour ces champs sur le document {label} ID {identifier} : Remarque : {quoted} ; Date d’échéance : {due}.",
                    )
                args = {"resource": resource, "identifier": identifier, "operation": "update",
                        "changes": {"remarque": note, "date_echeance": due}}
                add(n, "literal_field_boundaries", language, requests[style],
                    "prepare_change", args, {"style": style, "variant": variant,
                    "resource": resource, "identifier": identifier, "due": due, "literal": note})

    for language, n in PARENTS["invoices"].items():
        if old.target(source[n - 1])["name"] != "search_invoices":
            raise ValueError("Unexpected invoice parent")
        for profile in range(4):
            customer = ("SYN-Customer-" if language == "en" else "SYN-Client-") + ("Liseron", "Saule", "Tilleul", "Houx")[profile]
            product = "SYN-Article-" + ("Cobalt", "Satin", "Cuivre", "Jade")[profile]
            args = ({"client_name": customer, "product_name": product, "limit": 4,
                     "date_from": "2035-06-03", "date_to": "2035-06-18"},
                    {"client_name": customer, "product_name": product},
                    {"client_name": customer, "limit": 6, "date_to": "2035-07-30"},
                    {"product_name": product, "limit": 1, "date_from": "2035-08-04"})[profile]
            if language == "en":
                details = (f"for customer {customer} with article {product}, between 2035-06-03 and 2035-06-18 inclusive; return up to 4",
                           f"for customer {customer} with article {product}",
                           f"for customer {customer}, earlier than 2035-07-31; return no more than 6",
                           f"with article {product}, starting on 2035-08-04 inclusive; return only 1")[profile]
                requests = (f"I need invoice matches {details}.",
                            f"I need invoice matches {details}. Keep only invoices with a balance still unpaid.")
            else:
                details = (f"du client {customer} avec l’article {product}, entre le 2035-06-03 et le 2035-06-18 inclus ; affiche au maximum 4 résultats",
                           f"du client {customer} avec l’article {product}",
                           f"du client {customer}, avant le 2035-07-31 ; affiche au plus 6 résultats",
                           f"avec l’article {product}, depuis le 2035-08-04 inclus ; affiche un seul résultat")[profile]
                requests = (f"J’ai besoin des factures {details}.",
                            f"J’ai besoin des factures {details}. Garde uniquement celles dont le solde reste à payer.")
            for unpaid in (False, True):
                expected = deepcopy(args)
                if unpaid:
                    expected["unpaid"] = True
                add(n, "unpaid_filter_presence", language, requests[int(unpaid)],
                    "search_invoices", expected, {"profile": profile, "unpaid_requested": unpaid,
                    "filters": deepcopy(args)})

    n = PARENTS["latest"]
    if old.target(source[n - 1]) != {"name": "list_payments", "arguments": {}}:
        raise ValueError("Unexpected latest-payments parent")
    for language in ("en", "fr"):
        for anchor in ("2035-04-30", "2036-02-29"):
            d = date.fromisoformat(anchor)
            modes = (
                ("lower_inclusive", {"date_from": anchor},
                 f"on {anchor} or any later day", f"le {anchor} ou à une date ultérieure"),
                ("lower_exclusive", {"date_from": (d + timedelta(days=1)).isoformat()},
                 f"after {anchor}, excluding that day", f"après le {anchor}, en excluant ce jour"),
                ("upper_inclusive", {"date_to": anchor},
                 f"no later than {anchor}, including that day", f"au plus tard le {anchor}, en incluant ce jour"),
                ("upper_exclusive", {"date_to": (d - timedelta(days=1)).isoformat()},
                 f"before {anchor}, excluding that day", f"avant le {anchor}, en excluant ce jour"),
            )
            for mode, args, english, french in modes:
                request = (f"Among valid payments dated {english}, show the latest records."
                           if language == "en" else
                           f"Parmi les règlements valides datés {french}, affiche les plus récents.")
                add(n, "inclusive_exclusive_dates", language, request, "list_payments",
                    args, {"mode": mode, "anchor": anchor})

    for language in ("en", "fr"):
        for query in ("SYN-Transaction-Nebuleuse", "SYN-Transaction-Peche",
                      "SYN-Transaction-Silex", "SYN-Transaction-Verveine"):
            request = (f"In payment records, look for {query} in either the customer’s name or the invoice’s number."
                       if language == "en" else
                       f"Dans les règlements, retrouve {query} dans le nom du client ou le numéro de facture.")
            for available in (True, False):
                n = PARENTS["payments" if available else "denied"][language]
                offered = {t["function"]["name"] for t in source[n - 1]["tools"]}
                if ("search_payments" in offered) != available:
                    raise ValueError("Payment permission contrast changed")
                args = {"query": query} if available else {"reason": "unsupported", "language": language}
                add(n, "available_payment_tool", language, request,
                    "search_payments" if available else "clarify", args,
                    {"available": available, "query": query})
    validate(result, source)
    return result


def validate(generated, source):
    old = helper()
    if Counter(r["augmentation"]["family"] for r in generated) != Counter(FAMILIES):
        raise ValueError("Missing argument coverage family")
    if Counter(r["language"] for r in generated) != Counter(en=40, fr=40):
        raise ValueError("Unbalanced language coverage")
    for row in generated:
        meta = row["augmentation"]
        parent = source[meta["source_line"] - 1]
        original = old.target(parent)
        call = old.target(row)
        if row["tools"] != parent["tools"] or row["messages"][:-2] != parent["messages"][:-2]:
            raise ValueError("Trusted context or permissions changed")
        prefix, _ = old.helper().current_request(parent["messages"][-2]["content"])
        actual_prefix, text = old.helper().current_request(row["messages"][-2]["content"])
        if actual_prefix != prefix:
            raise ValueError("Neutral background changed")
        f = meta["factors"]
        family = meta["family"]
        args = call["arguments"]
        if family == "literal_field_boundaries":
            if (call["name"] != "prepare_change"
                    or args != {"resource": f["resource"], "identifier": f["identifier"],
                                "operation": "update", "changes": {
                                    "remarque": f["literal"], "date_echeance": f["due"]}}
                    or text.count(f["literal"]) != 1 or text.count(f["due"]) != 1
                    or str(f["identifier"]) not in text
                    or original["arguments"]["resource"] != f["resource"]):
                raise ValueError("Full literal or separate change fields lost")
            date.fromisoformat(f["due"])
        elif family == "unpaid_filter_presence":
            expected = deepcopy(f["filters"])
            if f["unpaid_requested"]:
                expected["unpaid"] = True
            if call["name"] != "search_invoices" or args != expected:
                raise ValueError("Unpaid filter presence changed")
            if not f["unpaid_requested"] and "unpaid" in args:
                raise ValueError("Unrequested unpaid filter")
        elif family == "inclusive_exclusive_dates":
            d = date.fromisoformat(f["anchor"])
            expected = {
                "lower_inclusive": {"date_from": d.isoformat()},
                "lower_exclusive": {"date_from": (d + timedelta(days=1)).isoformat()},
                "upper_inclusive": {"date_to": d.isoformat()},
                "upper_exclusive": {"date_to": (d - timedelta(days=1)).isoformat()},
            }[f["mode"]]
            if call["name"] != "list_payments" or args != expected:
                raise ValueError("Incorrect inclusive calendar boundary")
        elif family == "available_payment_tool":
            available = f["available"]
            expected = {"query": f["query"]} if available else {
                "reason": "unsupported", "language": row["language"]}
            if call != {"name": "search_payments" if available else "clarify",
                        "arguments": expected}:
                raise ValueError("Payment availability target changed")
        else:
            raise ValueError("Unknown family")


def prepare(base, source, native, output, exclusion_paths):
    base, source, native, output = (Path(p).resolve() for p in (base, source, native, output))
    if (output.exists() or not output.parent.is_dir()
            or any(p == output or p in output.parents for p in (base, source, native))):
        raise ValueError("A new isolated output with an existing parent is required")
    base_raw = (base / "train.jsonl").read_bytes()
    source_raw = (source / "train.jsonl").read_bytes()
    valid = (base / "valid.jsonl").read_bytes()
    if (sha(base_raw), sha(source_raw), sha(valid)) != (BASE_SHA, SOURCE_SHA, VALID_SHA):
        raise ValueError("Pinned replay, approved TRAIN or validation changed")
    if (source / "valid.jsonl").read_bytes() != valid or not base_raw.endswith(b"\n"):
        raise ValueError("Validation bytes or replay line boundary changed")
    original, approved = rows(base_raw), rows(source_raw)
    if len(original) != 176 or len(approved) != 500:
        raise ValueError("Complete replay and approved TRAIN required")
    old = helper()
    if {name: sha((native / name).read_bytes()) for name in old.NATIVE_SHA256} != old.NATIVE_SHA256:
        raise ValueError("Native business contracts changed")
    manifest_raw = (base / "manifest.json").read_bytes()
    if sha(manifest_raw) != BASE_MANIFEST_SHA:
        raise ValueError("Pinned exclusion manifest changed")
    prior_manifest = json.loads(manifest_raw)
    expected_exclusions = prior_manifest["extra_exclusion_sha256"]
    if len(exclusion_paths) != len(expected_exclusions):
        raise ValueError("All frozen input exclusions are required")
    excluded = [input_only(row) for row in rows(valid)]
    exclusion_hashes = {}
    for (name, digest), path in zip(expected_exclusions.items(), exclusion_paths):
        payload = Path(path).read_bytes()
        if sha(payload) != digest:
            raise ValueError("Frozen input exclusion changed")
        exclusion_hashes[name] = digest
        excluded.extend(input_only(row) for row in rows(payload))
    # No expected/evaluation answer field is read below this input-only boundary.
    generated = generate(approved)
    checked = exclusions(original, generated, excluded)
    pattern = re.compile(r"-----BEGIN .*PRIVATE KEY|\bsk-[A-Za-z0-9]{16,}|id_ed25519|"
                         r"(?:password|api[_ -]?key|access[_ -]?token|secret)\s*[:=]\s*\S+", re.I)
    for row in original + generated:
        old.target(row)
        text = row["messages"][-2]["content"] + encoded(row["messages"][-1])
        if pattern.search(text):
            raise ValueError("Possible credential in supervised data")
    additions = b"".join((encoded(row) + "\n").encode() for row in generated)
    train = base_raw + additions
    all_rows = original + generated
    counts = Counter(r["application"] for r in all_rows)
    if counts != Counter(facturation=224, management_projet=16, design_workflow=16):
        raise ValueError("Retained application exposure changed")
    files = {"train.jsonl": train, "valid.jsonl": valid, "additions.jsonl": additions}
    manifest = {
        "version": VERSION, "status": "PREPARED ONLY; review and server preflight required",
        "count": 256, "by_application": dict(counts), "applications": list(counts),
        "languages": ["en", "fr"],
        "base176_preserved_byte_for_byte": True, "frozen_validation_preserved_byte_for_byte": True,
        "additions": FAMILIES, "addition_languages": {"en": 40, "fr": 40},
        "source_sha256": {"base176": BASE_SHA, "approved500": SOURCE_SHA, "validation": VALID_SHA},
        "native_contract_sha256": old.NATIVE_SHA256,
        "source_lines": sorted({r["augmentation"]["source_line"] for r in generated}),
        "exclusions": checked, "exclusion_sha256": exclusion_hashes,
        "sensitive_supervised_rows_checked": len(all_rows),
        "generator_sha256": sha(Path(__file__).read_bytes()), "helper_sha256": HELPER_SHA,
        "files": {name: sha(payload) for name, payload in files.items()},
        "development_informed_correction": True, "new_independent_holdout_claimed": False,
        "evaluation_targets_used_for_training": False, "training_executed": False,
        "model_accepted": False, "production_activation": False,
    }
    output.mkdir(mode=0o700)
    for name, payload in files.items():
        (output / name).write_bytes(payload)
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("base", "source", "native", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--exclusion", type=Path, action="append", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.base, args.source, args.native, args.output, args.exclusion), indent=2))
