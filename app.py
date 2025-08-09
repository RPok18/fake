from flask import Flask, request, jsonify, render_template
import joblib
import os
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import re
from urllib.parse import urlparse
from datetime import datetime

app = Flask(__name__)

# Load the trained model and embedder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    model = joblib.load(os.path.join(BASE_DIR, 'fake_news_model.pkl'))
    embedder = SentenceTransformer(os.path.join(BASE_DIR, 'sentence_embedder'))
    print("✅ Model and embedder loaded successfully")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None
    embedder = None

# News API configuration
try:
    from config_local import NEWS_API_KEY
    print(f"✅ Using NewsAPI key from local config")
except ImportError:
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'your_news_api_key_here')
    if NEWS_API_KEY == 'your_news_api_key_here':
        print("⚠️  No valid NewsAPI key found. Create config_local.py with your API key.")

# Credibility scores for different news sources
CREDIBILITY_SCORES = {
    'reuters.com': 98, 'reuters': 98,
    'ap.org': 97, 'apnews.com': 97, 'associated press': 97,
    'bbc.com': 96, 'bbc.co.uk': 96, 'bbc': 96,
    'npr.org': 95, 'npr': 95,
    'pbs.org': 94, 'pbs': 94,
    'nytimes.com': 88, 'nytimes': 88,
    'washingtonpost.com': 87, 'washington post': 87,
    'wsj.com': 86, 'wall street journal': 86,
    'economist.com': 85, 'economist': 85,
    'time.com': 84, 'time': 84,
    'cnn.com': 83, 'cnn': 83,
    'abcnews.go.com': 82, 'abc news': 82,
    'cbsnews.com': 81, 'cbs news': 81,
    'nbcnews.com': 80, 'nbc news': 80,
    'usatoday.com': 78, 'usa today': 78,
    'foxnews.com': 75, 'fox news': 75,
    'msnbc.com': 74, 'msnbc': 74,
    'huffpost.com': 72, 'huffington post': 72,
    'vox.com': 71, 'vox': 71,
    'theguardian.com': 68, 'guardian': 68,
    'independent.co.uk': 65, 'independent': 65,
    'telegraph.co.uk': 64, 'telegraph': 64,
    'dailymail.co.uk': 62, 'daily mail': 62,
    'forbes.com': 58, 'forbes': 58,
    'businessinsider.com': 55, 'business insider': 55,
    'techcrunch.com': 54, 'techcrunch': 54,
    'buzzfeed.com': 52, 'buzzfeed': 52,
    'default': 50
}

def get_credibility_score(source_name):
    """Get credibility score for a news source"""
    if not source_name:
        return CREDIBILITY_SCORES['default']
    
    source_lower = source_name.lower().strip()
    if source_lower in CREDIBILITY_SCORES:
        return CREDIBILITY_SCORES[source_lower]
    
    for key, score in CREDIBILITY_SCORES.items():
        if key in source_lower or source_lower in key:
            return score
    
    if any(word in source_lower for word in ['news', 'times', 'post', 'journal', 'tribune']):
        return 65
    elif any(word in source_lower for word in ['blog', 'medium', 'substack']):
        return 45
    
    return CREDIBILITY_SCORES['default']

def analyze_content_quality(text):
    """Analyze the quality and characteristics of the news text"""
    analysis = {
        'length': len(text),
        'has_numbers': bool(re.search(r'\d+', text)),
        'has_dates': bool(re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', text.lower())),
        'has_names': bool(re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)),
        'has_quotes': text.count('"') >= 2,
        'has_sources': any(word in text.lower() for word in ['according to', 'said', 'reported', 'announced', 'confirmed']),
        'emotional_language': len(re.findall(r'\b(amazing|incredible|shocking|terrible|wonderful|horrible|fantastic|awful)\b', text.lower())),
        'exaggeration_words': len(re.findall(r'\b(always|never|everyone|nobody|completely|absolutely|totally|entirely)\b', text.lower()))
    }
    
    quality_score = 0
    if analysis['has_numbers']: quality_score += 15
    if analysis['has_dates']: quality_score += 15
    if analysis['has_names']: quality_score += 15
    if analysis['has_quotes']: quality_score += 15
    if analysis['has_sources']: quality_score += 15
    if analysis['emotional_language'] < 3: quality_score += 10
    if analysis['exaggeration_words'] < 2: quality_score += 10
    if analysis['length'] > 50: quality_score += 5
    
    analysis['quality_score'] = min(100, quality_score)
    return analysis

def cross_reference_sources(results):
    """Cross-reference information across multiple sources"""
    if len(results) < 2:
        return {'consistency': 'low', 'score': 30, 'details': 'Only one source found'}
    
    key_phrases = []
    for result in results:
        title = result['title'].lower()
        phrases = re.findall(r'\b[a-z]+(?:\s+[a-z]+)*\b', title)
        key_phrases.extend([p for p in phrases if len(p) > 3])
    
    phrase_counts = {}
    for phrase in key_phrases:
        phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
    
    total_sources = len(results)
    consistent_phrases = sum(1 for count in phrase_counts.values() if count > 1)
    
    if total_sources >= 5 and consistent_phrases >= 3:
        consistency_score = 90
        consistency_level = 'high'
    elif total_sources >= 3 and consistent_phrases >= 2:
        consistency_score = 70
        consistency_level = 'medium'
    else:
        consistency_score = 50
        consistency_level = 'low'
    
    return {
        'consistency': consistency_level,
        'score': consistency_score,
        'details': f'{consistent_phrases} key phrases consistent across {total_sources} sources'
    }

def fact_check_indicators(text, results):
    """Check for common fact-checking indicators"""
    indicators = {
        'verifiable_claims': 0,
        'specific_details': 0,
        'attributable_statements': 0,
        'red_flags': 0
    }
    
    if re.search(r'\b\d+%\b|\b\d+\s+(million|billion|thousand)\b', text):
        indicators['verifiable_claims'] += 1
    
    if re.search(r'\b\d{1,2}:\d{2}\b|\b\d{1,2}:\d{2}\s*(am|pm)\b', text):
        indicators['specific_details'] += 1
    
    if re.search(r'\b(according to|said|reported|announced|confirmed)\b', text):
        indicators['attributable_statements'] += 1
    
    red_flag_patterns = [
        r'\b(conspiracy|cover-up|secret|hidden|suppressed)\b',
        r'\b(100%|guaranteed|definitely|absolutely)\b',
        r'\b(urgent|breaking|exclusive|shocking)\b',
        r'\b(they don\'t want you to know|mainstream media won\'t report)\b'
    ]
    
    for pattern in red_flag_patterns:
        if re.search(pattern, text.lower()):
            indicators['red_flags'] += 1
    
    fact_score = (
        indicators['verifiable_claims'] * 20 +
        indicators['specific_details'] * 20 +
        indicators['attributable_statements'] * 20 -
        indicators['red_flags'] * 15
    )
    
    indicators['fact_score'] = max(0, min(100, fact_score))
    return indicators

def determine_verdict(credibility_score, consistency_score, fact_score, content_quality, source_count):
    """Determine final TRUE/FALSE verdict based on comprehensive analysis"""
    final_score = (
        credibility_score * 0.3 +
        consistency_score * 0.25 +
        fact_score * 0.25 +
        content_quality * 0.15 +
        min(source_count * 5, 25)
    )
    
    if final_score >= 80:
        verdict = "TRUE"
        confidence = "HIGH"
        explanation = "Multiple credible sources confirm this news with consistent information and verifiable details."
    elif final_score >= 60:
        verdict = "LIKELY TRUE"
        confidence = "MEDIUM"
        explanation = "Several sources support this news, but some details may need verification."
    elif final_score >= 40:
        verdict = "UNCERTAIN"
        confidence = "LOW"
        explanation = "Mixed signals - some sources support this, but credibility or consistency is questionable."
    else:
        verdict = "LIKELY FALSE"
        confidence = "MEDIUM"
        explanation = "Multiple red flags suggest this news may be inaccurate or misleading."
    
    return {
        'verdict': verdict,
        'confidence': confidence,
        'final_score': round(final_score, 1),
        'explanation': explanation
    }

def search_newsapi(query):
    """Search using NewsAPI"""
    if NEWS_API_KEY == 'your_news_api_key_here':
        return []
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 10
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for article in data.get('articles', []):
                source_name = article.get('source', {}).get('name', 'Unknown')
                credibility = get_credibility_score(source_name)
                
                results.append({
                    'title': article.get('title', ''),
                    'source': source_name,
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'credibility': credibility,
                    'api_source': 'NewsAPI'
                })
            
            return results
    except Exception as e:
        print(f"NewsAPI error: {e}")
    
    return []

def search_google_news(query):
    """Search using Google News RSS"""
    try:
        rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}"
        response = requests.get(rss_url, timeout=10)
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')[:10]
        
        results = []
        for item in items:
            if item.title and item.title.text:
                source_name = item.source.text if item.source else 'Unknown'
                credibility = get_credibility_score(source_name)
                
                results.append({
                    'title': item.title.text,
                    'source': source_name,
                    'url': item.link.text if item.link else '',
                    'published_at': item.pubDate.text if item.pubDate else '',
                    'credibility': credibility,
                    'api_source': 'Google News'
                })
        
        return results
    except Exception as e:
        print(f"Google News error: {e}")
        return []

def search_reuters(query):
    """Search Reuters website for news"""
    try:
        search_url = f"https://www.reuters.com/search/news?blob={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = []
        articles = soup.find_all('a', href=True)
        
        for article in articles[:10]:
            href = article.get('href', '')
            if '/article/' in href and article.text.strip():
                results.append({
                    'title': article.text.strip(),
                    'source': 'Reuters',
                    'url': f"https://www.reuters.com{href}",
                    'published_at': '',
                    'credibility': CREDIBILITY_SCORES['reuters.com'],
                    'api_source': 'Reuters'
                })
        
        return results
    except Exception as e:
        print(f"Reuters error: {e}")
        return []

def comprehensive_verification_api(text):
    """Provide comprehensive news verification for API endpoint"""
    all_results = []
    
    # Search across multiple sources
    if NEWS_API_KEY != 'your_news_api_key_here':
        newsapi_results = search_newsapi(text)
        all_results.extend(newsapi_results)
    
    google_results = search_google_news(text)
    all_results.extend(google_results)
    
    reuters_results = search_reuters(text)
    all_results.extend(reuters_results)
    
    # Remove duplicates and sort by credibility
    unique_results = []
    seen_titles = set()
    
    for result in all_results:
        title_lower = result['title'].lower()
        if title_lower not in seen_titles and len(title_lower) > 10:
            seen_titles.add(title_lower)
            unique_results.append(result)
    
    unique_results.sort(key=lambda x: x['credibility'], reverse=True)
    
    if unique_results:
        avg_credibility = sum(r['credibility'] for r in unique_results) / len(unique_results)
        content_analysis = analyze_content_quality(text)
        consistency_analysis = cross_reference_sources(unique_results)
        fact_analysis = fact_check_indicators(text, unique_results)
        
        verdict = determine_verdict(
            avg_credibility,
            consistency_analysis['score'],
            fact_analysis['fact_score'],
            content_analysis['quality_score'],
            len(unique_results)
        )
        
        return {
            'success': True,
            'verdict': verdict,
            'analysis': {
                'source_credibility': round(avg_credibility, 1),
                'cross_source_consistency': consistency_analysis,
                'fact_checking_score': fact_analysis['fact_score'],
                'content_quality': content_analysis['quality_score'],
                'source_count': len(unique_results)
            },
            'top_sources': unique_results[:5],
            'content_analysis': content_analysis
        }
    else:
        content_analysis = analyze_content_quality(text)
        fact_analysis = fact_check_indicators(text, [])
        
        return {
            'success': True,
            'verdict': {
                'verdict': 'UNVERIFIED',
                'confidence': 'LOW',
                'final_score': 0,
                'explanation': 'No matching news found in any source'
            },
            'analysis': {
                'source_credibility': 0,
                'cross_source_consistency': {'consistency': 'none', 'score': 0, 'details': 'No sources found'},
                'fact_checking_score': fact_analysis['fact_score'],
                'content_quality': content_analysis['quality_score'],
                'source_count': 0
            },
            'top_sources': [],
            'content_analysis': content_analysis
        }

@app.route('/')
def index():
    """Main page with news verification form"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """ML model prediction endpoint"""
    if model is None or embedder is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Clean and encode text
        cleaned_text = text.lower().strip()
        text_embedding = embedder.encode([cleaned_text])
        
        # Make prediction
        prediction = model.predict(text_embedding)[0]
        confidence = model.predict_proba(text_embedding)[0]
        
        result = {
            'text': text,
            'prediction': prediction,
            'confidence': float(max(confidence)),
            'probability_real': float(confidence[1] if prediction == 'real' else confidence[0]),
            'probability_fake': float(confidence[0] if prediction == 'real' else confidence[1])
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify', methods=['POST'])
def verify():
    """Comprehensive verification endpoint combining ML and online sources"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Get ML prediction if model is available
        ml_result = None
        if model is not None and embedder is not None:
            try:
                cleaned_text = text.lower().strip()
                text_embedding = embedder.encode([cleaned_text])
                prediction = model.predict(text_embedding)[0]
                confidence = model.predict_proba(text_embedding)[0]
                
                ml_result = {
                    'prediction': prediction,
                    'confidence': float(max(confidence)),
                    'probability_real': float(confidence[1] if prediction == 'real' else confidence[0]),
                    'probability_fake': float(confidence[0] if prediction == 'real' else confidence[1])
                }
            except Exception as e:
                print(f"ML prediction error: {e}")
        
        # Get online verification
        online_result = comprehensive_verification_api(text)
        
        # Combine results
        result = {
            'text': text,
            'ml_prediction': ml_result,
            'online_verification': online_result,
            'timestamp': str(datetime.now())
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify-online', methods=['POST'])
def verify_online():
    """Pure online verification endpoint (no ML)"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        result = comprehensive_verification_api(text)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/live-news')
def live_news():
    """Fetch and analyze live news headlines"""
    try:
        # Fetch news from Google News RSS
        rss_url = "https://news.google.com/rss/topstories"
        response = requests.get(rss_url, timeout=10)
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')[:10]
        
        news_items = []
        for item in items:
            if item.title and item.title.text:
                title = item.title.text
                source = item.source.text if item.source else 'Unknown'
                
                # Get ML prediction if available
                ml_result = None
                if model is not None and embedder is not None:
                    try:
                        text_embedding = embedder.encode([title])
                        prediction = model.predict(text_embedding)[0]
                        confidence = model.predict_proba(text_embedding)[0]
                        
                        ml_result = {
                            'prediction': prediction,
                            'confidence': float(max(confidence))
                        }
                    except:
                        pass
                
                news_items.append({
                    'title': title,
                    'source': source,
                    'url': item.link.text if item.link else '',
                    'published_at': item.pubDate.text if item.pubDate else '',
                    'ml_prediction': ml_result
                })
        
        return jsonify({'news': news_items})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
