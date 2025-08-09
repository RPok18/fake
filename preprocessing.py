import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sentence_transformers import SentenceTransformer
import joblib
import re
import string
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import os

# Improved text cleaning function
def clean_text(text):
    """Clean and preprocess text data"""
    text = str(text).lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\d+', '', text)
    text = ' '.join(text.split())
    text = ' '.join([word for word in text.split() if word not in ENGLISH_STOP_WORDS])
    return text

def main():
    """Main preprocessing and training function"""
    try:
        # Check if required files exist
        if not os.path.exists('True.csv'):
            raise FileNotFoundError("True.csv not found in current directory")
        if not os.path.exists('Fake.csv'):
            raise FileNotFoundError("Fake.csv not found in current directory")
        
        print("📁 Loading datasets...")
        # Load datasets with correct filenames
        df_real = pd.read_csv('True.csv')
        df_fake = pd.read_csv('Fake.csv')  # Fixed: was 'fake.csv'
        
        print(f"✅ Loaded {len(df_real)} real news articles")
        print(f"✅ Loaded {len(df_fake)} fake news articles")
        
        # Check if 'text' column exists, if not try 'title' or first column
        text_column = None
        for col in ['text', 'title', 'headline']:
            if col in df_real.columns:
                text_column = col
                break
        
        if text_column is None:
            # Use the first column that contains text data
            for col in df_real.columns:
                if df_real[col].dtype == 'object':
                    text_column = col
                    break
        
        if text_column is None:
            raise ValueError("No suitable text column found in the dataset")
        
        print(f"📝 Using column '{text_column}' for text processing")
        
        # Add labels
        df_real['label'] = 'real'
        df_fake['label'] = 'fake'
        
        # Combine datasets
        df = pd.concat([df_real, df_fake], ignore_index=True)
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        print(f"🔄 Combined dataset: {len(df)} total articles")
        print(f"📊 Label distribution: {df['label'].value_counts().to_dict()}")
        
        # Clean text data
        print("🧹 Cleaning text data...")
        X = df[text_column].astype(str).apply(clean_text)
        y = df['label']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📚 Training set: {len(X_train)} articles")
        print(f"🧪 Test set: {len(X_test)} articles")
        
        # Initialize and train SentenceTransformer embedder
        print("🔤 Initializing SentenceTransformer...")
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        print("📊 Encoding training data...")
        X_train_emb = embedder.encode(X_train.tolist(), show_progress_bar=True)
        
        print("📊 Encoding test data...")
        X_test_emb = embedder.encode(X_test.tolist(), show_progress_bar=True)
        
        print(f"🎯 Training data shape: {X_train_emb.shape}")
        print(f"🎯 Test data shape: {X_test_emb.shape}")
        
        # Train Logistic Regression model
        print("🤖 Training Logistic Regression model...")
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train_emb, y_train)
        
        # Evaluate model
        print("📈 Evaluating model performance...")
        y_pred = model.predict(X_test_emb)
        print("\n" + "="*50)
        print("📊 CLASSIFICATION REPORT")
        print("="*50)
        print(classification_report(y_test, y_pred))
        print("="*50)
        
        # Save model and embedder
        print("💾 Saving model and embedder...")
        joblib.dump(model, 'fake_news_model.pkl')
        embedder.save('sentence_embedder')
        
        print("✅ Preprocessing and training completed successfully!")
        print("📁 Saved files:")
        print("   - fake_news_model.pkl (trained model)")
        print("   - sentence_embedder/ (sentence transformer)")
        
        # Print model info
        print(f"\n🎯 Model Summary:")
        print(f"   - Algorithm: Logistic Regression")
        print(f"   - Training samples: {len(X_train)}")
        print(f"   - Test samples: {len(X_test)}")
        print(f"   - Feature dimensions: {X_train_emb.shape[1]}")
        print(f"   - Random state: 42")
        
    except FileNotFoundError as e:
        print(f"❌ File Error: {e}")
        print("💡 Make sure True.csv and Fake.csv are in the current directory")
    except Exception as e:
        print(f"❌ Error during preprocessing: {e}")
        print("💡 Check your data format and try again")

if __name__ == "__main__":
    main()
