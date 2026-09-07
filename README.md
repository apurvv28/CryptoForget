# Adaptive Personalized Content Recommendation Using Dynamic User Preference Modeling

A research-oriented personalized content recommendation system that investigates whether dynamically updating a user's preference representation using **long-term historical behavior** and **short-term recent interactions** can improve recommendation quality, particularly when user interests change over time.

---

## 1. Research Question

> **Does dynamically updating a user's preference representation using both long-term historical behavior and recent interactions improve personalized content recommendation compared with static or non-personalized approaches, particularly when the user's interests change over time?**

The project investigates this question using the **Microsoft News Dataset (MIND-small)** and compares multiple recommendation approaches under offline evaluation.

---

## 2. Project Overview

Traditional recommendation systems often represent a user's interests using their historical behavior. However, user interests can change over time.

For example:

```text
Long-term history:
AI → Machine Learning → Programming → Data Science

Recent behavior:
Football → Premier League → Sports
```

A static profile may continue recommending technology-related content even when the user's recent behavior indicates an interest in sports.

This project investigates a dynamic user representation that combines:

* **Long-term preference** — accumulated historical interests
* **Short-term preference** — recent interactions
* **Recency weighting** — recent interactions receive greater importance
* **Dynamic profile fusion** — long-term and short-term representations are combined
* **Chronological updates** — the user profile changes as new interactions become available

The resulting user representation is used to rank candidate news articles.

---

## 3. Recommendation Pipeline

```text
                     MIND-small Dataset
                              │
                              ▼
                     Data Preprocessing
                              │
                              ▼
                    Recommendation Events
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
         Popularity       Collaborative    Content-Based
                           Filtering
              │               │                │
              └───────────────┼────────────────┘
                              │
                              ▼
                    Embedding-Based Model
                              │
                              ▼
                 Dynamic Preference Modeling
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
          Long-Term Profile          Short-Term Profile
                │                           │
                │                    Recency Weighted
                │                           │
                └─────────────┬─────────────┘
                              ▼
                     Dynamic User Profile
                              │
                              ▼
                    Candidate News Ranking
                              │
                              ▼
                         Evaluation
```

---

## 4. Dataset

This project uses the **Microsoft News Dataset (MIND-small)**.

Official dataset website:

https://msnews.github.io/

The local dataset is expected at:

```text
data/raw/MINDsmall_train/
```

### Dataset files

```text
MINDsmall_train/
├── behaviors.tsv
├── news.tsv
├── entity_embedding.vec
└── relation_embedding.vec
```

### News schema

```text
news_id
category
subcategory
title
abstract
url
title_entities
abstract_entities
```

### Behavior schema

```text
impression_id
user_id
time
history
impressions
```

The project uses the available interaction signals from MIND, primarily:

* user ID
* news ID
* timestamp
* historical clicked news
* clicked/non-clicked impressions

The project does **not** assume unavailable interaction signals such as likes, saves, shares, dwell time, or reading duration.

---

## 5. Dataset Statistics

The local MIND-small data used in the experiments contains approximately:

| Property                       |     Value |
| ------------------------------ | --------: |
| Users                          |    50,000 |
| News articles                  |    51,282 |
| Expanded impressions           | 5,843,444 |
| Clicked interactions           |   236,344 |
| Non-clicked interactions       | 5,607,100 |
| Evaluation events              |   156,965 |
| News appearing in interactions |    20,288 |

The interaction timestamps cover:

```text
2019-11-09 00:00:19
        to
2019-11-14 23:59:13
```

---

# 6. Temporal Evaluation

A major requirement of this project is preventing future interactions from influencing earlier recommendations.

The interaction data is therefore processed chronologically.

The overall interaction data was divided temporally into:

```text
70% → Training period
15% → Validation period
15% → Test period
```

Approximate periods:

| Split      | Time range      | Interactions |
| ---------- | --------------- | -----------: |
| Train      | Nov 9 → Nov 13  |    3,475,543 |
| Validation | Nov 13 → Nov 14 |    1,164,956 |
| Test       | Nov 14          |    1,202,945 |

For the dynamic evaluation, recommendation events are processed sequentially.

At time `t`, only information available before `t` is allowed to influence the user's profile.

---

# 7. Dynamic User Preference Modeling

The central component of the project is the dynamic user preference representation.

## Long-Term Preference

The long-term profile represents the user's accumulated interests.

For a set of previously clicked articles:

```text
Long-Term Profile
=
Mean representation of historical clicked articles
```

The article representations are generated using TF-IDF.

---

## Short-Term Preference

The short-term profile represents recent user behavior.

Only interactions within a defined recent time window are considered.

The current configuration uses:

```text
Short-term window = 24 hours
Decay rate = 0.05
```

Recent interactions receive larger weights using exponential decay:

```text
w = exp(-λ × Δt)
```

where:

* `w` = recency weight
* `λ` = decay rate
* `Δt` = time since the interaction

Therefore:

```text
Recent interaction
        ↓
Higher weight

Older interaction
        ↓
Lower weight
```

---

## Dynamic Fusion

The long-term and short-term profiles are combined using:

```text
Dynamic Profile
=
α × Long-Term Profile
+
(1 − α) × Short-Term Profile
```

The primary dynamic configuration uses:

```text
α = 0.5
```

This gives equal weight to the long-term and short-term components.

---

# 8. Recommendation Models

The project evaluates the following approaches.

### 1. Popularity

Ranks content based on overall popularity.

This serves as a non-personalized baseline.

---

### 2. Collaborative Filtering

Uses user-item interaction behavior to generate personalized recommendations.

---

### 3. Static Content-Based Recommendation

Represents news articles using TF-IDF features derived from their textual content.

A user's profile is constructed from their historical clicked articles.

Candidate articles are ranked using cosine similarity between:

```text
User Profile
       ↕
News Representation
```

---

### 4. Embedding-Based Recommendation

Uses the embedding information provided with the MIND dataset.

---

### 5. Dynamic Long-Term + Short-Term Recommendation

The proposed approach combines:

```text
Historical Preference
        +
Recent Preference
        +
Recency Weighting
        ↓
Dynamic User Profile
        ↓
Candidate Ranking
```

The dynamic profile is reconstructed chronologically as new interactions become available.

---

# 9. Interest-Shift Detection

The project also evaluates recommendation performance during detected changes in user interests.

Interest shifts are identified by comparing:

```text
Older user interests
        VS
Recent user interests
```

The current detection configuration uses:

```text
Recent window:       24 hours
Minimum history:     3 interactions
Minimum recent:      2 interactions
Shift threshold:     0.5
```

The shift score is based on category overlap using Jaccard similarity:

```text
Shift Score
=
1 − Jaccard Overlap
```

Higher values indicate greater difference between older and recent category interests.

### Detected shifts

```text
Interest-shift events: 40,252
Unique users:          7,763
Mean shift score:      0.7107
Median shift score:    0.7143
```

A leakage-controlled evaluation was performed on a fixed sample of:

```text
2,000 detected interest-shift events
```

---

# 10. Evaluation Metrics

The recommendation systems are evaluated using:

### AUC

Measures the ability of the model to distinguish clicked from non-clicked candidate articles.

Higher is better.

### MRR

Measures how highly the first relevant article appears in the ranking.

Higher is better.

### NDCG@K

Measures ranking quality while giving greater importance to relevant articles appearing near the top.

Higher is better.

### Recall@K

Measures how many clicked articles are successfully included within the top-K recommendations.

Higher is better.

The project reports:

```text
AUC
MRR
NDCG@5
NDCG@10
Recall@5
Recall@10
```

---

# 11. Overall Benchmark Results

The overall benchmark produced the following results:

| Model                   |        AUC |        MRR |     NDCG@5 |    NDCG@10 |   Recall@5 |  Recall@10 |
| ----------------------- | ---------: | ---------: | ---------: | ---------: | ---------: | ---------: |
| Popularity              |     0.6033 |     0.3448 |     0.3218 |     0.3725 |     0.4383 |     0.5842 |
| Collaborative Filtering |     0.9303 |     0.7950 |     0.7735 |     0.7975 |     0.8407 |     0.9077 |
| Static Content-Based    | **0.9913** | **0.9335** | **0.9447** | **0.9491** | **0.9859** | **0.9983** |
| Embedding-Based         |     0.5000 |     0.2545 |     0.2359 |     0.2926 |     0.3531 |     0.5181 |
| Dynamic Long+Short      |     0.5847 |     0.3226 |     0.3046 |     0.3613 |     0.4317 |     0.5949 |

### Important evaluation note

The overall baseline results above were generated using the available interaction data before evaluation. Therefore, they should **not be interpreted as a completely leakage-controlled comparison against the chronological dynamic model**.

The interest-shift experiment provides the more appropriate comparison for studying the temporal adaptation hypothesis.

---

# 12. Leakage-Controlled Interest-Shift Results

At detected interest-shift events:

| Model                |        AUC |        MRR |     NDCG@5 |    NDCG@10 |   Recall@5 |  Recall@10 |
| -------------------- | ---------: | ---------: | ---------: | ---------: | ---------: | ---------: |
| Static Content-Based | **0.6055** | **0.3581** | **0.2549** | **0.3165** | **0.3096** | **0.4753** |
| Dynamic Long+Short   |     0.5902 |     0.3002 |     0.2178 |     0.2784 |     0.2820 |     0.4379 |

The static model outperformed the current dynamic configuration on all evaluated metrics.

This result does **not** support the hypothesis that adding the short-term recency-weighted component improves recommendation performance under the current experimental setup.

---

# 13. Alpha Sensitivity Analysis

The contribution of the long-term component was investigated by varying `α`.

```text
α = 0.00
α = 0.25
α = 0.50
α = 0.75
α = 1.00
```

Results:

|    α |        AUC |        MRR |     NDCG@5 |    NDCG@10 |   Recall@5 |  Recall@10 |
| ---: | ---------: | ---------: | ---------: | ---------: | ---------: | ---------: |
| 0.00 |     0.5397 |     0.2739 |     0.1919 |     0.2461 |     0.2481 |     0.3920 |
| 0.25 |     0.5794 |     0.2864 |     0.2032 |     0.2652 |     0.2624 |     0.4239 |
| 0.50 |     0.5902 |     0.3002 |     0.2178 |     0.2784 |     0.2820 |     0.4379 |
| 0.75 |     0.6013 |     0.3185 |     0.2337 |     0.2934 |     0.2974 |     0.4529 |
| 1.00 | **0.6056** | **0.3569** | **0.2542** | **0.3159** | **0.3093** | **0.4751** |

All evaluated metrics increased as the long-term weight increased.

The best result was obtained at:

```text
α = 1.0
```

which corresponds to using only the long-term representation.

The alpha experiment is treated as a **sensitivity/ablation analysis**. The primary dynamic configuration remains `α = 0.5`.

---

# 14. Project Structure

```text
Forget/
│
├── README.md
├── requirements.txt
│
├── configs/
│
├── data/
│   ├── raw/
│   │   └── MINDsmall_train/
│   │       ├── behaviors.tsv
│   │       ├── news.tsv
│   │       ├── entity_embedding.vec
│   │       └── relation_embedding.vec
│   │
│   └── processed/
│       └── interest_shift_events.csv
│
├── src/
│   │
│   ├── data/
│   │   ├── loader.py
│   │   ├── preprocessing.py
│   │   ├── temporal_split.py
│   │   ├── user_history.py
│   │   └── evaluation_events.py
│   │
│   ├── models/
│   │   ├── content_representation.py
│   │   ├── content_recommender.py
│   │   └── dynamic_recommender.py
│   │
│   ├── personalization/
│   │   ├── long_term.py
│   │   ├── short_term.py
│   │   ├── recency.py
│   │   ├── fusion.py
│   │   ├── dynamic_profile.py
│   │   ├── temporal_profile.py
│   │   ├── history_profile.py
│   │   └── user_click_store.py
│   │
│   └── evaluation/
│       ├── chronological.py
│       ├── metrics.py
│       └── interest_shift.py
│
├── scripts/
│   ├── evaluate_dynamic.py
│   ├── detect_interest_shifts.py
│   ├── evaluate_interest_shift.py
│   ├── evaluate_alpha.py
│   └── generate_results.py
│
├── models/
│
├── notebooks/
│
└── results/
    ├── model_comparison.csv
    ├── interest_shift_results.csv
    ├── interest_shift_summary.csv
    ├── alpha_sensitivity_results.csv
    ├── alpha_summary.csv
    │
    └── figures/
        ├── overall_auc.png
        ├── overall_mrr.png
        ├── overall_ndcg_5.png
        ├── overall_ndcg_10.png
        ├── overall_recall_5.png
        ├── overall_recall_10.png
        ├── interest_shift_auc.png
        ├── interest_shift_mrr.png
        ├── interest_shift_ndcg_5.png
        ├── interest_shift_ndcg_10.png
        ├── interest_shift_recall_5.png
        ├── interest_shift_recall_10.png
        ├── alpha_auc.png
        ├── alpha_mrr.png
        ├── alpha_ndcg5.png
        ├── alpha_ndcg10.png
        ├── alpha_recall5.png
        └── alpha_recall10.png
```

---

# 15. Installation

Clone or open the project:

```bash
cd Forget
```

Create a virtual environment:

### Windows

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

# 16. Dataset Setup

Download **MIND-small** from the official Microsoft News Dataset website:

https://msnews.github.io/

Place the extracted files inside:

```text
data/raw/MINDsmall_train/
```

The directory should contain:

```text
behaviors.tsv
news.tsv
entity_embedding.vec
relation_embedding.vec
```

---

# 17. Running the Experiments

## Dynamic Recommendation Evaluation

```powershell
python .\scripts\evaluate_dynamic.py
```

---

## Interest-Shift Detection

```powershell
python .\scripts\detect_interest_shifts.py
```

This produces:

```text
data/processed/interest_shift_events.csv
```

---

## Interest-Shift Evaluation

```powershell
python .\scripts\evaluate_interest_shift.py
```

This produces:

```text
results/interest_shift_results.csv
```

---

## Alpha Sensitivity Analysis

```powershell
python .\scripts\evaluate_alpha.py
```

This produces:

```text
results/alpha_sensitivity_results.csv
```

---

## Generate Final Tables and Figures

```powershell
python .\scripts\generate_results.py
```

Generated outputs are stored in:

```text
results/
```

and:

```text
results/figures/
```

---

# 18. Reproducibility

The project uses a fixed experimental configuration for the primary dynamic model:

```text
Dataset:              MIND-small
TF-IDF dimensions:    20,000
Short-term window:    24 hours
Decay rate:           0.05
Alpha:                0.5
```

The interest-shift and alpha sensitivity experiments use a fixed sample of:

```text
2,000 events
```

with:

```text
random_state = 42
```

This ensures that the reported experiments can be reproduced under the same environment and dataset.

---

# 19. Cold Start Handling

Users without sufficient historical interaction information cannot immediately receive a meaningful personalized profile.

The system therefore supports a simple fallback concept:

```text
Insufficient history
        ↓
Popularity-based recommendation
        ↓
Sufficient interaction history
        ↓
Personalized recommendation
```

---

# 20. Data Governance

The recommendation system is intended to operate with user consent for using interaction history for personalization.

Conceptually:

```text
User opts in
     ↓
Interaction history may be used
     ↓
Personalized recommendations

User opts out
     ↓
Personalization history excluded
     ↓
Non-personalized fallback
```

---

# 21. Limitations

The current study has several limitations.

### Limited temporal coverage

MIND-small covers a relatively short period of user activity, limiting the ability to study long-term behavioral evolution.

### Offline evaluation

The system is evaluated using historical data rather than a live recommendation environment.

### Click-only feedback

The dataset primarily provides click/non-click interaction information. Richer feedback such as dwell time or explicit ratings is unavailable.

### Cold-start users

Users with little or no interaction history are difficult to personalize effectively.

### Popularity bias

Popular news can naturally receive more interactions, potentially influencing evaluation results.

### Interest-shift detection

The current shift detector is based on changes in clicked news categories and may not perfectly represent a genuine change in user intent.

### Computational limitations

Processing millions of interactions and repeatedly constructing user profiles is computationally expensive.

### No online deployment

The current work is an offline research implementation and does not evaluate real-time production serving.

### Baseline evaluation protocol

The overall benchmark results and the leakage-controlled temporal evaluation should be interpreted separately because the baseline fitting procedures used for the overall benchmark do not provide the same strict chronological constraint as the dynamic evaluation.

---

# 22. Research Findings

The experiments provide several important findings.

### Finding 1 — Personalization is valuable

Both collaborative filtering and content-based personalization substantially outperform the popularity baseline in the overall benchmark.

### Finding 2 — Content representation performs strongly

The static content-based model achieves the strongest overall benchmark performance.

### Finding 3 — Dynamic modeling did not improve the current evaluation

The long-term + short-term dynamic model did not outperform the static content-based model in the leakage-controlled interest-shift experiment.

### Finding 4 — Long-term preference dominates in the current setup

The alpha sensitivity experiment shows consistent improvement as the long-term contribution increases.

### Finding 5 — The short-term component requires further investigation

The results do not provide evidence that the current 24-hour recency-weighted short-term representation improves predictive performance for the evaluated MIND-small events.

These findings should be interpreted as empirical observations from the current dataset and experimental configuration rather than universal conclusions about recommendation systems.

---

# 23. Research Contribution

The project investigates a temporal personalization approach in which a user's representation is not treated as completely static.

The core methodological contribution is the explicit modeling of:

```text
Long-Term Preference
        +
Short-Term Recent Preference
        +
Recency Weighting
        ↓
Dynamic User Representation
```

combined with chronological evaluation to prevent future interactions from influencing earlier recommendations.

An equally important contribution of the study is the empirical analysis showing that the proposed short-term component **does not necessarily improve recommendation quality** under the evaluated conditions.

This negative result provides useful evidence about the limitations of simple recency-based preference adaptation.

---

# 24. Current Status

```text
Dataset preparation                 ✓
Data preprocessing                  ✓
Temporal splitting                  ✓
Popularity baseline                 ✓
Collaborative filtering             ✓
Content-based recommendation        ✓
Embedding-based recommendation     ✓
Long-term preference modeling       ✓
Short-term preference modeling      ✓
Recency weighting                   ✓
Dynamic profile fusion              ✓
Chronological evaluation            ✓
Interest-shift detection            ✓
Interest-shift evaluation           ✓
Alpha sensitivity analysis          ✓
Final results generation            ✓
Research analysis                   → Next
Research paper/report               → Next
```

---

## 25. License and Dataset Attribution

The MIND dataset is provided by Microsoft Research.

Dataset information and access:

https://msnews.github.io/

Please follow the dataset's applicable terms of use and licensing requirements when distributing or publishing work based on the dataset.

---

## 26. Citation

If this project is used in an academic report or research paper, cite the original MIND dataset publication and any additional sources used in the research methodology.

The project itself is a research implementation for studying dynamic personalized content recommendation using temporal user preference modeling.
