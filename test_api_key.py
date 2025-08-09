#!/usr/bin/env python3
"""
Test script to verify your NewsAPI key is working correctly
Run this script after setting your API key in config_local.py
"""

import requests
import sys

def test_newsapi_key():
    """Test if the NewsAPI key is working"""
    
    # Try to import the API key
    try:
        from config_local import NEWS_API_KEY
        print(f"✅ Found API key: {NEWS_API_KEY[:10]}...")
    except ImportError:
        print("❌ config_local.py not found!")
        print("Please create config_local.py with your NEWS_API_KEY")
        return False
    except NameError:
        print("❌ NEWS_API_KEY not found in config_local.py!")
        print("Please add NEWS_API_KEY = 'your_key_here' to config_local.py")
        return False
    
    # Check if it's still the placeholder
    if NEWS_API_KEY == "your_actual_news_api_key_here":
        print("❌ API key is still the placeholder value!")
        print("Please replace 'your_actual_news_api_key_here' with your real API key")
        return False
    
    # Test the API
    print("🔍 Testing NewsAPI connection...")
    
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'country': 'us',
            'apiKey': NEWS_API_KEY,
            'pageSize': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('articles'):
                article = data['articles'][0]
                print("✅ API key is working!")
                print(f"📰 Sample article: {article.get('title', 'No title')}")
                print(f"📊 Total articles available: {data.get('totalResults', 'Unknown')}")
                return True
            else:
                print("⚠️  API responded but no articles found")
                return False
        elif response.status_code == 401:
            print("❌ API key is invalid or expired!")
            print("Please check your API key at https://newsapi.org/")
            return False
        elif response.status_code == 429:
            print("⚠️  Rate limit exceeded!")
            print("Free tier allows 100 requests per day")
            return False
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔑 NewsAPI Key Test")
    print("=" * 30)
    
    success = test_newsapi_key()
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 Your API key is working correctly!")
        print("You can now run the main application with full functionality.")
    else:
        print("💡 To fix the issue:")
        print("1. Go to https://newsapi.org/")
        print("2. Sign up for a free account")
        print("3. Get your API key")
        print("4. Add it to config_local.py")
        print("5. Run this test again")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
