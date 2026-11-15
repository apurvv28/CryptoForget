"""
SISA Ensemble Aggregator for Causal Language Models.

Per Doc 01 (§7): For causal language models, aggregate output distributions/logits
rather than averaging independently trained model weights.
"""

from pathlib import Path
from typing import Any
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

from ml.training.checkpoint import CheckpointManager


class SISAEnsemble:
    """
    Ensemble of K SISA shard models.
    Produces predictions by aggregating output logits across all shards.
    """

    def __init__(
        self,
        model_path: str = "./models/distilgpt2",
        checkpoint_dir: str = "./data/checkpoints",
        num_shards: int = 2,
        final_slice_id: int = 2,
    ):
        self.model_path = Path(model_path)
        self.num_shards = num_shards
        self.final_slice_id = final_slice_id
        self.checkpoint_manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load models for each shard at the final slice
        self.models: list[AutoModelForCausalLM] = []
        for shard_id in range(self.num_shards):
            m = AutoModelForCausalLM.from_pretrained(str(self.model_path))
            m.to("cpu")
            self.checkpoint_manager.load_slice_checkpoint(
                shard_id=shard_id,
                slice_id=self.final_slice_id,
                model=m,
                restore_rng=False,
            )
            m.eval()
            self.models.append(m)

    @torch.no_grad()
    def get_aggregated_logits(self, input_ids: torch.Tensor, attention_mask: torch.Tensor | None = None) -> torch.Tensor:
        """
        Compute uniform average logits across all K shard models.
        """
        logits_list = []
        for model in self.models:
            out = model(input_ids=input_ids, attention_mask=attention_mask)
            logits_list.append(out.logits)

        # Average logits across models
        stacked = torch.stack(logits_list, dim=0)  # [K, batch, seq_len, vocab_size]
        avg_logits = torch.mean(stacked, dim=0)
        return avg_logits

    @torch.no_grad()
    def compute_loss(self, input_ids: torch.Tensor, attention_mask: torch.Tensor | None = None) -> float:
        """
        Compute cross-entropy loss of the ensemble on a text sequence.
        """
        logits = self.get_aggregated_logits(input_ids, attention_mask)
        # Shift logits and labels for causal LM loss calculation
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = input_ids[..., 1:].contiguous()
        loss = F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            reduction="mean",
        )
        return loss.item()

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 50,
        temperature: float = 0.7,
        top_k: int = 50,
    ) -> str:
        """
        Autoregressively generate text by aggregating next-token logits at each step.
        """
        input_ids = self.tokenizer(prompt, return_tensors="pt")["input_ids"]

        curr_ids = input_ids.clone()
        for _ in range(max_new_tokens):
            avg_logits = self.get_aggregated_logits(curr_ids)
            next_token_logits = avg_logits[:, -1, :] / max(1e-5, temperature)

            # Top-k filtering
            if top_k > 0:
                indices_to_remove = next_token_logits < torch.topk(next_token_logits, top_k)[0][..., -1, None]
                next_token_logits[indices_to_remove] = -float("Inf")

            probs = F.softmax(next_token_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            curr_ids = torch.cat([curr_ids, next_token], dim=-1)

            if next_token.item() == self.tokenizer.eos_token_id:
                break

        return self.tokenizer.decode(curr_ids[0], skip_special_tokens=True)
