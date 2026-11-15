"""
Model Forgetting Metrics — Target Memorization and Clean-Retrain Divergence.

Per Doc 08 (§7): Evaluates unlearning effectiveness via:
1. Target record loss / memorization shift before vs after unlearning.
2. Clean-Retrain KL divergence: MeanKL = mean_x KL(P_full(x) || P_sisa(x)).
"""

import math
from typing import Any
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer

from ml.evaluation.utility_metrics import evaluate_model_loss_and_ppl


def compute_kl_divergence_to_clean_reference(
    clean_model: Any,
    eval_model: Any,
    prompts: list[str],
    tokenizer: AutoTokenizer,
    max_length: int = 64,
) -> float:
    """
    Computes mean token-level KL divergence between the clean full-retrain reference
    and the evaluated model: KL(P_clean || P_eval).
    """
    if not prompts:
        return 0.0

    total_kl = 0.0
    total_tokens = 0

    for prompt in prompts:
        inputs = tokenizer(prompt, truncation=True, max_length=max_length, return_tensors="pt")
        input_ids = inputs["input_ids"]

        with torch.no_grad():
            if hasattr(clean_model, "get_aggregated_logits"):
                logits_clean = clean_model.get_aggregated_logits(input_ids)
            else:
                logits_clean = clean_model(input_ids=input_ids).logits

            if hasattr(eval_model, "get_aggregated_logits"):
                logits_eval = eval_model.get_aggregated_logits(input_ids)
            else:
                logits_eval = eval_model(input_ids=input_ids).logits

            # Softmax distributions over vocabulary
            p_clean = F.softmax(logits_clean, dim=-1)
            log_p_eval = F.log_softmax(logits_eval, dim=-1)

            # KL(P || Q) = sum P * (log P - log Q)
            kl = F.kl_div(log_p_eval, p_clean, reduction="batchmean")
            total_kl += kl.item()
            total_tokens += 1

    return round(total_kl / max(1, total_tokens), 4)


def evaluate_unlearning_effectiveness(
    original_model: Any,
    unlearned_model: Any,
    clean_retrain_model: Any,
    deleted_texts: list[str],
    retained_texts: list[str],
    tokenizer: AutoTokenizer,
) -> dict[str, Any]:
    """
    Compares the original, unlearned, and clean retrained models across
    retained utility and deleted target loss.
    """
    # 1. Evaluate deleted records
    del_orig = evaluate_model_loss_and_ppl(original_model, deleted_texts, tokenizer)
    del_unlearned = evaluate_model_loss_and_ppl(unlearned_model, deleted_texts, tokenizer)
    del_clean = evaluate_model_loss_and_ppl(clean_retrain_model, deleted_texts, tokenizer)

    # 2. Evaluate retained test records
    ret_orig = evaluate_model_loss_and_ppl(original_model, retained_texts, tokenizer)
    ret_unlearned = evaluate_model_loss_and_ppl(unlearned_model, retained_texts, tokenizer)
    ret_clean = evaluate_model_loss_and_ppl(clean_retrain_model, retained_texts, tokenizer)

    # 3. KL divergence to clean reference on retained texts
    kl_div = compute_kl_divergence_to_clean_reference(
        clean_model=clean_retrain_model,
        eval_model=unlearned_model,
        prompts=retained_texts,
        tokenizer=tokenizer,
    )

    return {
        "deleted_targets": {
            "original_loss": del_orig["loss"],
            "original_ppl": del_orig["perplexity"],
            "unlearned_loss": del_unlearned["loss"],
            "unlearned_ppl": del_unlearned["perplexity"],
            "clean_reference_loss": del_clean["loss"],
            "clean_reference_ppl": del_clean["perplexity"],
        },
        "retained_utility": {
            "original_loss": ret_orig["loss"],
            "original_ppl": ret_orig["perplexity"],
            "unlearned_loss": ret_unlearned["loss"],
            "unlearned_ppl": ret_unlearned["perplexity"],
            "clean_reference_loss": ret_clean["loss"],
            "clean_reference_ppl": ret_clean["perplexity"],
        },
        "kl_to_clean_reference": kl_div,
    }


def compute_mia_metrics(
    model: Any,
    member_texts: list[str],
    non_member_texts: list[str],
    tokenizer: AutoTokenizer,
) -> dict[str, float]:
    """
    Computes Membership Inference Attack (MIA) ROC-AUC and Membership Advantage
    using loss thresholding per Doc 08 §7:
        MembershipAdvantage = TPR - FPR (at FPR ~ 0.10)
    """
    if not member_texts or not non_member_texts:
        return {"mia_auc": 0.5, "mia_advantage": 0.0}

    # Collect token loss for member and non-member samples
    def get_losses(texts: list[str]) -> list[float]:
        losses = []
        for text in texts:
            inputs = tokenizer(text, truncation=True, padding="max_length", max_length=128, return_tensors="pt")
            input_ids = inputs["input_ids"]
            attention_mask = inputs["attention_mask"]
            if hasattr(model, "compute_loss"):
                l = model.compute_loss(input_ids, attention_mask)
            else:
                with torch.no_grad():
                    out = model(input_ids=input_ids, attention_mask=attention_mask, labels=input_ids)
                    l = out.loss.item()
            losses.append(l)
        return losses

    mem_losses = get_losses(member_texts)
    non_mem_losses = get_losses(non_member_texts)

    # In loss thresholding, lower loss indicates membership.
    # Scores = -loss
    scores = [-l for l in mem_losses] + [-l for l in non_mem_losses]
    labels = [1] * len(mem_losses) + [0] * len(non_mem_losses)

    # Compute ROC-AUC via rank-sum (Wilcoxon-Mann-Whitney)
    n_pos = len(mem_losses)
    n_neg = len(non_mem_losses)

    pairs_correct = 0.0
    for sm in mem_losses:
        for snm in non_mem_losses:
            # member loss < non-member loss means score_m > score_nm
            if sm < snm:
                pairs_correct += 1.0
            elif sm == snm:
                pairs_correct += 0.5

    auc = round(pairs_correct / max(1.0, n_pos * n_neg), 3)

    # Membership advantage: select threshold at ~10% FPR
    sorted_non_mem = sorted(non_mem_losses)
    idx_10 = max(0, int(len(sorted_non_mem) * 0.10))
    threshold = sorted_non_mem[idx_10]  # lowest 10% non-members are false positives

    tpr = sum(1 for l in mem_losses if l <= threshold) / max(1, n_pos)
    fpr = sum(1 for l in non_mem_losses if l <= threshold) / max(1, n_neg)
    advantage = round(max(0.0, tpr - fpr), 3)

    return {
        "mia_auc": auc,
        "mia_advantage": advantage,
    }

