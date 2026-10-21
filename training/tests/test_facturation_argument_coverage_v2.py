"""Semantic and leakage guards for TRAIN-only correction, not model scores."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import prepare_facturation_argument_coverage_v2 as g
from test_facturation_semantic_correction_v2 import source_rows


def synthetic_source():
    data = source_rows()
    for n in (49, 53):
        row = data[n - 1]
        row["messages"][-1]["tool_calls"][0]["function"] = {
            "name": "search_payments", "arguments": {"query": "SYN-Parent"}}
        template = deepcopy(row["tools"][0])
        template["function"]["name"] = "search_payments"
        template["function"]["parameters"]["properties"]["query"] = {"type": "string"}
        row["tools"].append(template)
    for n, lang in ((497, "en"), (499, "fr")):
        row = data[n - 1]
        row["tools"] = [t for t in row["tools"] if t["function"]["name"] in ("navigate", "clarify")]
        row["messages"][-1]["tool_calls"][0]["function"] = {
            "name": "clarify", "arguments": {"reason": "unsupported", "language": lang}}
    return data


class ArgumentCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = synthetic_source()
        cls.generated = g.generate(cls.source)

    def changed(self, family):
        data = deepcopy(self.generated)
        row = next(r for r in data if r["augmentation"]["family"] == family)
        return data, row, row["messages"][-1]["tool_calls"][0]["function"]["arguments"]

    def test_balanced_pure_generation_preserves_permissions_and_history(self):
        before = deepcopy(self.source)
        self.assertEqual(g.generate(self.source), self.generated)
        self.assertEqual(before, self.source)
        self.assertEqual(len(self.generated), 80)
        self.assertEqual(Counter(r["language"] for r in self.generated), {"en": 40, "fr": 40})
        for row in self.generated:
            parent = self.source[row["augmentation"]["source_line"] - 1]
            self.assertEqual(row["tools"], parent["tools"])
            self.assertEqual(row["messages"][:-2], parent["messages"][:-2])

    def test_every_semantic_factor_cell_occurs_once(self):
        cells = Counter()
        for row in self.generated:
            f = row["augmentation"]["factors"]
            family = row["augmentation"]["family"]
            keys = {"literal_field_boundaries": ("resource", "style", "variant"),
                    "unpaid_filter_presence": ("profile", "unpaid_requested"),
                    "inclusive_exclusive_dates": ("anchor", "mode"),
                    "available_payment_tool": ("query", "available")}[family]
            cells[(family, row["language"], *(f[k] for k in keys))] += 1
        self.assertEqual(len(cells), 80)
        self.assertEqual(set(cells.values()), {1})

    def test_truncated_literal_and_omitted_second_field_are_rejected(self):
        for mutation in ("truncate", "omit"):
            data, _, args = self.changed("literal_field_boundaries")
            if mutation == "truncate":
                args["changes"]["remarque"] = args["changes"]["remarque"].split()[0]
            else:
                del args["changes"]["date_echeance"]
            with self.assertRaisesRegex(ValueError, "literal"):
                g.validate(data, self.source)

    def test_filter_omission_and_unsolicited_unpaid_are_rejected(self):
        for mutation in ("omit_client", "unsolicited_unpaid"):
            data, _, args = self.changed("unpaid_filter_presence")
            if mutation == "omit_client":
                del args["client_name"]
            else:
                args["unpaid"] = True
            with self.assertRaisesRegex(ValueError, "Unpaid"):
                g.validate(data, self.source)

    def test_real_leap_calendar_boundaries(self):
        data = [r for r in self.generated
                if r["augmentation"]["family"] == "inclusive_exclusive_dates"
                and r["augmentation"]["factors"]["anchor"] == "2036-02-29"]
        expected = {"lower_inclusive": {"date_from": "2036-02-29"},
                    "lower_exclusive": {"date_from": "2036-03-01"},
                    "upper_inclusive": {"date_to": "2036-02-29"},
                    "upper_exclusive": {"date_to": "2036-02-28"}}
        for row in data:
            call = g.helper().target(row)
            self.assertEqual(call["arguments"], expected[row["augmentation"]["factors"]["mode"]])
        bad, _, args = self.changed("inclusive_exclusive_dates")
        args["date_from"] = "2035-05-01"
        with self.assertRaisesRegex(ValueError, "calendar"):
            g.validate(bad, self.source)

    def test_same_payment_request_obeys_different_offered_tools(self):
        pairs = {}
        for row in self.generated:
            if row["augmentation"]["family"] != "available_payment_tool":
                continue
            key = (row["language"], row["augmentation"]["factors"]["query"])
            pairs.setdefault(key, []).append(row)
        self.assertEqual(len(pairs), 8)
        for pair in pairs.values():
            self.assertEqual(pair[0]["messages"][-2]["content"], pair[1]["messages"][-2]["content"])
            self.assertEqual({g.helper().target(r)["name"] for r in pair}, {"search_payments", "clarify"})
            self.assertNotIn("search_payments", [t["function"]["name"] for t in pair[1]["tools"]])

    def test_unoffered_tool_and_changed_context_rejected(self):
        bad = deepcopy(self.source)
        n = g.PARENTS["payments"]["en"]
        bad[n - 1]["tools"] = [t for t in bad[n - 1]["tools"]
                               if t["function"]["name"] != "search_payments"]
        with self.assertRaises(ValueError):
            g.generate(bad)
        data, row, _ = self.changed("literal_field_boundaries")
        row["messages"][0]["content"] += " changed"
        with self.assertRaisesRegex(ValueError, "context"):
            g.validate(data, self.source)

    def test_evaluation_answers_never_touched(self):
        class Forbidden:
            def __deepcopy__(self, memo):
                raise AssertionError("Evaluation answer copied")
        row = deepcopy(self.generated[0])
        row["messages"][-1] = {"role": "assistant", "content": Forbidden(), "tool_calls": Forbidden()}
        row["expected"] = Forbidden()
        envelope = g.input_only(row)
        self.assertEqual(envelope["messages"][-1]["role"], "user")
        self.assertNotIn("expected", envelope)

    def test_clarify_injection_and_tool_order_cannot_hide_overlap(self):
        row = deepcopy(self.generated[0])
        held = deepcopy(row)
        held["offered_tool_schemas"] = list(reversed([
            t for t in held["tools"] if t["function"]["name"] != "clarify"]))
        self.assertEqual(g.input_only(row), g.input_only(held))
        with self.assertRaisesRegex(ValueError, "overlaps"):
            g.exclusions([], [row], [held])

    def test_near_duplicate_date_identifier_changes_are_rejected(self):
        row = deepcopy(self.generated[0])
        held = deepcopy(row)
        held["messages"][-2]["content"] = held["messages"][-2]["content"].replace(
            "84001", "99001").replace("2035-05-12", "2037-01-01")
        with self.assertRaisesRegex(ValueError, "near duplicate"):
            g.exclusions([], [row], [held])

    def test_legacy_collision_is_disclosed_without_relabeling(self):
        row = self.generated[0]
        report = g.exclusions([row], [], [row])
        self.assertEqual(report["legacy_exact_overlap_under_stronger_normalization"], 1)
        self.assertFalse(report["evaluation_answers_consulted"])

    def test_changed_pinned_replay_and_existing_output_fail_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("base", "source", "native"):
                (root / name).mkdir()
            (root / "base/train.jsonl").write_text("{}\n")
            (root / "base/valid.jsonl").write_text("{}\n")
            (root / "source/train.jsonl").write_text("{}\n")
            out = root / "data"
            with self.assertRaisesRegex(ValueError, "Pinned replay"):
                g.prepare(root / "base", root / "source", root / "native", out, [])
            self.assertFalse(out.exists())
            out.mkdir()
            with self.assertRaisesRegex(ValueError, "isolated"):
                g.prepare(root / "base", root / "source", root / "native", out, [])


if __name__ == "__main__":
    unittest.main()
