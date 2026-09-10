# Serving layer — Recommendation model API

Wraps Vedant's dynamic (long-term + short-term) content-based recommender
(`src/models`, `src/personalization`) in a FastAPI service and a Docker image,
ready to hand off to Anushka's MLOps/retraining pipeline.

## What's actually being "served"

There's no single trained weights file (`.pkl` classifier). The model is:

1. **`NewsContentModel`** — a TF-IDF vectorizer fit once on `news.tsv`
   (title + abstract). This is the only piece that needs "training".
2. **User profile = long-term (historical clicks) + short-term (recent
   clicks, exponentially decayed) fused with `alpha`** — built on the fly,
   per request, from whatever click history is available for that user.
3. **`DynamicRecommender`** — ranks candidate news IDs by cosine similarity
   between the user profile and each candidate's TF-IDF vector.

So "training" = re-fitting the TF-IDF model on the news corpus (step 1
below). "Inference" = building a profile + ranking, which happens live in
the API on every `/recommend` call.

## 1. Build the model artifacts (do this before building the image)

```bash
# from the repo root
pip install -r serving/requirements.txt
python serving/scripts/build_content_model.py \
    --data-dir data/raw/MINDsmall_train \
    --output-dir serving/models
```

This writes `serving/models/content_model.joblib` (fitted TF-IDF model) and
`serving/models/user_histories.joblib` (long-term history lookup for the
~49k users already present in `behaviors.tsv`). Re-run this any time the
news catalog / interaction data changes — this is the step Anushka's
scheduled retraining job (Airflow/Jenkins/GitHub Actions) should trigger.

## 2. Run locally (no Docker)

```bash
cd serving
MODELS_DIR=./models uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/docs

## 3. Build & run the Docker image

Build context must be the **repo root** (Dockerfile copies `src/` from
there):

```bash
docker build -f serving/Dockerfile -t recommendation-service:latest .
docker run -p 8000:8000 recommendation-service:latest
```

## 4. API contract (what Anushka/Nisha plug into)

| Method | Path         | Purpose                                                    |
| ------ | ------------ | ----------------------------------------------------------- |
| GET    | `/health`    | Liveness/readiness probe — model loaded, vector dim, user count |
| POST   | `/clicks`    | Ingest one observed click (feed this from the Kafka/Redis/Kinesis stream simulation) |
| POST   | `/recommend` | Rank a candidate pool of news IDs for a user               |

`POST /recommend` body:
```json
{
  "user_id": "U1000",
  "candidate_news_ids": ["N1", "N2", "N3"],
  "top_k": 10,
  "history": null
}
```
`history` is optional — omit it to use the user's known long-term MIND
history (if any) plus whatever has been POSTed to `/clicks` for them so
far. Pass an explicit list to override it (useful for brand-new simulated
users who aren't in the original dataset).

## 5. Config (env vars)

| Var                       | Default        | Meaning                          |
| -------------------------- | -------------- | --------------------------------- |
| `MODELS_DIR`               | `/app/models`  | Where to load the `.joblib` artifacts from |
| `MODEL_VERSION`             | `dev`          | Reported in `/health` and every response |
| `ALPHA`                     | `0.5`          | Long-term vs short-term fusion weight |
| `SHORT_TERM_WINDOW_HOURS`   | `24`           | Recency window for short-term profile |
| `DECAY_RATE`                | `0.05`         | Exponential decay rate for recency weighting |

## 6. Handoff to Anushka

- The Docker image is stateless w.r.t. training — it only needs
  `serving/models/*.joblib` mounted or baked in.
- `/health` is the probe her orchestrator (Airflow/Kubeflow/Jenkins) should
  poll after a redeploy.
- Her retraining job = re-run `build_content_model.py` on fresh data →
  produce new `.joblib` artifacts → rebuild/redeploy this image (or mount
  the new artifacts and restart the container — no code change needed).
- Note (from the README's own findings section): the static content-based
  model outperformed this dynamic long+short-term model in offline
  evaluation. The serving code still implements the dynamic model since
  that's the project's core contribution, but swapping to
  `ContentRecommender` (static) is a one-line change in `model_state.py`
  if the team decides to serve that instead.
