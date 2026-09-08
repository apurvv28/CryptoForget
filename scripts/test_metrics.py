import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.evaluation.metrics import (
    auc_score,
    mrr_score,
    ndcg_score,
    recall_score,
)


ranked_news = [
    ("N1", 0.95),
    ("N2", 0.80),
    ("N3", 0.70),
    ("N4", 0.50),
    ("N5", 0.20),
]

labels = {
    "N1": 0,
    "N2": 1,
    "N3": 0,
    "N4": 1,
    "N5": 0,
}


print("========== METRICS TEST ==========")

print("AUC:", auc_score(ranked_news, labels))
print("MRR:", mrr_score(ranked_news, labels))
print("NDCG@3:", ndcg_score(ranked_news, labels, k=3))
print("NDCG@5:", ndcg_score(ranked_news, labels, k=5))
print("Recall@3:", recall_score(ranked_news, labels, k=3))
print("Recall@5:", recall_score(ranked_news, labels, k=5))