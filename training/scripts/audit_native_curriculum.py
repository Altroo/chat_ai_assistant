"""Read-only curriculum/native-routing audit; no Django database or model calls."""
import argparse
import ast
from copy import deepcopy
from dataclasses import make_dataclass, replace
import hashlib
import json
from pathlib import Path
import re

from jsonschema import validate
from chat_ai_assistant.routing import normalized, shortlist as facturation_shortlist
from chat_ai_assistant.selection_context import explicit_target_matches
from prepare_shared_v5r6 import current_request, function

Tool = make_dataclass("Tool", [("name", str), ("input_schema", dict)])


def load_shortlist(path):
    """Load the actual, self-contained native function, without Django startup.

    Paths must be reviewed local application source, not retrieved/user content.
    Source hashes in the result bind the audit to those exact implementations.
    """
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "shortlist")
    namespace = {"normalized": normalized, "deepcopy": deepcopy, "replace": replace, "re": re}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["shortlist"]


def load_facturation_aliases(path):
    tree = ast.parse(path.read_text())
    prepare = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "prepare")
    return ast.literal_eval(next(
        node.value for node in prepare.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "aliases" for target in node.targets)
    ))


def audit(dataset, management_planner, design_planner, facturation_actions):
    manifest = json.loads((dataset / "manifest.json").read_text())
    payload = (dataset / "train.jsonl").read_bytes()
    assert hashlib.sha256(payload).hexdigest() == manifest["files"]["train.jsonl"]
    rows = [json.loads(line) for line in payload.splitlines()]
    retained = manifest["counts"]["retained_train"]
    assert len(rows) == manifest["counts"]["train"] == retained + manifest["counts"]["added_train"]
    native = {"facturation": facturation_shortlist,
              "management_projet": load_shortlist(management_planner),
              "design_workflow": load_shortlist(design_planner)}
    aliases = load_facturation_aliases(facturation_actions)
    target_checks = 0
    for line, row in enumerate(rows[retained:], start=retained + 1):
        target = function(row)
        context = json.loads(row["messages"][0]["content"].split("Trusted context: ", 1)[1])
        tools = [Tool(t["function"]["name"], t["function"]["parameters"]) for t in row["tools"]]
        offered = {t.name: t for t in native[row["application"]](current_request(row), tools, context)}
        if target["name"] not in offered:
            raise ValueError(f"Row {line}: expected tool is not natively offered")
        validate(target["arguments"], offered[target["name"]].input_schema)
        if row["application"] == "facturation" and target["name"] == "prepare_change":
            args = target["arguments"]
            if explicit_target_matches(current_request(row), args["resource"], args["identifier"], aliases) is not True:
                raise ValueError(f"Row {line}: explicit mutation target does not match native guard")
            target_checks += 1
    import chat_ai_assistant.routing as routing
    import chat_ai_assistant.selection_context as selection_context
    sources = {"management_planner": management_planner, "design_planner": design_planner,
               "facturation_actions": facturation_actions, "shared_routing": Path(routing.__file__),
               "shared_target_guard": Path(selection_context.__file__)}
    return {"scope": "New synthetic rows only; native shortlist/schema/target checks, not authorization or model accuracy",
            "added_rows_checked": len(rows) - retained, "explicit_target_checks": target_checks,
            "dataset_sha256": hashlib.sha256(payload).hexdigest(),
            "native_source_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sources.items()},
            "passed": True}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--management-planner", type=Path, required=True)
    p.add_argument("--design-planner", type=Path, required=True)
    p.add_argument("--facturation-actions", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = audit(a.dataset, a.management_planner, a.design_planner, a.facturation_actions)
    with a.output.open("x") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))
