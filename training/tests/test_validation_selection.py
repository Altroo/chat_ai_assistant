"""Validation checkpoint decisions must be bounded, reproducible and label-free."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validation_selection import ValidationSelection


def report(a=0.1, b=0.2):
    return {"micro": (a + 2 * b) / 3, "macro": (a + b) / 2,
            "by_application": {"facturation": a, "management_projet": b}}


class ValidationSelectionTests(unittest.TestCase):
    def selection(self):
        return ValidationSelection(report(), ("facturation", "management_projet"))

    def test_baseline_remains_selected_when_loss_worsens_or_ties(self):
        selected = self.selection()
        self.assertFalse(selected.observe(10, report(0.2, 0.3)))
        self.assertFalse(selected.observe(20, report()))
        self.assertEqual(selected.best_step, 0)

    def test_best_can_be_intermediate_and_does_not_alias_input(self):
        selected = self.selection()
        result = report(0.05, 0.1)
        self.assertTrue(selected.observe(10, result))
        result["by_application"]["facturation"] = 9
        self.assertFalse(selected.observe(20, report()))
        self.assertEqual(selected.best_step, 10)
        self.assertEqual(selected.best, report(0.05, 0.1))

    def test_nonfinite_negative_missing_or_inconsistent_reject(self):
        for value in (float("nan"), float("inf"), -1, True, "0.1"):
            with self.subTest(loss=value), self.assertRaises(ValueError):
                self.selection().observe(10, {"micro": value, "macro": value,
                                              "by_application": {"facturation": value, "management_projet": value}})
        for bad in ({"micro": .1, "macro": .1, "by_application": {"facturation": .1}},
                    {"micro": .1, "macro": .5, "by_application": {"facturation": .1, "management_projet": .1}}):
            with self.assertRaises(ValueError):
                self.selection().observe(10, bad)

    def test_step_must_increase_and_score_is_application_macro(self):
        selected = self.selection()
        self.assertTrue(selected.observe(10, report(0.2, 0.05)))
        for step in (0, 10, 9, True, 10.5):
            with self.subTest(step=step), self.assertRaises(ValueError):
                selected.observe(step, report())
        self.assertEqual(selected.best_step, 10)
