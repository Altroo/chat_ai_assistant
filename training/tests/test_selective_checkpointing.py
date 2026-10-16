"""Checkpoint-mask contract tests with synthetic objects, never model weights."""
from functools import partial
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from selective_checkpointing import TextCheckpointMask


def checkpoint(function, *args, use_reentrant, **kwargs):
    if use_reentrant is not False:
        raise AssertionError("Checkpoint semantics changed")
    return function(*args, **kwargs)


class Decoder:
    def __init__(self, index):
        self.training = True
        self.gradient_checkpointing = True
        self.block_type = "full_attention" if index % 4 == 3 else "linear_attention"
        self._gradient_checkpointing_func = partial(checkpoint, use_reentrant=False)

    def forward(self, value):
        if self.training and self.gradient_checkpointing:
            return self._gradient_checkpointing_func(lambda x: x + 1, value)
        return value + 1


class Model:
    def __init__(self):
        self.training = True
        self.vision = Decoder(0)
        self.layers = [Decoder(i) for i in range(24)]
        self.text = SimpleNamespace(layers=self.layers, config=SimpleNamespace(use_cache=False))
        self.base = SimpleNamespace(model=SimpleNamespace(language_model=self.text),
            config=SimpleNamespace(use_cache=False, text_config=SimpleNamespace(num_hidden_layers=24)))

    def get_base_model(self):
        return self.base

    def named_modules(self):
        # Vision is deliberately first, as in the real multimodal model.
        yield "vision", self.vision
        yield from ((f"text.{i}", layer) for i, layer in enumerate(self.layers))

    def forward(self, value=0):
        for layer in self.layers:
            value = layer.forward(value)
        return value


class TextCheckpointMaskTests(unittest.TestCase):
    def make(self, model, indices=range(0, 24, 2)):
        return TextCheckpointMask(model, indices, decoder_type=Decoder, checkpoint_fn=checkpoint)

    def snapshot(self, model):
        return [(module.gradient_checkpointing, module._gradient_checkpointing_func)
                for _, module in model.named_modules()]

    def test_selective_and_full_masks_observe_actual_text_calls(self):
        for indices in (range(24), range(0, 24, 2)):
            model = Model()
            before = self.snapshot(model)
            with self.make(model, indices) as mask:
                for _ in range(2):
                    mask.begin_step()
                    self.assertEqual(model.forward(), 24)
                    report = mask.end_step()
                    self.assertEqual([r["index"] for r in report if r["checkpointing"]], list(indices))
                    self.assertEqual(sum(r["checkpoint_calls"] for r in report), len(indices))
                    self.assertEqual([r["block_type"] for r in report],
                                     [layer.block_type for layer in model.layers])
                self.assertEqual((model.vision.gradient_checkpointing,
                                  model.vision._gradient_checkpointing_func), before[0])
            self.assertEqual(self.snapshot(model), before)

    def test_invalid_indices_reject_before_mutation(self):
        for indices in ([], [0, 0], [-1], [24], [True], [1.0], ["1"]):
            model = Model()
            before = self.snapshot(model)
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                self.make(model, indices)
            self.assertEqual(self.snapshot(model), before)

    def test_invalid_setup_rejects_before_mutation(self):
        def wrong_function(m):
            m.layers[-1]._gradient_checkpointing_func = partial(checkpoint, use_reentrant=True)
        mutations = [
            lambda m: setattr(m, "training", False),
            lambda m: setattr(m.base.config, "use_cache", True),
            lambda m: setattr(m.text.config, "use_cache", True),
            lambda m: setattr(m.base.config.text_config, "num_hidden_layers", 23),
            lambda m: setattr(m.layers[-1], "training", False),
            lambda m: setattr(m.layers[-1], "gradient_checkpointing", False),
            lambda m: setattr(m.layers[-1], "block_type", "unknown"),
            wrong_function,
            lambda m: m.layers.__setitem__(23, m.layers[0]),
        ]
        for change in mutations:
            model = Model()
            change(model)
            before = self.snapshot(model)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.make(model)
            self.assertEqual(self.snapshot(model), before)

    def test_wrong_decoder_or_function_rejects(self):
        model = Model()
        before = self.snapshot(model)
        for kwargs in ({"decoder_type": dict, "checkpoint_fn": checkpoint},
                       {"decoder_type": Decoder, "checkpoint_fn": lambda *a: None}):
            with self.assertRaises(ValueError):
                TextCheckpointMask(model, [0], **kwargs)
            self.assertEqual(self.snapshot(model), before)

    def test_missing_extra_and_disabled_layer_calls_fail(self):
        for mode in ("missing", "extra", "disabled"):
            model = Model()
            with self.make(model) as mask:
                mask.begin_step()
                if mode != "missing":
                    model.forward()
                    index = 0 if mode == "extra" else 1
                    model.layers[index]._gradient_checkpointing_func(lambda: None)
                with self.assertRaisesRegex(RuntimeError, "Actual checkpoint calls"):
                    mask.end_step()

    def test_call_outside_step_and_nested_step_fail(self):
        model = Model()
        with self.make(model) as mask:
            with self.assertRaisesRegex(RuntimeError, "outside"):
                model.forward()
            with self.assertRaisesRegex(RuntimeError, "No diagnostic"):
                mask.end_step()
            mask.begin_step()
            with self.assertRaisesRegex(RuntimeError, "Previous diagnostic"):
                mask.begin_step()
            model.forward()
            mask.end_step()
        with self.assertRaisesRegex(RuntimeError, "closed"):
            mask.begin_step()

    def test_flag_function_training_and_cache_tampering_fail(self):
        mutations = [
            lambda m: setattr(m.layers[0], "gradient_checkpointing", False),
            lambda m: setattr(m.layers[1], "gradient_checkpointing", True),
            lambda m: setattr(m.layers[0], "_gradient_checkpointing_func", checkpoint),
            lambda m: setattr(m.layers[0], "training", False),
            lambda m: setattr(m, "training", False),
            lambda m: setattr(m.text.config, "use_cache", True),
            lambda m: setattr(m.vision, "gradient_checkpointing", False),
            lambda m: setattr(m.vision, "_gradient_checkpointing_func", checkpoint),
        ]
        for change in mutations:
            model = Model()
            with self.make(model) as mask:
                mask.begin_step()
                model.forward()
                change(model)
                with self.subTest(change=change), self.assertRaisesRegex(RuntimeError, "changed"):
                    mask.end_step()

    def test_exception_restores_owned_text_configuration(self):
        model = Model()
        before = self.snapshot(model)
        with self.assertRaisesRegex(RuntimeError, "test failure"):
            with self.make(model):
                raise RuntimeError("test failure")
        self.assertEqual(self.snapshot(model), before)


if __name__ == "__main__":
    unittest.main()
