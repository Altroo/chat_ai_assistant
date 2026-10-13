"""Prepare clearer validation requests without changing active comparisons.

Reads only the published validation split and native-source audit metadata.
No candidate predictions, training examples, inference or score calculation.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "training/datasets/shared-v5r6-en-fr"
OUTPUT = ROOT / "training/datasets/shared-validation-v2-en-fr"
SOURCE_MANIFEST_SHA256 = "71d2f2e11ce5f7abf55a32b486c76169d67e8231547084d42ce1c08583ca60b4"

# Source row identifies a distinct request. All identical history variants get
# the same correction; history, trusted context, offered tools and targets stay.
# Defects and uncertain wording are deliberately distinguished.
EDITS = {
    2: ("containing SYN-BOBINE", "containing article SYN-BOBINE", "explicit_article", "ambiguous"),
    3: ("contenant SYN-BOBINE", "contenant l’article SYN-BOBINE", "explicit_article", "ambiguous"),
    12: ("with SYN-CHARNIERE", "containing article SYN-CHARNIERE", "explicit_article", "ambiguous"),
    13: ("avec SYN-CHARNIERE", "contenant l’article SYN-CHARNIERE", "explicit_article", "ambiguous"),
    16: ("with SYN-CHARNIERE", "containing article SYN-CHARNIERE", "explicit_article", "ambiguous"),
    17: ("avec SYN-CHARNIERE", "contenant l’article SYN-CHARNIERE", "explicit_article", "ambiguous"),
    20: ("with SYN-CHARNIERE", "containing article SYN-CHARNIERE", "explicit_article", "ambiguous"),
    21: ("avec SYN-CHARNIERE", "contenant l’article SYN-CHARNIERE", "explicit_article", "ambiguous"),
    22: ("Two products maximum, designation containing", "Two article records maximum, reference or designation containing", "native_article_search_scope", "defect"),
    23: ("désignation contenant", "référence ou désignation contenant", "native_article_search_scope", "defect"),
    108: ("Combien de dépenses", "Quel montant total de dépenses", "amount_not_count", "ambiguous"),
    116: ("pour SYN-Jonc", "pour le projet SYN-Jonc", "explicit_project", "ambiguous"),
    117: ("for SYN-Jonc", "for project SYN-Jonc", "explicit_project", "ambiguous"),
    136: ("pour Pavillon Essai", "pour le projet Pavillon Essai", "explicit_project", "ambiguous"),
    137: ("for Pavillon Essai", "for project Pavillon Essai", "explicit_project", "ambiguous"),
    138: ("Dans Pavillon Essai : budget réel, étape Façade.", "Dans le projet Pavillon Essai, recherche les lignes de budget réel contenant « Façade » dans l’étape, la description ou les notes.", "native_budget_search_scope", "defect"),
    139: ("In Pavillon Essai: actual budget, stage Façade.", "In project Pavillon Essai, find actual-budget entries containing “Façade” in their stage, description or notes.", "native_budget_search_scope", "defect"),
    140: ("de Pavillon Essai", "du projet Pavillon Essai", "explicit_project", "ambiguous"),
    141: ("for Pavillon Essai", "for project Pavillon Essai", "explicit_project", "ambiguous"),
    142: ("pour Pavillon Essai", "pour le projet Pavillon Essai", "explicit_project", "ambiguous"),
    143: ("for Pavillon Essai", "for project Pavillon Essai", "explicit_project", "ambiguous"),
    152: ("Pour Lucarne Essai", "Pour le projet Lucarne Essai", "explicit_project", "uncertain"),
    153: ("For Lucarne Essai", "For project Lucarne Essai", "explicit_project", "uncertain"),
    164: ("de Fictif Étain", "du fournisseur Fictif Étain", "explicit_supplier", "ambiguous"),
    165: ("from Fictif Étain", "from supplier Fictif Étain", "explicit_supplier", "ambiguous"),
    174: ("pour Topaze", "pour le projet Topaze", "explicit_project", "ambiguous"),
    175: ("for Topaze", "for project Topaze", "explicit_project", "ambiguous"),
    186: ("de SYN-Frene", "du projet SYN-Frene", "explicit_project", "ambiguous"),
    187: ("in SYN-Frene", "in project SYN-Frene", "explicit_project", "ambiguous"),
    194: ("Cartes de Démo Ines dans Atelier Essai", "Cartes assignées à Démo Ines dans le projet Atelier Essai", "explicit_assignment_and_project", "uncertain"),
    195: ("in Atelier Essai", "in project Atelier Essai", "explicit_project", "uncertain"),
    202: ("sur Atelier Essai", "dans le projet Atelier Essai", "explicit_project", "uncertain"),
    203: ("on Atelier Essai", "in project Atelier Essai", "explicit_project", "uncertain"),
    204: ("dont le nom est", "dont le nom contient", "substring_project_name", "uncertain"),
    205: ("whose name is", "whose name contains", "substring_project_name", "uncertain"),
    208: ("Dans Lucarne Essai, les cartes en cours de Démo Aya.", "Dans le projet Lucarne Essai, les cartes en cours assignées à Démo Aya.", "explicit_assignment_and_project", "uncertain"),
    209: ("In Lucarne Essai", "In project Lucarne Essai", "explicit_project", "uncertain"),
    214: ("dans Maquette Témoin", "dans le projet Maquette Témoin", "explicit_project", "uncertain"),
    215: ("in Maquette Témoin", "in project Maquette Témoin", "explicit_project", "uncertain"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def request(row):
    text = row["messages"][-2]["content"]
    if text.startswith("Earlier user messages (background only): "):
        return text.split("\nCurrent request: ", 1)[1]
    return text


def correct(rows):
    require(len(rows) == 275, "Unexpected validation size")
    changes = {}
    for index, (before, after, kind, certainty) in EDITS.items():
        old = request(rows[index])
        require(old.count(before) == 1, "Reviewed request drifted")
        require(old not in changes, "Duplicate source request")
        changes[old] = (old.replace(before, after), kind, certainty, index)
    result, provenance = [], []
    for index, row in enumerate(rows):
        value = deepcopy(row)
        old = request(row)
        if old in changes:
            new, kind, certainty, source_index = changes[old]
            text = value["messages"][-2]["content"]
            require(text.endswith(old), "Request boundary changed")
            value["messages"][-2]["content"] = text[:-len(old)] + new
            provenance.append({"index": index, "source_scenario_index": source_index,
                               "kind": kind, "certainty": certainty,
                               "old_request": old, "new_request": new})
        result.append(value)
    return result, provenance


def prepare(source=SOURCE, output=OUTPUT):
    require(not output.exists(), "Never overwrite a versioned validation split")
    require(sha(source / "manifest.json") == SOURCE_MANIFEST_SHA256, "Parent manifest changed")
    manifest = json.loads((source / "manifest.json").read_text())
    require(manifest["version"] == "shared-v5r6-en-fr", "Unexpected parent")
    for name in ("train.jsonl", "valid.jsonl"):
        require(sha(source / name) == manifest["files"][name], "Parent data changed")
    raw = (source / "valid.jsonl").read_text().splitlines(keepends=True)
    rows = [json.loads(line) for line in raw]
    values, changes = correct(rows)
    payload = "".join(json.dumps(value, ensure_ascii=False) + "\n" if value != row else line
                      for row, value, line in zip(rows, values, raw))
    report = {
        "version": output.name, "applications": manifest["applications"], "languages": ["en", "fr"],
        "parent_manifest_sha256": sha(source / "manifest.json"),
        "parent_validation_sha256": sha(source / "valid.jsonl"),
        "unchanged_training_sha256": sha(source / "train.jsonl"),
        "generator_sha256": sha(Path(__file__)),
        "count": len(rows), "changed_count": len(changes), "unchanged_count": len(rows) - len(changes),
        "changed_distinct_requests": len(EDITS), "changes": changes,
        "targets_changed": 0, "contexts_changed": 0, "tools_changed": 0,
        "status": "PREPARED; not measured or used for checkpoint selection",
        "policy": "Separate future validation version. All active and historical V1 inputs, predictions, scores and selection rules remain unchanged. No training or held-out acceptance data is changed. V2 needs its own frozen comparison and fresh inference for changed prompts; it must not be substituted into the current eight-checkpoint comparison. Identical-history variants remain correlated. Targets stay unchanged: article requests explicitly use the broad native reference-or-designation scope and both languages now ask for articles rather than a product-only subset. Native budget search scope and named entity relationships are made explicit.",
        "limitations": [
            "Source scenarios have been repeatedly inspected; this is not an unseen accuracy certification.",
            "Most edits clarify ambiguous or uncertain wording rather than establish that the original expected action was wrong.",
            "The clearer wording changes task difficulty. V1 and V2 scores must be reported separately.",
            "Unchanged targets are not proof of native authorization or deployment readiness."
        ],
        "files": {"valid.jsonl": hashlib.sha256(payload.encode()).hexdigest()},
    }
    output.mkdir()
    (output / "valid.jsonl").write_text(payload)
    (output / "manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


if __name__ == "__main__":
    result = prepare()
    print(json.dumps({k: result[k] for k in ("count", "changed_count", "unchanged_count", "changed_distinct_requests", "status")}))
