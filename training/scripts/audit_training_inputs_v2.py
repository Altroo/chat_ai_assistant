"""Extend a mechanics rehearsal with declared bilingual curriculum coverage.

Selection uses training inputs only. Existing audits and their default selection
remain unchanged. This does not predict validation or acceptance accuracy.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import json
import re

import audit_training_inputs as base
from training_schedule import complete_epoch_order


def extend_rehearsal(rows, original, categories, maximum=96):
    categories = tuple(categories)
    if (not categories or len(categories) != len(set(categories)) or
            any(not isinstance(c, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", c) for c in categories)):
        raise ValueError("Distinct explicit curriculum categories required")
    groups = defaultdict(list)
    for index, row in enumerate(rows):
        category = row.get("curriculum_category")
        if category in categories:
            if row.get("language") not in ("en", "fr"):
                raise ValueError("Category coverage requires explicit English/French labels")
            groups[(row["application"], category, row["language"])].append(index)
    if {group[1] for group in groups} != set(categories):
        raise ValueError("Requested curriculum category is absent")
    for app, category in {(group[0], group[1]) for group in groups}:
        if {lang for a, c, lang in groups if (a, c) == (app, category)} != {"en", "fr"}:
            raise ValueError("Each curriculum category needs both languages")
    coverage = []
    for group in sorted(groups):
        index = min(groups[group], key=lambda i: (base.digest(base.model_input_key(rows[i]).encode()), i))
        coverage.append({"application": group[0], "category": group[1], "language": group[2], "row_index": index})
    selected = sorted(set(original["row_indices"]) | {item["row_index"] for item in coverage})
    if type(maximum) is not int or maximum < 1 or len(selected) > maximum:
        raise ValueError("Rehearsal budget cannot cover declared curriculum")
    selected = [selected[i] for i in complete_epoch_order([rows[i] for i in selected])]
    result = deepcopy(original)
    result.update(row_indices=selected, count=len(selected),
        by_application=dict(Counter(rows[i]["application"] for i in selected)),
        selected_rows_sha256=base.digest(base.encoded([rows[i] for i in selected]).encode()),
        base_selection_count=original["count"], curriculum_categories=sorted(categories),
        category_coverage=coverage, selection_contract="tool-and-bilingual-category-v1")
    result["limitations"] = [*result["limitations"],
        "One deterministic input per declared application/category/language does not cover every example or prove learning."]
    return result


def audit(data, maximum_rehearsal=96, window=300, *, categories=()):
    result = base.audit(data, maximum_rehearsal, window)
    if not categories:
        return result
    raw = (data / "train.jsonl").read_bytes()
    if base.digest(raw) != result["input_sha256"]["train"]:
        raise ValueError("Training data changed before category selection")
    rows = [json.loads(line) for line in raw.splitlines()]
    result["rehearsal"] = extend_rehearsal(rows, result["rehearsal"], categories, maximum_rehearsal)
    return result
