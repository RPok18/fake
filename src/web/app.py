import os
import re
import json
import logging
from datetime import datetime
from functools import lru_cache


import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template, url_for

from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=frozenset(['GET', 'POST']))
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)
session.mount('http://', adapter)



from config.config import ROOT_DIR, CREDIBILITY_SCORES, get_credibility_score



model = None
embedder = None
np = None
joblib = None

def get_ml_resources():
    """Lazy load ML resources"""
    global model, embedder, np, joblib
    if model is None or embedder is None:
        try:
            logger.info("Loading ML model and embedder...")
            import joblib as _joblib
            import numpy as _np
            from sentence_transformers import SentenceTransformer as _SentenceTransformer
            
            # Assign to globals so they can be used elsewhere
            joblib = _joblib
            np = _np
            
            model = joblib.load(os.path.join(ROOT_DIR, 'data', 'fake_news_model.pkl'))
            embedder = _SentenceTransformer(os.path.join(ROOT_DIR, 'data', 'sentence_embedder'))
            logger.info("✅ Model and embedder loaded successfully")
        except Exception as e:
            logger.exception("❌ Error loading model/embedder: %s", e)
            model = None
            embedder = None
            np = None
    return model, embedder



NEWS_API_KEY = os.getenv('NEWS_API_KEY')
if not NEWS_API_KEY or NEWS_API_KEY == '10a09f51f6ed4b6494bda63da3a64b59':
    logger.warning("⚠️  No valid NewsAPI key found in .env. Please set NEWS_API_KEY.")
else:
    logger.info("✅ Using NewsAPI key from environment")


# CREDIBILITY_SCORES and get_credibility_score imported from config.config


def analyze_content_quality(text):
    """Analyze the quality and characteristics of the news text"""
    if not isinstance(text, str):
        text = str(text or "")
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
    """Cross-reference information across multiple sources (simple phrase overlap)."""
    if len(results) < 2:
        return {'consistency': 'low', 'score': 30, 'details': 'Only one source found'}

    key_phrases = []
    for result in results:
        title = (result.get('title') or '').lower()
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

def determine_verdict(credibility_score, consistency_score, fact_score, content_quality, source_count, top_sources=None):
    """Determine final TRUE/FALSE verdict based on comprehensive analysis.

    This version rewards finding high-credibility sources heavily.
    """
    source_factor = (min(source_count, 5) / 5) * 100  # 0..100
    
    # Check for authoritative sources
    high_cred_sources = 0
    if top_sources:
        for s in top_sources:
            if s.get('credibility', 0) >= 80:
                high_cred_sources += 1

    # Weights sum to 1.0 (tweak if desired)
    w_cred = 0.35      # Increased from 0.28
    w_cons = 0.25      # Increased from 0.22
    w_fact = 0.15      # Reduced from 0.22 (naive regex is less reliable)
    w_quality = 0.10   # Reduced from 0.13
    w_sources = 0.15

    base_score = (
        credibility_score * w_cred +
        consistency_score * w_cons +
        fact_score * w_fact +
        content_quality * w_quality +
        source_factor * w_sources
    )

    # BOOST: If we found at least one highly credible source (Reuters, AP, BBC, etc.),
    # we should trust it significantly more than our regex heuristics.
    final_score = base_score
    if high_cred_sources >= 1:
        final_score = max(final_score, 85.0)  # At least LIKELY TRUE
        if high_cred_sources >= 2:
            final_score = max(final_score, 92.0) # Almost certainly TRUE
        
    final_score = max(0.0, min(100.0, final_score))

    if final_score >= 80:
        verdict = "TRUE"
        confidence = "HIGH"
        explanation = "Multiple credible sources (like Reuters, AP, or major networks) confirm this news."
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


@lru_cache(maxsize=128)
def cached_search_newsapi(query):
    """Cached wrapper for NewsAPI search. Returns a JSON-serializable tuple of results."""
    
    try:
        if not NEWS_API_KEY or NEWS_API_KEY == '10a09f51f6ed4b6494bda63da3a64b59' or NEWS_API_KEY == 'your_news_api_key_here':
             logger.warning("Skipping NewsAPI search: No valid API key provided")
             return tuple()

        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 10
        }
        resp = session.get(url, params=params, timeout=3)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for article in data.get('articles', []):
            source_name = article.get('source', {}).get('name', 'Unknown')
            credibility = get_credibility_score(source_name)
            results.append({
                'title': article.get('title', '') or '',
                'source': source_name,
                'url': article.get('url', '') or '',
                'published_at': article.get('publishedAt', '') or '',
                'credibility': credibility,
                'api_source': 'NewsAPI'
            })
        return tuple(results)
    except Exception as e:
        logger.exception("NewsAPI error: %s", e)
        return tuple()

@lru_cache(maxsize=128)
def cached_search_google_news(query):
    """Cached wrapper for Google News RSS search."""
    try:
        logger.info(f"Searching Google News for: {query}")
        rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = session.get(rss_url, headers=headers, timeout=3)
        resp.raise_for_status()
        logger.info(f"Google News RSS response status: {resp.status_code}, length: {len(resp.content)}")
        
        soup = BeautifulSoup(resp.content, 'xml')
        items = soup.find_all('item')[:10]
        logger.info(f"Found {len(items)} items in Google News RSS")
        
        results = []
        for item in items:
            title = item.title.text if item.find('title') and item.title and item.title.text else ''
            source_name = item.source.text if item.find('source') and item.source and item.source.text else 'Unknown'
            url = item.link.text if item.find('link') and item.link and item.link.text else ''
            published = item.pubDate.text if item.find('pubDate') and item.pubDate and item.pubDate.text else ''
            credibility = get_credibility_score(source_name)
            if title:
                results.append({
                    'title': title,
                    'source': source_name,
                    'url': url,
                    'published_at': published,
                    'credibility': credibility,
                    'api_source': 'Google News'
                })
        logger.info(f"Google News returned {len(results)} valid results")
        return tuple(results)
    except Exception as e:
        logger.exception("Google News error: %s", e)
        return tuple()

@lru_cache(maxsize=128)
def cached_search_reuters(query):
    """Cached wrapper for a very small Reuters scrape. Returns tuple of results."""
    try:
        search_url = f"https://www.reuters.com/search/news?blob={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = session.get(search_url, headers=headers, timeout=3)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        results = []
        # Find links; be conservative about what we claim is an article
        anchors = soup.find_all('a', href=True)
        for a in anchors:
            href = a.get('href', '')
            text = a.text.strip() or ''
            if '/article/' in href and text:
                full_url = href if href.startswith('http') else f"https://www.reuters.com{href}"
                results.append({
                    'title': text,
                    'source': 'Reuters',
                    'url': full_url,
                    'published_at': '',
                    'credibility': CREDIBILITY_SCORES.get('reuters.com', 98),
                    'api_source': 'Reuters'
                })
            if len(results) >= 10:
                break
        return tuple(results)
    except Exception as e:
        logger.exception("Reuters error: %s", e)
        return tuple()

@lru_cache(maxsize=128)
def cached_search_indian_news(query):
    """Cached wrapper for Indian news sources search."""
    try:
        logger.info(f"Searching Indian news sources for: {query}")
        
        # Search The Hindu RSS feed
        hindu_rss_url = f"https://www.thehindu.com/news/national/?service=rss"
        results = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            resp = session.get(hindu_rss_url, headers=headers, timeout=3)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'xml')
            items = soup.find_all('item')[:5]
            
            for item in items:
                title = item.title.text if item.find('title') and item.title and item.title.text else ''
                url = item.link.text if item.find('link') and item.link and item.link.text else ''
                published = item.pubDate.text if item.find('pubDate') and item.pubDate and item.pubDate.text else ''
                
               
                query_terms = query.lower().split()
                title_lower = title.lower()
                if any(term in title_lower for term in query_terms):
                    credibility = get_credibility_score('thehindu.com')
                    results.append({
                        'title': title,
                        'source': 'The Hindu',
                        'url': url,
                        'published_at': published,
                        'credibility': credibility,
                        'api_source': 'Indian News'
                    })
        except Exception as e:
            logger.exception("The Hindu RSS error: %s", e)
        
       
        try:
            toi_rss_url = f"https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
            resp = session.get(toi_rss_url, headers=headers, timeout=3)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'xml')
            items = soup.find_all('item')[:5]
            
            for item in items:
                title = item.title.text if item.find('title') and item.title and item.title.text else ''
                url = item.link.text if item.find('link') and item.link and item.link.text else ''
                published = item.pubDate.text if item.find('pubDate') and item.pubDate and item.pubDate.text else ''
                
               
                query_terms = query.lower().split()
                title_lower = title.lower()
                if any(term in title_lower for term in query_terms):
                    credibility = get_credibility_score('timesofindia.indiatimes.com')
                    results.append({
                        'title': title,
                        'source': 'Times of India',
                        'url': url,
                        'published_at': published,
                        'credibility': credibility,
                        'api_source': 'Indian News'
                    })
        except Exception as e:
            logger.exception("Times of India RSS error: %s", e)
        
        logger.info(f"Indian news sources returned {len(results)} results")
        return tuple(results)
    except Exception as e:
        logger.exception("Indian news search error: %s", e)
        return tuple()


def comprehensive_verification_api(text):
    """Provide comprehensive news verification for API endpoint"""
    all_results = []

    
    try:
        if NEWS_API_KEY != '10a09f51f6ed4b6494bda63da3a64b59':
            all_results.extend(list(cached_search_newsapi(text)))
    except Exception:
        logger.exception("cached_search_newsapi failed")

    try:
        google_results = list(cached_search_google_news(text))
        logger.info(f"Google News returned {len(google_results)} results")
        all_results.extend(google_results)
    except Exception:
        logger.exception("cached_search_google_news failed")

    try:
        all_results.extend(list(cached_search_reuters(text)))
    except Exception:
        logger.exception("cached_search_reuters failed")

    try:
        indian_results = list(cached_search_indian_news(text))
        logger.info(f"Indian news sources returned {len(indian_results)} results")
        all_results.extend(indian_results)
    except Exception:
        logger.exception("cached_search_indian_news failed")

    logger.info(f"Total results before filtering: {len(all_results)}")

    
    unique_results = []
    seen_titles = set()
    for result in all_results:
        title_lower = (result.get('title') or '').lower().strip()
        if not title_lower or len(title_lower) <= 10:
            logger.info(f"Filtering out short title: '{title_lower}' (length: {len(title_lower)})")
            continue
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_results.append(result)
        else:
            logger.info(f"Filtering out duplicate title: '{title_lower}'")

    logger.info(f"Results after filtering: {len(unique_results)}")

   
    unique_results.sort(key=lambda x: x.get('credibility', 0), reverse=True)

    if unique_results:
        logger.info(f"Processing {len(unique_results)} unique results")
        avg_credibility = sum(r.get('credibility', 0) for r in unique_results) / len(unique_results)
        content_analysis = analyze_content_quality(text)
        consistency_analysis = cross_reference_sources(unique_results)
        fact_analysis = fact_check_indicators(text, unique_results)

        verdict = determine_verdict(
            avg_credibility,
            consistency_analysis.get('score', 0),
            fact_analysis.get('fact_score', 0),
            content_analysis.get('quality_score', 0),
            len(unique_results),
            top_sources=unique_results[:5]
        )

        logger.info(f"Returning results with {len(unique_results)} sources")
        return {
            'success': True,
            'verdict': verdict,
            'analysis': {
                'source_credibility': round(avg_credibility, 1),
                'cross_source_consistency': consistency_analysis,
                'fact_checking_score': fact_analysis.get('fact_score', 0),
                'content_quality': content_analysis.get('quality_score', 0),
                'source_count': len(unique_results)
            },
            'top_sources': unique_results[:5],
            'content_analysis': content_analysis
        }

   
    logger.info("No unique results found, returning UNVERIFIED")
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
            'fact_checking_score': fact_analysis.get('fact_score', 0),
            'content_quality': content_analysis.get('quality_score', 0),
            'source_count': 0
        },
        'top_sources': [],
        'content_analysis': content_analysis
    }


@app.route('/')
def index_route():
    """Main page with news verification form"""
   
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """ML model prediction endpoint - robust mapping of class labels and probabilities"""
    model, embedder = get_ml_resources()
    if model is None or embedder is None:
        return jsonify({'error': 'Model or embedder not loaded'}), 500

    try:
        data = request.get_json(force=True)
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        cleaned_text = text.lower().strip()

       
        try:
            embedding = embedder.encode([cleaned_text])
        except TypeError:
           
            embedding = embedder.encode([cleaned_text], convert_to_numpy=True)

        embedding = np.asarray(embedding)
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)

       
        try:
            pred_label = model.predict(embedding)[0]
        except Exception as e:
            return jsonify({'error': f'Model predict error: {str(e)}'}), 500

        probabilities = None
        if hasattr(model, 'predict_proba'):
            try:
                probabilities = model.predict_proba(embedding)[0]
            except Exception as e:
                logger.exception("predict_proba failed: %s", e)
                probabilities = None

        result = {'text': text, 'prediction': str(pred_label)}

        if probabilities is not None and hasattr(model, 'classes_'):
            class_list = list(model.classes_)
            prob_map = {class_list[i]: float(probabilities[i]) for i in range(len(class_list))}
            result['probabilities'] = prob_map
            # Provide probability_real and probability_fake where possible
            result['probability_real'] = float(prob_map.get('real', prob_map.get('true', 0.0)))
            result['probability_fake'] = float(prob_map.get('fake', prob_map.get('false', 0.0)))
            result['confidence'] = float(max(probabilities))
        else:
            # best-effort fallback
            result['probabilities'] = None
            result['probability_real'] = None
            result['probability_fake'] = None
            result['confidence'] = float(max(probabilities)) if probabilities is not None else None

        return jsonify(result)

    except Exception as e:
        logger.exception("Predict endpoint error: %s", e)
        return jsonify({'error': str(e)}), 500

@app.route('/verify', methods=['POST'])
def verify():
    """Comprehensive verification endpoint combining ML and online sources"""
    try:
        data = request.get_json(force=True)
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        ml_result = None
        model, embedder = get_ml_resources()
        if model is not None and embedder is not None:
            try:
                cleaned_text = text.lower().strip()
                emb = embedder.encode([cleaned_text])
                emb = np.asarray(emb)
                if emb.ndim == 1:
                    emb = emb.reshape(1, -1)

                pred = model.predict(emb)[0]
                probs = None
                if hasattr(model, 'predict_proba'):
                    probs = model.predict_proba(emb)[0]
                ml_result = {'prediction': str(pred)}
                if probs is not None and hasattr(model, 'classes_'):
                    class_list = list(model.classes_)
                    prob_map = {class_list[i]: float(probs[i]) for i in range(len(class_list))}
                    ml_result['probabilities'] = prob_map
                    ml_result['confidence'] = float(max(probs))
                else:
                    ml_result['probabilities'] = None
                    ml_result['confidence'] = float(max(probs)) if probs is not None else None
            except Exception as e:
                logger.exception("ML prediction error in /verify: %s", e)

        online_result = comprehensive_verification_api(text)

        result = {
            'text': text,
            'ml_prediction': ml_result,
            'online_verification': online_result,
            'timestamp': str(datetime.utcnow())
        }
        return jsonify(result)

    except Exception as e:
        logger.exception("Verify endpoint error: %s", e)
        return jsonify({'error': str(e)}), 500

@app.route('/verify-online', methods=['POST'])
def verify_online():
    """Pure online verification endpoint (no ML)"""
    try:
        data = request.get_json(force=True)
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        result = comprehensive_verification_api(text)
        return jsonify(result)
    except Exception as e:
        logger.exception("Verify-online endpoint error: %s", e)
        return jsonify({'error': str(e)}), 500

@app.route('/live-news')
def live_news():
    """Fetch and analyze live news headlines"""
    try:
        rss_url = "https://news.google.com/rss/topstories"
        resp = session.get(rss_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'xml')
        items = soup.find_all('item')[:10]
        news_items = []
        for item in items:
            title = item.title.text if item.find('title') and item.title and item.title.text else ''
            source = item.source.text if item.find('source') and item.source and item.source.text else 'Unknown'
            url = item.link.text if item.find('link') and item.link and item.link.text else ''
            published_at = item.pubDate.text if item.find('pubDate') and item.pubDate and item.pubDate.text else ''

            ml_result = None
            model, embedder = get_ml_resources()
            if model is not None and embedder is not None and title:
                try:
                    emb = embedder.encode([title])
                    emb = np.asarray(emb)
                    if emb.ndim == 1:
                        emb = emb.reshape(1, -1)
                    pred = model.predict(emb)[0]
                    probs = None
                    if hasattr(model, 'predict_proba'):
                        probs = model.predict_proba(emb)[0]
                    ml_result = {'prediction': str(pred)}
                    if probs is not None and hasattr(model, 'classes_'):
                        ml_result['confidence'] = float(max(probs))
                except Exception:
                    # swallow; we don't want live-news to fail because of ML predict issues
                    logger.exception("ML predict error for live-news title: %s", title)

            news_items.append({
                'title': title,
                'source': source,
                'url': url,
                'published_at': published_at,
                'ml_prediction': ml_result
            })

        return jsonify({'news': news_items})
    except Exception as e:
        logger.exception("Live news error: %s", e)
        return jsonify({'error': str(e)}), 500

# ---------------------------------------------------------------------
# Run app
# ---------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
