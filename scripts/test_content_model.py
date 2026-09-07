import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.data.loader import load_mind
from src.models.content_representation import NewsContentModel


DATA_DIR = "data/raw/MINDsmall_train"


news, behaviors = load_mind(DATA_DIR)


print("Loading news content model...")

model = NewsContentModel(
    max_features=20000,
    min_df=2,
    max_df=0.95,
)


model.fit(news)


print("\n========== CONTENT MODEL ==========")

print("News articles:", len(news))
print("TF-IDF dimensions:", model.get_dimension())


print("\n========== SAMPLE NEWS ==========")

sample_news_id = news.iloc[0]["news_id"]

print("News ID:", sample_news_id)
print("Title:", news.iloc[0]["title"])

vector = model.get_vector(sample_news_id)

print("Vector shape:", vector.shape)
print("Non-zero values:", vector.nnz)