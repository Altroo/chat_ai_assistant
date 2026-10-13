"""Prepare twelve replacement training rows with native search scope.

The replacements are NOT extra samples: a future dataset must replace the
corresponding parent rows. Completed training and original data stay immutable.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "training/datasets/shared-v5r6-en-fr"
OUTPUT = ROOT / "training/datasets/training-scope-errata-v1-en-fr"
PARENT = "71d2f2e11ce5f7abf55a32b486c76169d67e8231547084d42ce1c08583ca60b4"
CHANGES = {
    72: ("Look for articles whose designation includes SYN-VERNIS.", "Look for articles whose reference or designation includes SYN-VERNIS."),
    73: ("Cherche les articles dont la désignation contient SYN-VERNIS.", "Cherche les articles dont la référence ou la désignation contient SYN-VERNIS."),
    80: ("Search archived articles whose designation contains SYN-VERNIS.", "Search archived articles whose reference or designation contains SYN-VERNIS."),
    81: ("Cherche les articles archivés dont la désignation contient SYN-VERNIS.", "Cherche les articles archivés dont la référence ou la désignation contient SYN-VERNIS."),
    654: ("Dans les lignes du budget réel du projet SYN-Lotus, recherche l’étape Menuiserie.", "Dans les lignes du budget réel du projet SYN-Lotus, recherche Menuiserie dans l’étape, la description ou les notes."),
    655: ("In actual budget entries for project SYN-Lotus, search stage Menuiserie.", "In actual budget entries for project SYN-Lotus, search Menuiserie in the stage, description or notes."),
    854: ("Dans le budget réel de SYN-Aster, retrouve l’étape Électricité.", "Dans le budget réel du projet SYN-Aster, recherche Électricité dans l’étape, la description ou les notes."),
    855: ("In the actual budget of SYN-Aster, find the Électricité stage.", "In the actual budget of project SYN-Aster, search Électricité in the stage, description or notes."),
    952: ("Budget réel de Rive 42, étape Fondation.", "Budget réel du projet Rive 42 : recherche Fondation dans l’étape, la description ou les notes."),
    953: ("Actual budget of Rive 42, stage Fondation.", "Actual budget of project Rive 42: search Fondation in the stage, description or notes."),
    1108: ("Budget réel : Belvédère Test ; étape Électricité.", "Budget réel du projet Belvédère Test : recherche Électricité dans l’étape, la description ou les notes."),
    1109: ("Actual budget: Belvédère Test; stage Électricité.", "Actual budget of project Belvédère Test: search Électricité in the stage, description or notes."),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def request(row):
    return row["messages"][-2]["content"].split("\nCurrent request: ", 1)[-1]


def replacements(rows):
    require(len(rows) == 1969, "Unexpected source size")
    result, provenance = [], []
    for index, (old, new) in CHANGES.items():
        row = rows[index]
        require(request(row) == old, "Reviewed source request changed")
        value = deepcopy(row)
        text = value["messages"][-2]["content"]
        value["messages"][-2]["content"] = text[:-len(old)] + new
        fn = value["messages"][-1]["tool_calls"][0]["function"]
        schemas = {t["function"]["name"]:t["function"]["parameters"] for t in value["tools"]}
        validate(fn["arguments"], schemas[fn["name"]])
        result.append(value)
        provenance.append({"source_index": index, "old_request": old, "new_request": new,
                           "scope": "reference_or_designation" if index < 100 else "stage_description_or_notes"})
    return result, provenance


def prepare(source=SOURCE, output=OUTPUT):
    require(not output.exists(), "Never overwrite versioned training corrections")
    require(sha(source / "manifest.json") == PARENT, "Parent manifest changed")
    manifest = json.loads((source / "manifest.json").read_text())
    for name in ("train.jsonl", "valid.jsonl"):
        require(sha(source / name) == manifest["files"][name], "Parent data changed")
    rows = list(map(json.loads, (source / "train.jsonl").read_text().splitlines()))
    values, provenance = replacements(rows)
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in values)
    report = {
        "version": output.name, "languages": ["en", "fr"], "applications": ["facturation", "management_projet"],
        "parent_manifest_sha256": PARENT, "parent_training_sha256": manifest["files"]["train.jsonl"],
        "unchanged_validation_sha256": manifest["files"]["valid.jsonl"],
        "generator_sha256": sha(Path(__file__)), "replacement_count": len(values),
        "source_rows": len(rows), "unchanged_rows": len(rows) - len(values),
        "targets_changed": 0, "context_changed": 0, "tools_changed": 0, "provenance": provenance,
        "status": "PREPARED replacements; not assembled into a cumulative dataset or trained",
        "policy": "Use each replacement at its exact source index in a separately versioned future dataset. Do not append it as another training example or mutate the original source. Requests are broadened explicitly to the supported native multi-field search; targets, other filters, history and trusted context remain unchanged. This corrects instructional inconsistency, not the backend. Original training, validation, held-out inputs and historical scores remain unchanged.",
        "limitations": ["Review covered the 28 article-search and 46 budget-entry-search training rows, not every training example.",
                       "Preparation alone establishes no model accuracy improvement or production readiness."],
        "files": {"train.replacements.jsonl": hashlib.sha256(payload.encode()).hexdigest()},
    }
    output.mkdir()
    (output / "train.replacements.jsonl").write_text(payload)
    (output / "manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


if __name__ == "__main__":
    result = prepare()
    print(json.dumps({k: result[k] for k in ("replacement_count", "unchanged_rows", "status")}))
