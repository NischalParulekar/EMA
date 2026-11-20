"""Residual-stream readout with forward hooks.

`residuals` returns the output of decoder block `layer - 1`, which is
`hidden_states[layer]` in Hugging Face's indexing (0 = embeddings). The
forward pass stops after the deepest requested block, so the remaining layers
and the LM head (a 32k x 152k logit matrix) are never computed.
"""

from __future__ import annotations

import torch


class _Stop(Exception):
    pass


def _blocks(model):
    return model.model.layers


@torch.inference_mode()
def residuals(model, input_ids: list[int], layers: list[int], positions: list[int] | None = None,
              start: int = 0) -> dict[int, torch.Tensor]:
    """Float32 CPU tensors per layer: rows at `positions`, or the mean over tokens [start:] if positions is None."""
    out: dict[int, torch.Tensor] = {}
    deepest = max(layers)

    def hook_for(layer):
        def hook(_module, _inputs, output):
            h = (output[0] if isinstance(output, tuple) else output)[0].float()
            out[layer] = (h[positions] if positions is not None else h[start:].mean(0, keepdim=True)).cpu()
            if layer == deepest:
                raise _Stop
        return hook

    handles = [_blocks(model)[layer - 1].register_forward_hook(hook_for(layer)) for layer in layers]
    try:
        ids = torch.tensor([input_ids], device=model.device)
        model.model(input_ids=ids, use_cache=False)
    except _Stop:
        pass
    finally:
        for h in handles:
            h.remove()
    return out
