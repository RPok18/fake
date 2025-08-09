# Configuration file for Enhanced News Verification Tool
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Try to import local configuration (for API keys)
try:
    from config_local import *
    print("✅ Loaded local configuration with API keys")
except ImportError:
    print("⚠️  No local configuration found. Create config_local.py with your API keys.")

# =============================================================================
# API KEYS & CREDENTIALS
# =============================================================================

# News API Configuration
# Get your free API key from: https://newsapi.org/
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'your_news_api_key_here')

# Alternative News APIs (for future use)
# Reuters API (requires subscription)
REUTERS_API_KEY = os.getenv('REUTERS_API_KEY', '')

# Associated Press API (requires subscription)
AP_API_KEY = os.getenv('AP_API_KEY', '')

# BBC API (requires subscription)
BBC_API_KEY = os.getenv('BBC_API_KEY', '')

# Google News API (free, no key required)
GOOGLE_NEWS_ENABLED = True

# =============================================================================
# CREDIBILITY SCORING SYSTEM
# =============================================================================

# Credibility scores for different news sources (0-100 scale)
CREDIBILITY_SCORES = {
    # Tier 1: Most Credible Sources (90-100)
    'reuters.com': 98, 'reuters': 98, 'reuters.co.uk': 98,
    'ap.org': 97, 'apnews.com': 97, 'associated press': 97,
    'bbc.com': 96, 'bbc.co.uk': 96, 'bbc': 96, 'bbc.com/news': 96,
    'npr.org': 95, 'npr': 95,
    'pbs.org': 94, 'pbs': 94,
    
    # Tier 2: Highly Credible Sources (80-89)
    'nytimes.com': 88, 'nytimes': 88, 'nytimes.com': 88,
    'washingtonpost.com': 87, 'washington post': 87, 'washingtonpost': 87,
    'wsj.com': 86, 'wall street journal': 86, 'wsj.com': 86,
    'economist.com': 85, 'economist': 85,
    'time.com': 84, 'time': 84,
    'cnn.com': 83, 'cnn': 83,
    'abcnews.go.com': 82, 'abc news': 82,
    'cbsnews.com': 81, 'cbs news': 81,
    'nbcnews.com': 80, 'nbc news': 80,
    
    # Tier 3: Credible Sources (70-79)
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
    
    # Tier 6: Lower Reliability (40-49)
    'buzzfeed.com': 52, 'buzzfeed': 52,
    'default': 50
}

# =============================================================================
# SEARCH & API SETTINGS
# =============================================================================

# Search settings
SEARCH_TIMEOUT = int(os.getenv('SEARCH_TIMEOUT', '10'))  # seconds
MAX_RESULTS_PER_SOURCE = int(os.getenv('MAX_RESULTS_PER_SOURCE', '10'))
MIN_TITLE_LENGTH = int(os.getenv('MIN_TITLE_LENGTH', '10'))  # Minimum title length to consider valid

# User agent for web scraping
USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

# Rate limiting (requests per minute)
RATE_LIMIT = {
    'newsapi': int(os.getenv('NEWSAPI_RATE_LIMIT', '100')),
    'google_news': int(os.getenv('GOOGLE_NEWS_RATE_LIMIT', '60')),
    'reuters': int(os.getenv('REUTERS_RATE_LIMIT', '30'))
}

# =============================================================================
# VERDICT DETERMINATION WEIGHTS
# =============================================================================

# Weights for final verdict calculation
VERDICT_WEIGHTS = {
    'source_credibility': 0.30,      # Source credibility (30%)
    'cross_source_consistency': 0.25, # Cross-source consistency (25%)
    'fact_checking': 0.25,           # Fact-checking indicators (25%)
    'content_quality': 0.15,         # Content quality (15%)
    'source_count_bonus': 0.05       # Source count bonus (5%)
}

# Verdict thresholds
VERDICT_THRESHOLDS = {
    'TRUE': 80,
    'LIKELY_TRUE': 60,
    'UNCERTAIN': 40,
    'LIKELY_FALSE': 0
}

# =============================================================================
# CONTENT ANALYSIS SETTINGS
# =============================================================================

# Content quality scoring weights
CONTENT_WEIGHTS = {
    'has_numbers': 15,
    'has_dates': 15,
    'has_names': 15,
    'has_quotes': 15,
    'has_sources': 15,
    'emotional_language_penalty': -10,  # Per instance over threshold
    'exaggeration_words_penalty': -10,  # Per instance over threshold
    'length_bonus': 5                   # If length > 50 characters
}

# Thresholds for content analysis
CONTENT_THRESHOLDS = {
    'emotional_language_max': 3,      # Maximum emotional words before penalty
    'exaggeration_words_max': 2,      # Maximum exaggeration words before penalty
    'min_length': 50                  # Minimum length for bonus
}

# Fact-checking patterns
FACT_CHECK_PATTERNS = {
    'verifiable_claims': [
        r'\b\d+%\b',                    # Percentages
        r'\b\d+\s+(million|billion|thousand)\b',  # Large numbers
        r'\b\d{1,2}:\d{2}\b',          # Time
        r'\b\d{1,2}:\d{2}\s*(am|pm)\b' # Time with AM/PM
    ],
    'red_flags': [
        r'\b(conspiracy|cover-up|secret|hidden|suppressed)\b',
        r'\b(100%|guaranteed|definitely|absolutely)\b',
        r'\b(urgent|breaking|exclusive|shocking)\b',
        r'\b(they don\'t want you to know|mainstream media won\'t report)\b',
        r'\b(click here|subscribe now|limited time)\b'
    ]
}

# =============================================================================
# FLASK APPLICATION SETTINGS
# =============================================================================

# Flask configuration
FLASK_CONFIG = {
    'DEBUG': os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
    'HOST': os.getenv('FLASK_HOST', '0.0.0.0'),
    'PORT': int(os.getenv('FLASK_PORT', '5000')),
    'SECRET_KEY': os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this-in-production')
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Logging settings
LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.getenv('LOG_FILE', 'news_verification.log')
}

# =============================================================================
# CACHE SETTINGS
# =============================================================================

# Cache configuration for API responses
CACHE_CONFIG = {
    'enabled': os.getenv('CACHE_ENABLED', 'True').lower() == 'true',
    'ttl': int(os.getenv('CACHE_TTL', '300')),  # Time to live in seconds
    'max_size': int(os.getenv('CACHE_MAX_SIZE', '1000'))  # Maximum cache entries
}

# =============================================================================
# ERROR HANDLING
# =============================================================================

# Error handling settings
ERROR_CONFIG = {
    'max_retries': int(os.getenv('MAX_RETRIES', '3')),
    'retry_delay': int(os.getenv('RETRY_DELAY', '1')),  # seconds
    'show_detailed_errors': os.getenv('SHOW_DETAILED_ERRORS', 'False').lower() == 'true'
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_credibility_score(source_name):
    """Get credibility score for a news source"""
    if not source_name:
        return CREDIBILITY_SCORES['default']
    
    source_lower = source_name.lower().strip()
    
    # Direct match
    if source_lower in CREDIBILITY_SCORES:
        return CREDIBILITY_SCORES[source_lower]
    
    # Partial match
    for key, score in CREDIBILITY_SCORES.items():
        if key in source_lower or source_lower in key:
            return score
    
    # Pattern matching
    if any(word in source_lower for word in ['news', 'times', 'post', 'journal', 'tribune']):
        return 65
    elif any(word in source_lower for word in ['blog', 'medium', 'substack']):
        return 45
    elif any(word in source_lower for word in ['social', 'forum', 'reddit']):
        return 35
    
    return CREDIBILITY_SCORES['default']

def is_api_key_valid(api_name):
    """Check if an API key is valid (not default placeholder)"""
    api_keys = {
        'newsapi': NEWS_API_KEY,
        'reuters': REUTERS_API_KEY,
        'ap': AP_API_KEY,
        'bbc': BBC_API_KEY
    }
    
    key = api_keys.get(api_name, '')
    return key and key != 'your_news_api_key_here' and key != ''

def get_enabled_apis():
    """Get list of enabled APIs based on available keys"""
    enabled_apis = []
    
    if is_api_key_valid('newsapi'):
        enabled_apis.append('newsapi')
    
    if GOOGLE_NEWS_ENABLED:
        enabled_apis.append('google_news')
    
    if is_api_key_valid('reuters'):
        enabled_apis.append('reuters')
    
    return enabled_apis

# =============================================================================
# ENVIRONMENT VALIDATION
# =============================================================================

def validate_config():
    """Validate configuration and return any issues"""
    issues = []
    
    if not is_api_key_valid('newsapi'):
        issues.append("NEWS_API_KEY not set - NewsAPI functionality will be limited")
    
    if not get_enabled_apis():
        issues.append("No news APIs are enabled - online verification will not work")
    
    if FLASK_CONFIG['SECRET_KEY'] == 'your-secret-key-change-this-in-production':
        issues.append("FLASK_SECRET_KEY is using default value - change in production")
    
    return issues

# =============================================================================
# CONFIGURATION EXPORT
# =============================================================================

# Export all configuration variables
__all__ = [
    'NEWS_API_KEY', 'REUTERS_API_KEY', 'AP_API_KEY', 'BBC_API_KEY',
    'CREDIBILITY_SCORES', 'SEARCH_TIMEOUT', 'MAX_RESULTS_PER_SOURCE',
    'MIN_TITLE_LENGTH', 'USER_AGENT', 'RATE_LIMIT', 'VERDICT_WEIGHTS',
    'VERDICT_THRESHOLDS', 'CONTENT_WEIGHTS', 'CONTENT_THRESHOLDS',
    'FACT_CHECK_PATTERNS', 'FLASK_CONFIG', 'LOGGING_CONFIG',
    'CACHE_CONFIG', 'ERROR_CONFIG', 'get_credibility_score',
    'is_api_key_valid', 'get_enabled_apis', 'validate_config'
]

if __name__ == "__main__":
    # Print configuration summary
    print("🔧 Enhanced News Verification Tool Configuration")
    print("=" * 50)
    
    print(f"📰 News APIs Enabled: {', '.join(get_enabled_apis())}")
    print(f"🔍 Search Timeout: {SEARCH_TIMEOUT}s")
    print(f"📊 Max Results per Source: {MAX_RESULTS_PER_SOURCE}")
    print(f"🎯 Verdict Thresholds: {VERDICT_THRESHOLDS}")
    
    # Check for configuration issues
    issues = validate_config()
    if issues:
        print("\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("\n✅ Configuration is valid!")
    
    print("\n💡 To enable NewsAPI, set the NEWS_API_KEY environment variable")
    print("   Get your free key from: https://newsapi.org/")
