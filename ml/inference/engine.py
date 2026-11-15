"""
Inference Engine — Model Loading, Dynamic Ensemble Serving, and Generation.

Per Doc 01 (§6): Dynamically loads the active model version or SISA ensemble
from the ModelRegistry. Automatically reflects unlearning updates without service restarts.
"""

from pathlib import Path
import time
from typing import Any
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.config import settings
from ml.registry.model_registry import DeploymentManifest, model_registry


class InferenceEngine:
    """
    Production inference engine that serves either a single base model
    or an ensembled SISA deployment based on ModelRegistry active pointer.
    """

    def __init__(self, model_path: str = "./models/distilgpt2"):
        self.model_path = Path(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Active loaded models cache
        self.active_version: str | None = None
        self.active_models: list[AutoModelForCausalLM] = []
        self._load_active_models()

    def _load_base_model(self) -> AutoModelForCausalLM:
        model = AutoModelForCausalLM.from_pretrained(str(self.model_path))
        model.to("cpu")
        model.eval()
        return model

    def _load_active_models(self) -> None:
        """Loads or refreshes models according to current registry deployment."""
        deployment = model_registry.get_current_deployment()

        if deployment is None or deployment.model_type == "single_baseline":
            # Serve single base model
            self.active_version = "distilgpt2-82M-base"
            self.active_models = [self._load_base_model()]
            return

        if self.active_version == deployment.model_version:
            # Already loaded
            return

        print(f"[InferenceEngine] Loading SISA deployment: {deployment.model_version} (K={deployment.num_shards})")
        models = []
        for shard_id, chk_path in deployment.shard_checkpoints.items():
            m = AutoModelForCausalLM.from_pretrained(str(self.model_path))
            m.to("cpu")
            chk = torch.load(chk_path, map_location="cpu", weights_only=False)
            m.load_state_dict(chk["model_state_dict"])
            m.eval()
            models.append(m)

        self.active_models = models
        self.active_version = deployment.model_version
        print(f"[InferenceEngine] Successfully activated {deployment.model_version}")

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 50,
        temperature: float = 0.7,
        top_k: int = 50,
    ) -> tuple[str, str, int, int, float]:
        """
        Generates text using active deployment.
        Returns (response_text, model_version, prompt_tokens, generated_tokens, elapsed_ms).
        """
        # Ensure we are serving the latest promoted deployment
        self._load_active_models()

        start = time.perf_counter()
        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"]
        prompt_tokens = input_ids.shape[-1]

        curr_ids = input_ids.clone()
        for _ in range(max_new_tokens):
            if len(self.active_models) == 1:
                logits = self.active_models[0](curr_ids).logits[:, -1, :]
            else:
                # Aggregate logits across SISA shard ensemble
                logits_list = [m(curr_ids).logits[:, -1, :] for m in self.active_models]
                logits = torch.mean(torch.stack(logits_list, dim=0), dim=0)

            next_token_logits = logits / max(1e-5, temperature)

            if top_k > 0:
                indices_to_remove = next_token_logits < torch.topk(next_token_logits, top_k)[0][..., -1, None]
                next_token_logits[indices_to_remove] = -float("Inf")

            probs = F.softmax(next_token_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            curr_ids = torch.cat([curr_ids, next_token], dim=-1)

            if next_token.item() == self.tokenizer.eos_token_id:
                break

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        generated_tokens = curr_ids.shape[-1] - prompt_tokens
        text = self.tokenizer.decode(curr_ids[0][prompt_tokens:], skip_special_tokens=True).strip()

        return text, self.active_version or "distilgpt2-82M", prompt_tokens, generated_tokens, round(elapsed_ms, 2)


# Global singleton
inference_engine = InferenceEngine()
