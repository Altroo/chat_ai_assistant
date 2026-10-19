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


def rows(count, application, prefix, fields=0):
    result = []
    for i in range(count):
        tool = f"tool_{i % 9}"
        properties = {"query": {"type": "string"}, "period": {
            "type": "string", "enum": ["current_year", "previous_year"]}}
        arguments = {"query": f"{prefix}-{i}", "period": (
            "current_year" if i % 2 else "previous_year")}
        if fields and tool == "tool_5":
            properties.update({f"field_{j}": {"type": "string"} for j in range(fields)})
            arguments[f"field_{(i // 9) % fields}"] = f"VALUE-{i}"
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
        self.training = (rows(2069, "facturation", "BASE-FACT")
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

    def prepare(self, name="candidate"):
        return subject.prepare(self.source, self.extra, self.root / name)

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
        self.training = (rows(2069, "facturation", "BASE-FACT")
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

    def test_outputs_are_deterministic(self):
        with self.approved():
            self.prepare("first")
            self.prepare("second")
        for name in ("train.jsonl", "valid.jsonl", "retained-plan.json", "manifest.json"):
            self.assertEqual((self.root / "first" / name).read_bytes(),
                             (self.root / "second" / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
