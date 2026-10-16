"""Admit a bounded, axis-covered Facturation-only pilot.

Selection consumes synthetic training examples and declared contrast metadata only.
No weights, inference or acceptance inputs are used. Numerical work is separate.
"""
from collections import Counter
from pathlib import Path
import json

import audit_training_inputs as base
from training_schedule import complete_epoch_order

FOCUS_MANIFEST_SHA256 = "b5e9850bd8bcd7a2090f618b60e9d5bdc0a4f1e015a5f744fafdb64305c1cc8b"
PARENT_MANIFEST_SHA256 = "70d19dd8ed341f13bd8dcd9b17f00382f0e75c996bb098260e27ddf5919b470c"
RETAINED_ROWS = 1047
FOCUS_CATEGORIES = (
    "date_optional_document", "date_optional_operation", "mixed_document_filters",
    "unpaid_optional_filters", "exclusive_boundary", "literal_field_copy",
    "account_navigation", "explicit_result_choice", "payment_reference_limit",
    "payment_party_filters",
)


def axis_features(row):
    """Explicit marginal and pairwise axes, not every Cartesian combination."""
    category, language = row["curriculum_category"], row["language"]
    if category not in FOCUS_CATEGORIES or language not in ("en", "fr"):
        raise ValueError("Published English/French contrast category required")
    details, action = row["contrast"], base.target(row)
    features = {(category, "language", language)}
    if category.startswith("date_optional_"):
        resource = action["arguments"].get("resource", action["name"])
        features.update({
            (category, "mode_optional", details["mode"], details["optional_state"]),
            (category, "resource_language", resource, language),
            (category, "mode_language", details["mode"], language),
            (category, "optional_language", details["optional_state"], language),
        })
    elif category == "mixed_document_filters":
        features.add((category, "limit_language", str(details["limit_present"]), language))
    elif category == "unpaid_optional_filters":
        features.update({
            (category, "mode_unpaid", details["mode"], str(details["unpaid_present"])),
            (category, "limit_unpaid", str(details["limit_present"]), str(details["unpaid_present"])),
        })
    elif category == "exclusive_boundary":
        features.add((category, "mode_language", details["mode"], language))
    elif category == "literal_field_copy":
        features.add((category, "field_language", details["fields"], language))
    elif category == "account_navigation":
        features.add((category, "target_language", details["target"], language))
    elif category == "explicit_result_choice":
        features.add((category, "selection_language", details["selection"], language))
    elif category == "payment_reference_limit":
        features.add((category, "limit_language", str(details["limit_present"]), language))
    elif category == "payment_party_filters":
        features.add((category, "party_status", details["party_state"], details["status"]))
    return features


def ordered_indices(rows, indices):
    return sorted(indices, key=lambda i: (base.digest(base.model_input_key(rows[i]).encode()), i))


def cover(rows, candidates, coverage, required):
    pending, selected = set(required), []
    candidates = ordered_indices(rows, candidates)
    while pending:
        if not candidates:
            raise ValueError("Required pilot axes are absent")
        best = max(candidates, key=lambda i: len(coverage[i] & pending))
        if not coverage[best] & pending:
            raise ValueError("Required pilot axes are absent")
        selected.append(best)
        pending -= coverage[best]
        candidates.remove(best)
    return selected


def balanced_selection(rows, maximum=96):
    if type(maximum) is not int or not 1 <= maximum <= 96:
        raise ValueError("Positive pilot budget of at most 96 updates required")
    if len(rows) != 1487:
        raise ValueError("Published pilot training row count changed")
    axes = {i: axis_features(rows[i]) for i in range(RETAINED_ROWS, len(rows))}
    required_axes = set().union(*axes.values())
    added = cover(rows, axes, axes, required_axes)
    # Existing tool, operation and clarification-reason groups that additions
    # do not cover must receive retained training sentinels.
    regular = {i: base.features(row) for i, row in enumerate(rows)}
    required_regular = set().union(*regular.values())
    covered_regular = set().union(*(regular[i] for i in added))
    retained = cover(rows, range(RETAINED_ROWS), regular, required_regular - covered_regular)
    selected = added + retained
    if len(selected) > maximum:
        raise ValueError("Pilot budget cannot cover declared axes and retained tool groups")
    selected = [selected[i] for i in complete_epoch_order([rows[i] for i in selected])]
    if len(selected) != len(set(selected)):
        raise ValueError("Pilot contains duplicate row indices")
    if len({base.model_input_key(rows[i]) for i in selected}) != len(selected):
        raise ValueError("Pilot contains duplicate model inputs")
    category_coverage = []
    for category in FOCUS_CATEGORIES:
        for language in ("en", "fr"):
            indices = [i for i in added if rows[i]["curriculum_category"] == category
                       and rows[i]["language"] == language]
            if not indices:
                raise ValueError("Pilot omits a category/language group")
            category_coverage.append({"application": "facturation", "category": category,
                                      "language": language, "row_index": ordered_indices(rows, indices)[0]})
    return {
        "selection_contract": "facturation-v2-axis-covered-training-pilot",
        "row_indices": selected, "count": len(selected),
        "by_application": dict(Counter(rows[i]["application"] for i in selected)),
        "by_explicit_language": dict(Counter(rows[i].get("language", "unlabeled") for i in selected)),
        "added_training_rows": added, "retained_training_sentinels": retained,
        "covered_features": [list(value) for value in sorted(required_regular)],
        "covered_axes": [list(value) for value in sorted(required_axes)],
        "curriculum_categories": sorted(FOCUS_CATEGORIES),
        "category_coverage": category_coverage,
        "selected_rows_sha256": base.digest(base.encoded([rows[i] for i in selected]).encode()),
        "status": "PREPARATION ONLY; numerical pilot and comparison not executed",
        "limitations": [
            "Covers declared marginal and pairwise axes, not every Cartesian cell or all 440 additions.",
            "Shared bilingual variants are correlated, not independent observations.",
            "Retained sentinels cover remaining tool/operation/reason groups, not every old training example.",
            "Selection uses training inputs only. It does not predict validation or acceptance accuracy.",
            "No longer epoch or production activation is admitted by this preparation.",
        ],
    }


def prepare_inputs(data, stage, retained, correction_root=None, *, categories=()):
    if stage != "facturation" or retained is not None or correction_root is not None:
        raise ValueError("This pilot admits Facturation only")
    if categories and (len(categories) != len(FOCUS_CATEGORIES) or set(categories) != set(FOCUS_CATEGORIES)):
        raise ValueError("Every published pilot category is required")
    data = Path(data)
    manifest_raw = (data / "manifest.json").read_bytes()
    if base.digest(manifest_raw) != FOCUS_MANIFEST_SHA256:
        raise ValueError("Published pilot manifest changed")
    manifest = json.loads(manifest_raw)
    if manifest["applications"] != ["facturation"] or manifest["languages"] != ["en", "fr"]:
        raise ValueError("Facturation English/French scope required")
    parent = data.parent / "facturation-focus-v1-en-fr"
    parent_raw = (parent / "manifest.json").read_bytes()
    if base.digest(parent_raw) != PARENT_MANIFEST_SHA256:
        raise ValueError("Published parent manifest changed")
    parent_manifest = json.loads(parent_raw)
    payloads = {s: (data / (s + ".jsonl")).read_bytes() for s in ("train", "valid")}
    parent_payloads = {s: (parent / (s + ".jsonl")).read_bytes() for s in ("train", "valid")}
    if any(base.digest(value) != parent_manifest["files"][split + ".jsonl"]
           for split, value in parent_payloads.items()):
        raise ValueError("Published parent split changed")
    if (manifest["source_manifest_sha256"] != PARENT_MANIFEST_SHA256
            or not payloads["train"].startswith(parent_payloads["train"])
            or payloads["valid"] != parent_payloads["valid"]):
        raise ValueError("Pilot must retain every parent training and validation byte")
    checked = base.audit(data)
    if checked["manifest_sha256"] != FOCUS_MANIFEST_SHA256:
        raise ValueError("Pilot manifest changed during audit")
    if any(base.digest(value) != checked["input_sha256"][split] for split, value in payloads.items()):
        raise ValueError("Pilot inputs changed during audit")
    rows = {s: [json.loads(line) for line in value.splitlines()] for s, value in payloads.items()}
    if (len(rows["train"]), len(rows["valid"])) != (1487, 133):
        raise ValueError("Published pilot row counts changed")
    checked["rehearsal"] = balanced_selection(rows["train"])
    selected = checked["rehearsal"]["row_indices"]
    captures = []
    # One declared diagnostic per new category, alternating its language.
    # Full bilingual development evaluation is separate and remains required.
    for offset, category in enumerate(FOCUS_CATEGORIES):
        language = ("en", "fr")[offset % 2]
        eligible = [i for i in selected if i >= RETAINED_ROWS
                    and rows["train"][i]["curriculum_category"] == category
                    and rows["train"][i]["language"] == language]
        captures.append(ordered_indices(rows["train"], eligible)[0])
    retained_candidates = checked["rehearsal"]["retained_training_sentinels"]
    captures += ordered_indices(rows["train"], retained_candidates)[:2]
    # Validation capture choice depends only on model inputs, never targets.
    validation = ordered_indices(rows["valid"], range(len(rows["valid"])))[:2]
    lineage = {
        "application": "facturation", "manifest_sha256": FOCUS_MANIFEST_SHA256,
        "source_manifest_sha256": PARENT_MANIFEST_SHA256,
        "retained_training_rows_byte_identical": RETAINED_ROWS,
        "retained_validation_rows_byte_identical": 133,
        "model_acceptance_verified": False, "longer_training_admitted": False,
    }
    if ((data / "manifest.json").read_bytes() != manifest_raw
            or (parent / "manifest.json").read_bytes() != parent_raw
            or any((data / (s + ".jsonl")).read_bytes() != value for s, value in payloads.items())
            or any((parent / (s + ".jsonl")).read_bytes() != value for s, value in parent_payloads.items())):
        raise ValueError("Pilot or retained source changed during admission")
    return checked, rows, {"train": captures, "valid": validation}, lineage
