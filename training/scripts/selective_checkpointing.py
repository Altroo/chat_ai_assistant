"""Explicit text-layer checkpoint masks for isolated numerical diagnostics.

Call only after configure_text_lora(..., checkpointing=True). This helper does
not load a model, launch a workload, change a training script, or establish
numerical equivalence. The diagnostic caller must supply the actual framework
decoder class and checkpoint function and verify gradients and updates.
"""
from functools import partial


class TextCheckpointMask:
    """Apply and observe a mask without changing vision/parent checkpoint flags."""

    def __init__(self, model, enabled_indices, *, decoder_type, checkpoint_fn):
        indices = tuple(enabled_indices)
        if (not indices or any(type(i) is not int for i in indices)
                or len(set(indices)) != len(indices)
                or any(i < 0 or i >= 24 for i in indices)):
            raise ValueError("A nonempty unique set of text indices 0 through 23 is required")
        if not isinstance(decoder_type, type) or not callable(checkpoint_fn):
            raise ValueError("Actual decoder class and checkpoint function are required")
        base = model.get_base_model()
        text = base.model.language_model
        layers = tuple(text.layers)
        if len(layers) != 24 or base.config.text_config.num_hidden_layers != 24:
            raise ValueError("Diagnostic requires exactly 24 text decoder layers")
        if len({id(layer) for layer in layers}) != 24:
            raise ValueError("Text decoder layers must be distinct")
        if base.config.use_cache is not False or text.config.use_cache is not False:
            raise ValueError("Model and text cache must be disabled")
        if model.training is not True:
            raise ValueError("Diagnostic model must already be in training mode")
        originals = []
        for layer in layers:
            function = getattr(layer, "_gradient_checkpointing_func", None)
            if (not isinstance(layer, decoder_type) or layer.training is not True
                    or layer.gradient_checkpointing is not True
                    or layer.block_type not in ("linear_attention", "full_attention")
                    or not isinstance(function, partial)
                    or function.func is not checkpoint_fn or function.args
                    or function.keywords != {"use_reentrant": False}):
                raise ValueError("Expected initialized nonreentrant text checkpointing")
            originals.append(function)
        layer_ids = {id(layer) for layer in layers}
        other = []
        for _, module in model.named_modules():
            if id(module) not in layer_ids and hasattr(module, "gradient_checkpointing"):
                other.append((module, module.gradient_checkpointing,
                              getattr(module, "_gradient_checkpointing_func", None)))
        self.model = model
        self.base = base
        self.text = text
        self.layers = layers
        self.enabled = frozenset(indices)
        self.originals = tuple(originals)
        self.other = tuple(other)
        self.counts = [0] * 24
        self.active = False
        self.closed = False
        self.wrappers = tuple(self._wrapper(i, fn) for i, fn in enumerate(originals))
        # All validation above occurs before the first model mutation.
        for i, layer in enumerate(layers):
            layer.gradient_checkpointing = i in self.enabled
            layer._gradient_checkpointing_func = self.wrappers[i]

    def _wrapper(self, index, original):
        def observed(*args, **kwargs):
            if not self.active:
                raise RuntimeError("Checkpoint call outside an observed diagnostic step")
            self.counts[index] += 1
            return original(*args, **kwargs)
        return observed

    def _check_state(self):
        if self.closed:
            raise RuntimeError("Checkpoint mask is closed")
        if (self.model.training is not True or self.base.config.use_cache is not False
                or self.text.config.use_cache is not False):
            raise RuntimeError("Diagnostic training or cache configuration changed")
        for i, layer in enumerate(self.layers):
            if (layer.training is not True
                    or layer.gradient_checkpointing is not (i in self.enabled)
                    or layer._gradient_checkpointing_func is not self.wrappers[i]):
                raise RuntimeError("Text checkpoint configuration changed")
        for module, flag, function in self.other:
            if (module.gradient_checkpointing is not flag
                    or getattr(module, "_gradient_checkpointing_func", None) is not function):
                raise RuntimeError("Nontext checkpoint configuration changed")

    def begin_step(self):
        self._check_state()
        if self.active:
            raise RuntimeError("Previous diagnostic step has not finished")
        self.counts = [0] * 24
        self.active = True

    def end_step(self):
        self._check_state()
        if not self.active:
            raise RuntimeError("No diagnostic step is active")
        self.active = False
        expected = [int(i in self.enabled) for i in range(24)]
        if self.counts != expected:
            raise RuntimeError("Actual checkpoint calls do not match the text mask")
        return [
            {"index": i, "block_type": layer.block_type,
             "checkpointing": i in self.enabled, "checkpoint_calls": self.counts[i]}
            for i, layer in enumerate(self.layers)
        ]

    def close(self):
        if not self.closed:
            for layer, original in zip(self.layers, self.originals):
                layer.gradient_checkpointing = True
                layer._gradient_checkpointing_func = original
            self.active = False
            self.closed = True

    def __enter__(self):
        self._check_state()
        return self

    def __exit__(self, *_):
        self.close()
