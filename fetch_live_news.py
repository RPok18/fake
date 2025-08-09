import feedparser
import joblib
import os

BASE_DIR = r"E:\fake"
model_path = os.path.join(BASE_DIR, 'fake_news_model.pkl')
vectorizer_path = os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl')

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

feed = feedparser.parse('https://news.google.com/rss')

print("Latest 10 news with fake news predictions:\n")

for entry in feed.entries[:10]:
    text = (entry.title + " " + entry.get('summary', '')).lower()
    vect = vectorizer.transform([text])
    pred = model.predict(vect)[0]
    print(f"{pred.upper()}: {entry.title}")
