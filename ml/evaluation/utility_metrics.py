"""
Model Utility Metrics — Perplexity, Loss, and Validation Evaluation.

Per Doc 08 (§6): Evaluates causal LM utility via validation loss and perplexity:
    PPL = exp(mean_token_negative_log_likelihood)
"""

import math
from typing import Any
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer


def evaluate_model_loss_and_ppl(
    model: AutoModelForCausalLM | Any,
    texts: list[str],
    tokenizer: AutoTokenizer,
    max_length: int = 128,
) -> dict[str, float]:
    """
    Evaluates cross-entropy loss and perplexity over a list of texts.
    Accepts standard PyTorch AutoModelForCausalLM or SISAEnsemble.
    """
    if not texts:
        return {"loss": 0.0, "perplexity": 1.0}

    total_loss = 0.0
    total_samples = 0

    for text in texts:
        inputs = tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors="pt",
        )
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]

        if hasattr(model, "compute_loss"):
            # SISA Ensemble
            loss = model.compute_loss(input_ids, attention_mask)
        else:
            # Single PyTorch model
            with torch.no_grad():
                out = model(input_ids=input_ids, attention_mask=attention_mask, labels=input_ids)
                loss = out.loss.item()

        total_loss += loss
        total_samples += 1

    avg_loss = total_loss / max(1, total_samples)
    ppl = math.exp(min(100.0, avg_loss))  # clamp exponent to avoid overflow

    return {
        "loss": round(avg_loss, 4),
        "perplexity": round(ppl, 2),
        "samples": total_samples,
    }
