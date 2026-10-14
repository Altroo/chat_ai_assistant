"""Training-data integrity and native semantic boundaries, without inference."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_shared_v5r8 as m


class R8CurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = m.ROOT / "training/datasets/shared-v5r7-en-fr"
        cls.original = list(map(json.loads, (cls.parent / "train.jsonl").read_text().splitlines()))
        cls.extra = m.additions(cls.original)
        folder = m.ROOT / "training/datasets/shared-v5r8-en-fr"
        cls.generated = list(map(json.loads, (folder / "train.jsonl").read_text().splitlines()))
        cls.manifest = json.loads((folder / "manifest.json").read_text())

    def test_parent_and_validation_bytes_retained(self):
        out = m.ROOT / "training/datasets/shared-v5r8-en-fr"
        self.assertTrue((out / "train.jsonl").read_bytes().startswith((self.parent / "train.jsonl").read_bytes()))
        self.assertEqual((out / "valid.jsonl").read_bytes(), (self.parent / "valid.jsonl").read_bytes())
        self.assertEqual(len(self.original), 2065)
        self.assertEqual(self.manifest["counts"]["added"], len(self.extra))
        self.assertEqual(len(self.generated), 2065 + 274)

    def test_all_native_metadata_checks_recorded(self):
        self.assertEqual(set(self.manifest["native_metadata"]), {"facturation", "management_projet", "design_workflow"})
        for proofs in self.manifest["native_metadata"].values():
            self.assertIn("chat_ai/tools.py", proofs)
            self.assertTrue(all(len(h) == 64 for h in proofs.values()))

    def test_exclusive_bounds_cross_calendar_boundaries(self):
        before = [m.function(r)["arguments"] for r in self.extra if r["curriculum_category"] == "compound_date_before"]
        after = [m.function(r)["arguments"] for r in self.extra if r["curriculum_category"] == "compound_date_after"]
        self.assertTrue(any(r.get("date_to") == "2032-02-29" for r in before))
        self.assertTrue(any(r.get("date_to") == "2032-12-31" for r in before))
        self.assertTrue(any(r.get("date_from") == "2032-03-01" for r in after))
        self.assertTrue(any(r.get("date_from") == "2033-05-01" for r in after))
        self.assertTrue(all("date_from" not in r for r in before))
        self.assertTrue(all("date_to" not in r for r in after))

    def test_compound_filters_survive_boundary_changes(self):
        for row in self.extra:
            if not row["curriculum_category"].startswith("compound_date_"):
                continue
            target = m.function(row)
            args = target["arguments"]
            if target["name"] in ("search_invoices", "search_quotes", "search_documents", "search_payments"):
                self.assertIn("client_name", args)
                self.assertIn("product_name", args)
            if target["name"] == "search_operations":
                self.assertIn("product_name", args)
                self.assertIn("location_name", args)

    def test_all_priority_values_and_both_resources(self):
        rows = [r for r in self.extra if r["curriculum_category"] == "priority_enum"]
        triples = {(m.function(r)["arguments"]["resource"], m.function(r)["arguments"]["changes"]["priority"], r["language"]) for r in rows}
        self.assertEqual(triples, {(r, p, lang) for r in ("project", "task") for p in ("low", "medium", "high", "urgent") for lang in ("fr", "en")})

    def test_unavailable_supplier_aggregate_never_becomes_project_total(self):
        rows = [r for r in self.extra if r["curriculum_category"] == "unsupported_supplier_total"]
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(m.function(r)["name"] == "clarify" and m.function(r)["arguments"]["reason"] == "unsupported" for r in rows))
        self.assertTrue(any("devis" in m.current_request(r) for r in rows))
        self.assertTrue(any("dépenses" in m.current_request(r) for r in rows))

    def test_invalid_financial_labels_fail_pure_semantic_check(self):
        for args in ({"metric": "estimates"}, {"metric": "budget", "period": "current_year"},
                     {"metric": "estimates", "project_name": "Synthetic", "period": "previous_month"},
                     {"metric": "expenses", "period": "custom"},
                     {"metric": "profit", "date_from": "2034-01-01"}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                m.validate_semantics("management_projet", "financial_summary", args)
        m.validate_semantics("management_projet", "financial_summary", {"metric": "estimates", "project_name": "Synthetic"})
        m.validate_semantics("management_projet", "financial_summary", {"metric": "expenses", "period": "previous_year"})

    def test_wrong_record_selection_is_not_supervised(self):
        rows = [r for r in self.extra if r["curriculum_category"].startswith("ordinal_multifield")]
        words = {"premier": 0, "first": 0, "deuxième": 1, "second": 1, "troisième": 2, "third": 2, "quatrième": 3, "fourth": 3, "cinquième": 4, "fifth": 4}
        for row in rows:
            request = m.current_request(row)
            positions = [p for word, p in words.items() if word in request]
            self.assertEqual(len(positions), 1)
            trusted = m.context(row)
            self.assertEqual(m.function(row)["arguments"]["identifier"], trusted["previous_result_identifiers"][positions[0]])
            self.assertNotEqual(m.function(row)["arguments"]["identifier"], trusted["current_identifier"])

    def test_out_of_range_selection_is_a_clarification(self):
        rows = [r for r in self.extra if r["curriculum_category"] == "ordinal_out_of_range"]
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(m.function(r)["name"] == "clarify" and m.function(r)["arguments"]["reason"] == "missing_details" for r in rows))

    def test_new_training_excludes_every_frozen_request(self):
        fresh = self.generated[len(self.original):]
        payloads, _ = m.assemble(self.parent, fresh, self.manifest["native_metadata"])
        self.assertEqual(payloads["train.jsonl"], (m.ROOT / "training/datasets/shared-v5r8-en-fr/train.jsonl").read_text())
        bad = copy.deepcopy(fresh)
        validation = json.loads((self.parent / "valid.jsonl").read_text().splitlines()[0])
        bad[0]["application"] = validation["application"]
        bad[0]["messages"][-2] = validation["messages"][-2]
        with self.assertRaises(AssertionError):
            m.assemble(self.parent, bad, self.manifest["native_metadata"])

    def test_changed_exclusion_manifest_is_rejected(self):
        fresh = self.generated[len(self.original):]
        original_sha = m.sha
        def tampered(path):
            if path.parent.name == "shared-dialogue-v2-en-fr" and path.name == "manifest.json":
                return "0" * 64
            return original_sha(path)
        with patch.object(m, "sha", side_effect=tampered), self.assertRaisesRegex(AssertionError, "Frozen exclusion manifest"):
            m.assemble(self.parent, fresh, self.manifest["native_metadata"])

    def test_fresh_controls_match_native_context_and_are_not_training(self):
        folder = m.ROOT / "training/datasets/shared-v5r8-fresh-en-fr"
        manifest = json.loads((folder / "manifest.json").read_text())
        rows = list(map(json.loads, (folder / "controls.eval.jsonl").read_text().splitlines()))
        self.assertEqual(len(rows), 48)
        self.assertEqual(m.Counter(r["trusted_context"]["application"] for r in rows),
                         {"facturation": 16, "management_projet": 16, "design_workflow": 16})
        self.assertEqual(m.Counter(r["language"] for r in rows), {"en": 24, "fr": 24})
        self.assertEqual(m.sha(folder / "controls.eval.jsonl"), manifest["files"]["controls.eval.jsonl"])
        self.assertEqual(m.sha(m.ROOT / "training/scripts/prepare_shared_v5r8_controls.py"), manifest["generator_sha256"])
        excluded = {m.key(r["application"], m.current_request(r)) for r in self.generated}
        excluded.update(m.key(r["application"], m.current_request(r)) for r in map(json.loads, (self.parent / "valid.jsonl").read_text().splitlines()))
        for row in rows:
            app = row["trusted_context"]["application"]
            self.assertNotIn(m.key(app, row["messages"][-1]["content"]), excluded)
            if app == "facturation":
                self.assertNotIn("capabilities", row["trusted_context"])
            if row["category"].startswith("read-only"):
                self.assertEqual(row["trusted_context"]["capabilities"], ["read"])
                self.assertNotIn("prepare_change", row["offered_tools"])
                self.assertEqual(row["expected"]["tool"], "clarify")

    def test_recorded_payload_hashes_match(self):
        folder = m.ROOT / "training/datasets/shared-v5r8-en-fr"
        for name, digest in self.manifest["files"].items():
            self.assertEqual(m.sha(folder / name), digest)
        self.assertEqual(m.sha(m.ROOT / "training/scripts/prepare_shared_v5r8.py"), self.manifest["generator_sha256"])
        for name, digest in self.manifest["helper_sha256"].items():
            self.assertEqual(m.sha(m.ROOT / name), digest)
        self.assertIn("design_workflow/models.py", self.manifest["native_metadata"]["design_workflow"])


if __name__ == "__main__":
    unittest.main()
