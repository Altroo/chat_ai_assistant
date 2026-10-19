"""Synthetic corpus fixtures verify preparation guards, not model accuracy."""
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_facturation_entity_pilot_v2 as subject


def rows(count, application, prefix, fields=0, tool_count=9):
    result = []
    for i in range(count):
        tool = f"tool_{i % tool_count}"
        properties = {"query": {"type": "string"}, "period": {
            "type": "string", "enum": ["current_year", "previous_year"]}}
        arguments = {"query": f"{prefix}-{i}", "period": (
            "current_year" if i % 2 else "previous_year")}
        if fields and tool == "tool_5":
            properties.update({f"field_{j}": {"type": "string"} for j in range(fields)})
            arguments[f"field_{(i // tool_count) % fields}"] = f"VALUE-{i}"
        result.append({
            "application": application,
            "messages": [
                {"role": "system", "content": f"Synthetic {application} context."},
                {"role": "user", "content": f"{prefix} request {i}"},
                {"role": "assistant", "tool_calls": [{"function": {
                    "name": tool, "arguments": arguments}}]},
            ],
            "tools": [{"function": {"name": tool, "parameters": {
                "type": "object", "properties": properties,
                "required": ["query"], "additionalProperties": False}}}],
        })
    return result


def critical_rows():
    """Synthetic real tool contracts expose combinations hidden by marginals."""
    values = rows(360, "facturation", "STRUCTURAL", tool_count=18)
    for i, row in enumerate(values):
        function = row["messages"][-1]["tool_calls"][0]["function"]
        tool = function["name"]
        variant = i // 18
        if tool == "tool_0":
            function["name"] = "prepare_change"
            arguments = {"resource": "invoice" if variant % 2 else "quote",
                         "operation": "update", "identifier": i + 1}
            if variant < 14:
                mask = variant // 2 + 1
                arguments["changes"] = {key: f"SYN-{i}" for bit, key in enumerate(
                    ("remarque", "date_echeance", "termes_paiement")) if mask & (1 << bit)}
            else:
                arguments["operation"] = "delete"
            function["arguments"] = arguments
            row["tools"] = [{"function": {"name": "prepare_change", "parameters": {
                "type": "object", "properties": {
                    "resource": {"type": "string"},
                    "operation": {"enum": ["update", "delete"]},
                    "identifier": {"type": "integer"},
                    "changes": {"type": "object", "properties": {
                        key: {"type": "string"} for key in
                        ("remarque", "date_echeance", "termes_paiement")},
                        "additionalProperties": False}},
                "required": ["resource", "operation", "identifier"],
                "additionalProperties": False}}}]
        elif tool == "tool_1":
            function["name"] = "search_payments"
            arguments = {"invoice_number": f"SYN-FAC-{i}"}
            if variant % 4 in (1, 3):
                arguments["limit"] = 3
            if variant % 4 in (2, 3):
                arguments["status"] = "Valide" if variant % 8 < 4 else "Annulé"
            function["arguments"] = arguments
            row["tools"] = [{"function": {"name": "search_payments", "parameters": {
                "type": "object", "properties": {
                    "invoice_number": {"type": "string"}, "limit": {"type": "integer"},
                    "status": {"enum": ["Valide", "Annulé"]}},
                "required": [], "additionalProperties": False}}}]
    return values

def write_rows(path, values):
    path.write_text("".join(json.dumps(row) + "\n" for row in values))


class CorrectivePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.extra = self.root / "supplement"
        self.source.mkdir()
        self.extra.mkdir()
        self.training = (rows(2069, "facturation", "BASE-FACT", 16, tool_count=18)
                         + rows(709, "management_projet", "TRAIN-MP", 12)
                         + rows(325, "design_workflow", "TRAIN-DW"))
        self.validation = (rows(133, "facturation", "VALID-FACT")
                           + rows(78, "management_projet", "VALID-MP")
                           + rows(64, "design_workflow", "VALID-DW"))
        self.supplement = rows(72, "facturation", "EXTRA")
        for i, row in enumerate(self.supplement):
            row["language"] = "en" if i % 2 else "fr"
        write_rows(self.source / "train.jsonl", self.training)
        write_rows(self.source / "valid.jsonl", self.validation)
        write_rows(self.extra / "contrasts.jsonl", self.supplement)
        (self.extra / "manifest.json").write_text('{"synthetic_fixture":true}\n')

    @contextmanager
    def approved(self):
        """Pin synthetic files only; never patch or rewrite real dataset files."""
        source_pins = {name: subject.sha((self.source / name).read_bytes())
                       for name in ("train.jsonl", "valid.jsonl")}
        extra_pins = {name: subject.sha((self.extra / name).read_bytes())
                      for name in ("manifest.json", "contrasts.jsonl")}
        with patch.object(subject.original.entity, "SOURCE_SHA256", source_pins), \
                patch.object(subject.original, "SUPPLEMENT_SHA256", extra_pins):
            with tempfile.TemporaryDirectory(dir=self.root) as temporary:
                reference = Path(temporary) / "approved-reference"
                subject.original.prepare(self.source, self.extra, reference)
                pins = {name: subject.sha((reference / name).read_bytes())
                        for name in subject.REFERENCE_SHA256}
            with patch.object(subject, "REFERENCE_SHA256", pins):
                yield

    def prepare(self, name="candidate", *, facturation_replay_rows=0):
        return subject.prepare(self.source, self.extra, self.root / name,
                               facturation_replay_rows=facturation_replay_rows)

    def test_counts_prefixes_validation_and_sources_are_preserved(self):
        before = {str(p): p.read_bytes() for folder in (self.source, self.extra)
                  for p in folder.iterdir()}
        with self.approved():
            subject.original.prepare(self.source, self.extra, self.root / "reference")
            manifest = self.prepare()
        old = (self.root / "reference/train.jsonl").read_bytes().splitlines()
        new = (self.root / "candidate/train.jsonl").read_bytes().splitlines()
        self.assertEqual(new[:144], old[:144])
        self.assertEqual(new[184:], old[144:])
        self.assertEqual(len(new), 256)
        self.assertEqual(manifest["by_application"],
                         {"facturation": 72, "management_projet": 112, "design_workflow": 72})
        self.assertEqual((self.root / "candidate/valid.jsonl").read_bytes(),
                         (self.source / "valid.jsonl").read_bytes())
        self.assertTrue(all(Path(name).read_bytes() == raw for name, raw in before.items()))

    def test_new_budget_covers_measured_shapes_without_claiming_behavior(self):
        with self.approved():
            subject.original.prepare(self.source, self.extra, self.root / "reference")
            self.prepare()
        old = json.loads((self.root / "reference/retained-plan.json").read_text())
        new = json.loads((self.root / "candidate/retained-plan.json").read_text())
        self.assertTrue(any(info["uncovered"] for info in
                            old["applications"]["management_projet"]["feature_coverage"].values()))
        self.assertTrue(all(not info["uncovered"] for plan in new["applications"].values()
                            for info in plan["feature_coverage"].values()))
        self.assertFalse(new["evaluation_outcomes_used_for_selection"])

    def test_metadata_cannot_claim_training_or_bound_accepted_parent(self):
        with self.approved():
            manifest = self.prepare()
        self.assertEqual(manifest["requested_experimental_parent"],
                         {"selected_step": 2048, "accepted": False, "actual_model_sha256": None})
        self.assertIsNone(manifest["current_pilot_failure_evidence_sha256"])
        for key in ("numerical_admission", "training_executed", "model_accepted",
                    "production_activation", "next_application_training_started"):
            self.assertFalse(manifest[key])
        data = [json.loads(line) for line in
                (self.root / "candidate/train.jsonl").read_text().splitlines()]
        self.assertTrue(all("language" not in row for row in data[72:]))
        self.assertEqual(Counter(row["language"] for row in data[:72]), {"en": 36, "fr": 36})

    def test_overlap_in_an_added_row_is_rejected_before_output(self):
        indices, _ = subject.original.retained(self.training, "management_projet", 112)
        self.validation[0] = deepcopy(self.training[indices[72]])
        write_rows(self.source / "valid.jsonl", self.validation)
        with self.approved(), self.assertRaisesRegex(ValueError, "overlap"):
            self.prepare()
        self.assertFalse((self.root / "candidate").exists())

    def test_unapproved_source_hash_is_rejected(self):
        with self.approved():
            with (self.source / "train.jsonl").open("a") as stream:
                stream.write("\n")
            with self.assertRaisesRegex(ValueError, "Immutable"):
                self.prepare()
        self.assertFalse((self.root / "candidate").exists())

    def test_source_change_after_reference_preparation_is_rejected(self):
        original_prepare = subject.original.prepare

        def changed(*args):
            result = original_prepare(*args)
            path = self.source / "train.jsonl"
            path.write_bytes(path.read_bytes() + b" ")
            return result

        with self.approved(), patch.object(subject.original, "prepare", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "changed during preparation"):
                self.prepare()
        self.assertFalse((self.root / "candidate").exists())

    def test_changed_helper_identity_is_rejected(self):
        with self.approved(), patch.object(subject, "HELPER_SHA256", {}):
            with self.assertRaisesRegex(ValueError, "helper identity"):
                self.prepare()
        self.assertFalse((self.root / "candidate").exists())

    def test_regenerated_reference_cannot_redefine_approved_identity(self):
        original_prepare = subject.original.prepare

        def changed(*args):
            result = original_prepare(*args)
            path = Path(args[2]) / "manifest.json"
            path.write_bytes(path.read_bytes() + b" ")
            return result

        with self.approved(), patch.object(subject.original, "prepare", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "reference identity"):
                self.prepare()
        self.assertFalse((self.root / "candidate").exists())

    def test_unapproved_language_is_rejected(self):
        with self.approved():
            self.supplement[0]["language"] = "ar"
            write_rows(self.extra / "contrasts.jsonl", self.supplement)
            pins = {name: subject.sha((self.extra / name).read_bytes())
                    for name in ("manifest.json", "contrasts.jsonl")}
            with patch.object(subject.original, "SUPPLEMENT_SHA256", pins), \
                    self.assertRaisesRegex(ValueError, "English/French"):
                self.prepare()
        self.assertFalse((self.root / "candidate").exists())

    def test_missing_coverage_cannot_be_hidden(self):
        self.training = (rows(2069, "facturation", "BASE-FACT", 16, tool_count=18)
                         + rows(709, "management_projet", "TRAIN-MP", 43)
                         + rows(325, "design_workflow", "TRAIN-DW"))
        write_rows(self.source / "train.jsonl", self.training)
        with self.approved(), self.assertRaisesRegex(ValueError, "shape/enum"):
            self.prepare()
        self.assertFalse((self.root / "candidate").exists())

    def test_existing_or_nested_output_is_rejected(self):
        (self.root / "candidate").mkdir()
        for output in (self.root / "candidate", self.source / "nested", self.extra / "nested"):
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, "isolated"):
                subject.prepare(self.source, self.extra, output)

    def test_expanded_replay_preserves_default_rows_sources_and_validation(self):
        before = {str(p): p.read_bytes() for folder in (self.source, self.extra)
                  for p in folder.iterdir()}
        with self.approved():
            self.prepare("default")
            manifest = self.prepare("expanded", facturation_replay_rows=128)
        old = (self.root / "default/train.jsonl").read_bytes().splitlines()
        new = (self.root / "expanded/train.jsonl").read_bytes().splitlines()
        self.assertEqual(new[:72], old[:72])
        self.assertEqual(new[200:], old[72:])
        self.assertEqual(len(new), 384)
        source_rows = set((self.source / "train.jsonl").read_bytes().splitlines())
        self.assertTrue(all(line in source_rows for line in new[72:200]))
        self.assertTrue(all(Path(name).read_bytes() == raw for name, raw in before.items()))
        self.assertEqual((self.root / "expanded/valid.jsonl").read_bytes(),
                         (self.source / "valid.jsonl").read_bytes())
        self.assertEqual(manifest["by_application"],
                         {"facturation": 200, "management_projet": 112, "design_workflow": 72})

    def test_expanded_replay_covers_all_facturation_tools_and_features(self):
        _, before = subject.original.retained(self.training, "facturation", 128)
        self.assertTrue(any(info["uncovered"] for info in before["feature_coverage"].values()))
        with self.approved():
            self.prepare(facturation_replay_rows=128)
        plan = json.loads((self.root / "candidate/retained-plan.json").read_text())
        facturation = plan["applications"]["facturation"]
        self.assertEqual(len(facturation["by_tool"]), 18)
        self.assertEqual(sum(facturation["by_tool"].values()), 128)
        self.assertTrue(all(not info["uncovered"]
                            for info in facturation["feature_coverage"].values()))
        self.assertLess(facturation["first_full_feature_coverage_at"], 128)
        self.assertFalse(plan["evaluation_outcomes_used_for_selection"])

    def test_expanded_replay_metadata_remains_unbound_and_untrained(self):
        with self.approved():
            manifest = self.prepare(facturation_replay_rows=128)
        self.assertEqual(manifest["variant"], "facturation-native-tool-replay")
        self.assertEqual(manifest["facturation_replay_rows"], 128)
        self.assertEqual(manifest["updates_requested"], 384)
        self.assertIsNone(manifest["requested_experimental_parent"]["actual_model_sha256"])
        self.assertIsNone(manifest["current_pilot_failure_evidence_sha256"])
        self.assertFalse(manifest["requested_experimental_parent"]["accepted"])
        for key in ("numerical_admission", "training_executed", "model_accepted",
                    "production_activation", "next_application_training_started"):
            self.assertFalse(manifest[key])
        data = [json.loads(line) for line in
                (self.root / "candidate/train.jsonl").read_text().splitlines()]
        self.assertTrue(all("language" not in row for row in data[72:]))

    def test_development_overlap_in_facturation_replay_is_rejected(self):
        indices, _ = subject.facturation_retained(self.training, 128)
        self.validation[0] = deepcopy(self.training[indices[0]])
        write_rows(self.source / "valid.jsonl", self.validation)
        with self.approved(), self.assertRaisesRegex(ValueError, "overlap"):
            self.prepare(facturation_replay_rows=128)
        self.assertFalse((self.root / "candidate").exists())

    def test_supplement_overlap_in_facturation_replay_is_rejected(self):
        indices, _ = subject.facturation_retained(self.training, 128)
        self.supplement[0] = deepcopy(self.training[indices[0]])
        self.supplement[0]["language"] = "fr"
        write_rows(self.extra / "contrasts.jsonl", self.supplement)
        with self.approved(), self.assertRaisesRegex(ValueError, "Duplicate"):
            self.prepare(facturation_replay_rows=128)
        self.assertFalse((self.root / "candidate").exists())

    def test_insufficient_facturation_replay_coverage_is_rejected(self):
        with self.approved(), self.assertRaisesRegex(ValueError, "every measured shape/enum"):
            self.prepare(facturation_replay_rows=18)
        self.assertFalse((self.root / "candidate").exists())

    def test_invalid_facturation_replay_counts_are_rejected(self):
        for value in (True, -1, 1.5, None):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "non-negative integer"):
                self.prepare(facturation_replay_rows=value)
        self.assertFalse((self.root / "candidate").exists())

    def test_missing_facturation_tool_is_rejected(self):
        altered = deepcopy(self.training)
        for row in altered:
            if row["application"] == "facturation" and row["tools"][0]["function"]["name"] == "tool_17":
                row["tools"][0]["function"]["name"] = "tool_16"
                row["messages"][-1]["tool_calls"][0]["function"]["name"] = "tool_16"
        with self.assertRaisesRegex(ValueError, "18 native tools"):
            subject.facturation_retained(altered, 128)

    def test_expanded_outputs_are_deterministic(self):
        with self.approved():
            self.prepare("expanded-one", facturation_replay_rows=128)
            self.prepare("expanded-two", facturation_replay_rows=128)
        for name in ("train.jsonl", "valid.jsonl", "retained-plan.json", "manifest.json"):
            self.assertEqual((self.root / "expanded-one" / name).read_bytes(),
                             (self.root / "expanded-two" / name).read_bytes())

    def test_priority_conjunctions_preserve_every_edit_and_exact_lookup_shape(self):
        values = critical_rows()
        selected, plan = subject.facturation_retained(values, 128)
        actual_changes, actual_lookups = set(), set()
        expected_changes, expected_lookups = set(), set()
        for i, row in enumerate(values):
            function = row["messages"][-1]["tool_calls"][0]["function"]
            args = function["arguments"]
            if function["name"] == "prepare_change":
                key = (args["resource"], args["operation"], tuple(sorted(args.get("changes", {}))))
                expected_changes.add(key)
                if i in selected:
                    actual_changes.add(key)
            elif function["name"] == "search_payments":
                key = (tuple(sorted(args)), args.get("status"))
                expected_lookups.add(key)
                if i in selected:
                    actual_lookups.add(key)
        self.assertEqual(len(expected_changes), 16)
        self.assertEqual(len(expected_lookups), 6)
        self.assertEqual(actual_changes, expected_changes)
        self.assertEqual(actual_lookups, expected_lookups)
        coverage = plan["priority_conjunction_coverage"]
        self.assertEqual(coverage["selected"], coverage["available"])
        self.assertFalse(coverage["uncovered"])

    def test_marginal_coverage_alone_cannot_satisfy_priority_budget(self):
        values = critical_rows()
        _, plan = subject.facturation_retained(values, 128)
        marginal_budget = plan["first_full_feature_coverage_at"]
        self.assertLess(marginal_budget, plan["first_full_priority_conjunction_coverage_at"])
        with self.assertRaisesRegex(ValueError, "critical or exact-lookup"):
            subject.facturation_retained(values, marginal_budget)

    def test_free_text_and_numeric_values_do_not_inflate_conjunctions(self):
        _, plan = subject.facturation_retained(self.training, 128)
        self.assertEqual(plan["conjunction_coverage"]["tool_0"]["available"], 1)
        self.assertEqual(plan["conjunction_coverage"]["tool_5"]["available"], 16)
        for tool, inventory in plan["conjunction_coverage"].items():
            self.assertEqual(inventory["selected"] + len(inventory["uncovered"]),
                             inventory["available"])

    def test_remaining_combinations_are_reported_without_claiming_full_coverage(self):
        values = rows(720, "facturation", "COMBINATIONS", tool_count=18)
        for i, row in enumerate(values):
            function = row["messages"][-1]["tool_calls"][0]["function"]
            if function["name"] != "tool_5":
                continue
            mask = i // 18 + 1
            function["arguments"] = {f"field_{bit}": f"SYN-{i}" for bit in range(6)
                                     if mask & (1 << bit)}
            row["tools"][0]["function"]["parameters"] = {
                "type": "object", "properties": {f"field_{bit}": {"type": "string"}
                                                 for bit in range(6)},
                "additionalProperties": False}
        _, plan = subject.facturation_retained(values, 24)
        inventory = plan["conjunction_coverage"]["tool_5"]
        self.assertTrue(inventory["uncovered"])
        self.assertLess(inventory["selected"], inventory["available"])
        _, complete = subject.facturation_retained(values, 64)
        full = complete["conjunction_coverage"]["tool_5"]
        self.assertEqual(full["selected"], 40)
        self.assertEqual(full["selected"], full["available"])
        self.assertFalse(full["uncovered"])

    def test_offered_tool_schema_variants_are_kept_as_distinct_bundles(self):
        values = rows(360, "facturation", "BUNDLES", tool_count=18)
        for i, row in enumerate(values):
            if row["tools"][0]["function"]["name"] == "tool_0":
                row["tools"][0]["function"]["parameters"]["properties"]["query"][
                    "maxLength"] = 100 if i % 36 else 200
        _, plan = subject.facturation_retained(values, 64)
        bundles = plan["offered_tool_bundle_coverage"]
        self.assertEqual(bundles["available"], 19)
        self.assertEqual(bundles["selected"], 19)
        self.assertFalse(bundles["uncovered"])

    def test_outputs_are_deterministic(self):
        with self.approved():
            self.prepare("first")
            self.prepare("second")
        for name in ("train.jsonl", "valid.jsonl", "retained-plan.json", "manifest.json"):
            self.assertEqual((self.root / "first" / name).read_bytes(),
                             (self.root / "second" / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
