import os
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


import sys
# Ensure config can be imported from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import ROOT_DIR

FAKE_CSV = os.path.join(ROOT_DIR, 'data', 'Fake.csv')
TRUE_CSV = os.path.join(ROOT_DIR, 'data', 'True.csv')
MODEL_PATH = os.path.join(ROOT_DIR, 'data', 'fake_news_model.pkl')
EMBEDDER_PATH = os.path.join(ROOT_DIR, 'data', 'sentence_embedder')


def load_data(sample_size=None):
    """Load and Combine True and Fake datasets."""
    if not os.path.exists(FAKE_CSV) or not os.path.exists(TRUE_CSV):
        logger.error("❌ Dataset files not found! Please ensure Fake.csv and True.csv are in the current directory.")
        return None

    logger.info("⏳ Loading datasets...")
    df_fake = pd.read_csv(FAKE_CSV)
    df_true = pd.read_csv(TRUE_CSV)

    # Add labels: 0 for Fake, 1 for Real (mapped effectively to class names later)
    # Using string labels directly for clarity in model.classes_
    df_fake['label'] = 'fake'
    df_true['label'] = 'real'

    # Combine
    df = pd.concat([df_fake, df_true], ignore_index=True)
    
    # Simple cleaning
    df['text'] = df['title'] + " " + df['text']  # Combine title and text for better context
    df['text'] = df['text'].astype(str).str.lower().str.strip()
    
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    if sample_size:
        logger.info(f"ℹ️  Using a sample of {sample_size} rows for quick training.")
        df = df.head(sample_size)
    
    logger.info(f"✅ Data loaded. Shape: {df.shape}")
    return df

def train_model(sample_size=None, save_embedder=True):
    """Train and save the model."""
    df = load_data(sample_size)
    if df is None:
        return

    # Load or download embedder
    logger.info("⏳ Loading SentenceTransformer...")
    # Use valid model name
    model_name = 'all-MiniLM-L6-v2' 
    if os.path.exists(EMBEDDER_PATH):
        logger.info(f"   Loading from local path: {EMBEDDER_PATH}")
        embedder = SentenceTransformer(EMBEDDER_PATH)
    else:
        logger.info(f"   Downloading {model_name}...")
        embedder = SentenceTransformer(model_name)
        if save_embedder:
            logger.info(f"   Saving embedder to {EMBEDDER_PATH}...")
            embedder.save(EMBEDDER_PATH)

    # Generate Embeddings
    logger.info("⏳ Generating embeddings (this may take a while)...")
    # Batch encoding is handled by SentenceTransformer, but for large datasets it can be slow
    X = embedder.encode(df['text'].tolist(), show_progress_bar=True)
    y = df['label']

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train Classifier
    logger.info("⏳ Training Classifier (Logistic Regression)...")
    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    logger.info("✅ Training Complete.")
    logger.info(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    logger.info("\n" + classification_report(y_test, y_pred))

    # Save Model
    joblib.dump(clf, MODEL_PATH)
    logger.info(f"💾 Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train Fake News Detection Model")
    parser.add_argument("--full", action="store_true", help="Train on full dataset (slow!)")
    parser.add_argument("--sample", type=int, default=2000, help="Number of samples to use (default: 2000)")
    args = parser.parse_args()

    # Determine sample size
    size = None if args.full else args.sample
    train_model(sample_size=size)
