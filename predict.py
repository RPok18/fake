import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os
import re
from urllib.parse import urlparse

# News API configuration (you'll need to get a free API key from https://newsapi.org/)
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '10a09f51f6ed4b6494bda63da3a64b59')

# Credibility scores for different news sources (0-100, higher = more credible)
CREDIBILITY_SCORES = {
    # Tier 1: Most Credible (90-100)
    'reuters.com': 98, 'reuters': 98,
    'ap.org': 97, 'apnews.com': 97, 'associated press': 97,
    'bbc.com': 96, 'bbc.co.uk': 96, 'bbc': 96,
    'npr.org': 95, 'npr': 95,
    'pbs.org': 94, 'pbs': 94,
    
    # Tier 2: Highly Credible (80-89)
    'nytimes.com': 88, 'nytimes': 88,
    'washingtonpost.com': 87, 'washington post': 87,
    'wsj.com': 86, 'wall street journal': 86,
    'economist.com': 85, 'economist': 85,
    'time.com': 84, 'time': 84,
    'cnn.com': 83, 'cnn': 83,
    'abcnews.go.com': 82, 'abc news': 82,
    'cbsnews.com': 81, 'cbs news': 81,
    'nbcnews.com': 80, 'nbc news': 80,
    
    # Tier 3: Credible (70-79)
    'usatoday.com': 78, 'usa today': 78,
    'foxnews.com': 75, 'fox news': 75,
    'msnbc.com': 74, 'msnbc': 74,
    'huffpost.com': 72, 'huffington post': 72,
    'vox.com': 71, 'vox': 71,
    
    # Tier 4: Generally Reliable (60-69)
    'theguardian.com': 68, 'guardian': 68,
    'independent.co.uk': 65, 'independent': 65,
    'telegraph.co.uk': 64, 'telegraph': 64,
    'dailymail.co.uk': 62, 'daily mail': 62,
    
    # Tier 5: Variable Reliability (50-59)
    'forbes.com': 58, 'forbes': 58,
    'businessinsider.com': 55, 'business insider': 55,
    'techcrunch.com': 54, 'techcrunch': 54,
    'buzzfeed.com': 52, 'buzzfeed': 52,
    
    # Default score for unknown sources
    'default': 50
}

def get_credibility_score(source_name):
    """Get credibility score for a news source"""
    if not source_name:
        return CREDIBILITY_SCORES['default']
    
    source_lower = source_name.lower().strip()
    
    # Check exact matches first
    if source_lower in CREDIBILITY_SCORES:
        return CREDIBILITY_SCORES[source_lower]
    
    # Check partial matches
    for key, score in CREDIBILITY_SCORES.items():
        if key in source_lower or source_lower in key:
            return score
    
    # Check for common patterns
    if any(word in source_lower for word in ['news', 'times', 'post', 'journal', 'tribune']):
        return 65  # Likely a traditional news source
    elif any(word in source_lower for word in ['blog', 'medium', 'substack']):
        return 45  # Likely a blog/opinion piece
    
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
    
    # Calculate quality score
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
    
    # Extract key information from titles
    key_phrases = []
    for result in results:
        title = result['title'].lower()
        # Extract key nouns and phrases
        phrases = re.findall(r'\b[a-z]+(?:\s+[a-z]+)*\b', title)
        key_phrases.extend([p for p in phrases if len(p) > 3])
    
    # Count frequency of key phrases
    phrase_counts = {}
    for phrase in key_phrases:
        phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
    
    # Calculate consistency score
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
    
    # Check for verifiable claims
    if re.search(r'\b\d+%\b|\b\d+\s+(million|billion|thousand)\b', text):
        indicators['verifiable_claims'] += 1
    
    # Check for specific details
    if re.search(r'\b\d{1,2}:\d{2}\b|\b\d{1,2}:\d{2}\s*(am|pm)\b', text):
        indicators['specific_details'] += 1
    
    # Check for attributable statements
    if re.search(r'\b(according to|said|reported|announced|confirmed)\b', text):
        indicators['attributable_statements'] += 1
    
    # Check for red flags
    red_flag_patterns = [
        r'\b(conspiracy|cover-up|secret|hidden|suppressed)\b',
        r'\b(100%|guaranteed|definitely|absolutely)\b',
        r'\b(urgent|breaking|exclusive|shocking)\b',
        r'\b(they don\'t want you to know|mainstream media won\'t report)\b'
    ]
    
    for pattern in red_flag_patterns:
        if re.search(pattern, text.lower()):
            indicators['red_flags'] += 1
    
    # Calculate fact-check score
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
    
    # Weighted scoring system
    final_score = (
        credibility_score * 0.3 +      # Source credibility (30%)
        consistency_score * 0.25 +     # Cross-source consistency (25%)
        fact_score * 0.25 +           # Fact-checking indicators (25%)
        content_quality * 0.15 +      # Content quality (15%)
        min(source_count * 5, 25)     # Source count bonus (up to 25%)
    )
    
    # Determine verdict
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
    """Search using NewsAPI (requires API key)"""
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
        # Reuters search URL
        search_url = f"https://www.reuters.com/search/news?blob={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = []
        # Look for article links (this is a simplified approach)
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

def comprehensive_verification(text):
    """Provide comprehensive news verification with TRUE/FALSE verdict"""
    print(f"\n=== Verifying: {text} ===\n")
    
    # Search across multiple sources
    print("🔍 Searching multiple news sources...")
    
    all_results = []
    
    # 1. NewsAPI (if key is available)
    if NEWS_API_KEY != 'your_news_api_key_here':
        print("📰 Searching NewsAPI...")
        newsapi_results = search_newsapi(text)
        all_results.extend(newsapi_results)
        print(f"   Found {len(newsapi_results)} results")
    
    # 2. Google News
    print("🌐 Searching Google News...")
    google_results = search_google_news(text)
    all_results.extend(google_results)
    print(f"   Found {len(google_results)} results")
    
    # 3. Reuters
    print("📊 Searching Reuters...")
    reuters_results = search_reuters(text)
    all_results.extend(reuters_results)
    print(f"   Found {len(reuters_results)} results")
    
    # Remove duplicates and sort by credibility
    unique_results = []
    seen_titles = set()
    
    for result in all_results:
        title_lower = result['title'].lower()
        if title_lower not in seen_titles and len(title_lower) > 10:
            seen_titles.add(title_lower)
            unique_results.append(result)
    
    # Sort by credibility score (highest first)
    unique_results.sort(key=lambda x: x['credibility'], reverse=True)
    
    print(f"\n📊 Total unique results: {len(unique_results)}")
    
    if unique_results:
        # Calculate key metrics
        avg_credibility = sum(r['credibility'] for r in unique_results) / len(unique_results)
        
        # Content analysis
        print("\n🔍 Analyzing content quality...")
        content_analysis = analyze_content_quality(text)
        
        # Cross-reference sources
        print("🔗 Cross-referencing sources...")
        consistency_analysis = cross_reference_sources(unique_results)
        
        # Fact-checking indicators
        print("✅ Checking fact-checking indicators...")
        fact_analysis = fact_check_indicators(text, unique_results)
        
        # Determine final verdict
        print("🎯 Determining final verdict...")
        verdict = determine_verdict(
            avg_credibility,
            consistency_analysis['score'],
            fact_analysis['fact_score'],
            content_analysis['quality_score'],
            len(unique_results)
        )
        
        # Display comprehensive results
        print(f"\n{'='*60}")
        print(f"🎯 FINAL VERDICT: {verdict['verdict']}")
        print(f"📊 Confidence: {verdict['confidence']}")
        print(f"🏆 Overall Score: {verdict['final_score']}/100")
        print(f"💡 Explanation: {verdict['explanation']}")
        print(f"{'='*60}")
        
        # Detailed breakdown
        print(f"\n📊 DETAILED ANALYSIS:")
        print(f"   🔍 Source Credibility: {avg_credibility:.1f}/100")
        print(f"   🔗 Cross-Source Consistency: {consistency_analysis['score']}/100 ({consistency_analysis['consistency']})")
        print(f"   ✅ Fact-Checking Score: {fact_analysis['fact_score']}/100")
        print(f"   📝 Content Quality: {content_analysis['quality_score']}/100")
        print(f"   📰 Number of Sources: {len(unique_results)}")
        
        # Content analysis details
        print(f"\n📝 CONTENT ANALYSIS:")
        print(f"   📏 Length: {content_analysis['length']} characters")
        print(f"   🔢 Has Numbers: {'✅' if content_analysis['has_numbers'] else '❌'}")
        print(f"   📅 Has Dates: {'✅' if content_analysis['has_dates'] else '❌'}")
        print(f"   👤 Has Names: {'✅' if content_analysis['has_names'] else '❌'}")
        print(f"   💬 Has Quotes: {'✅' if content_analysis['has_quotes'] else '❌'}")
        print(f"   📰 Has Sources: {'✅' if content_analysis['has_sources'] else '❌'}")
        print(f"   😤 Emotional Language: {content_analysis['emotional_language']} instances")
        print(f"   ⚠️  Exaggeration Words: {content_analysis['exaggeration_words']} instances")
        
        # Show top results with credibility scores
        print(f"\n🏆 Top {min(5, len(unique_results))} most credible sources:")
        for i, result in enumerate(unique_results[:5], 1):
            credibility_emoji = "🟢" if result['credibility'] >= 80 else "🟡" if result['credibility'] >= 60 else "🟠" if result['credibility'] >= 40 else "🔴"
            print(f"   {i}. {credibility_emoji} {result['title']}")
            print(f"      Source: {result['source']} (Credibility: {result['credibility']}/100)")
            print(f"      API: {result['api_source']}")
            if result['url']:
                print(f"      Link: {result['url']}")
            print()
            
    else:
        print(f"\n❌ VERIFICATION RESULT: UNVERIFIED")
        print("   No matching news found in any source")
        print("   This could be:")
        print("   - Breaking news that hasn't been widely reported yet")
        print("   - Misinformation or fake news")
        print("   - News with different wording/terminology")
        print("   - Regional/local news not covered by major outlets")
        
        # Even without sources, analyze the content
        content_analysis = analyze_content_quality(text)
        fact_analysis = fact_check_indicators(text, [])
        
        print(f"\n📝 CONTENT ANALYSIS (No Sources Found):")
        print(f"   Content Quality Score: {content_analysis['quality_score']}/100")
        print(f"   Fact-Checking Score: {fact_analysis['fact_score']}/100")
        
        if fact_analysis['red_flags'] > 0:
            print(f"   ⚠️  Red Flags Detected: {fact_analysis['red_flags']}")
            print("   This suggests the content may be misleading or false.")
    
    return unique_results

def show_credibility_guide():
    """Show credibility scoring guide"""
    print("\n📊 CREDIBILITY SCORING GUIDE:")
    print("🟢 90-100: Most Credible (Reuters, AP, BBC, NPR)")
    print("🟡 80-89: Highly Credible (NYT, Washington Post, WSJ)")
    print("🟠 70-79: Credible (USA Today, CNN, ABC News)")
    print("🔴 60-69: Generally Reliable (Guardian, Independent)")
    print("⚫ 50-59: Variable Reliability (Forbes, Business Insider)")
    print("⚪ Below 50: Unknown or Low Reliability Sources")

def show_verdict_guide():
    """Show verdict explanation guide"""
    print("\n🎯 VERDICT EXPLANATION GUIDE:")
    print("✅ TRUE: Multiple credible sources confirm with consistent information")
    print("🟢 LIKELY TRUE: Several sources support, some details may need verification")
    print("🟡 UNCERTAIN: Mixed signals, credibility or consistency questionable")
    print("🔴 LIKELY FALSE: Multiple red flags suggest inaccuracy")
    print("❌ UNVERIFIED: No sources found, cannot determine truth")

if __name__ == "__main__":
    print("🔍 Enhanced News Verification Tool")
    print("=" * 60)
    print("📰 Multiple API Sources + Credibility Scoring + TRUE/FALSE Verdict")
    print("=" * 60)
    
    # Show guides
    show_credibility_guide()
    show_verdict_guide()
    
    while True:
        article = input("\nEnter news text (or 'help' for guides, 'quit' to exit): ")
        if article.lower() == 'quit':
            break
        elif article.lower() == 'help':
            show_credibility_guide()
            show_verdict_guide()
            continue
        
        comprehensive_verification(article)
        print("\n" + "="*60)