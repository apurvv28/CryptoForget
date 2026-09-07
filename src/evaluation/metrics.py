import numpy as np
from sklearn.metrics import roc_auc_score


def auc_score(ranked_news, labels):
    """
    Calculate AUC for one recommendation event.

    ranked_news:
        List of (news_id, score), sorted by recommendation score.

    labels:
        Dictionary mapping news_id -> 0/1 click label.
    """

    y_true = []
    y_scores = []

    for news_id, score in ranked_news:
        y_true.append(labels[news_id])
        y_scores.append(score)

    # AUC is undefined if all candidates have the same label.
    if len(set(y_true)) < 2:
        return None

    return roc_auc_score(y_true, y_scores)


def mrr_score(ranked_news, labels):
    """
    Mean Reciprocal Rank for one event.

    Returns reciprocal rank of the first clicked article.
    Returns 0 if no clicked article exists.
    """

    for rank, (news_id, _) in enumerate(ranked_news, start=1):
        if labels[news_id] == 1:
            return 1.0 / rank

    return 0.0


def ndcg_score(ranked_news, labels, k=10):
    """
    NDCG@K for one recommendation event.
    """

    top_k = ranked_news[:k]

    dcg = 0.0

    for rank, (news_id, _) in enumerate(top_k, start=1):
        relevance = labels[news_id]

        if relevance == 1:
            dcg += relevance / np.log2(rank + 1)

    ideal_labels = sorted(
        labels.values(),
        reverse=True
    )[:k]

    idcg = 0.0

    for rank, relevance in enumerate(ideal_labels, start=1):
        if relevance == 1:
            idcg += relevance / np.log2(rank + 1)

    if idcg == 0:
        return 0.0

    return dcg / idcg


def recall_score(ranked_news, labels, k=10):
    """
    Recall@K for one recommendation event.

    Measures how many of the clicked articles
    appeared in the top K recommendations.
    """

    clicked_news = {
        news_id
        for news_id, label in labels.items()
        if label == 1
    }

    if not clicked_news:
        return 0.0

    recommended_news = {
        news_id
        for news_id, _ in ranked_news[:k]
    }

    hits = len(clicked_news & recommended_news)

    return hits / len(clicked_news)