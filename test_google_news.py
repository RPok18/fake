import requests
from bs4 import BeautifulSoup

def test_google_news():
    try:
        response = requests.get('https://news.google.com/rss/search?q=Biden')
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        print(f"Found {len(items)} items")
        
        for i, item in enumerate(items[:3]):
            title = item.find('title')
            source = item.find('source')
            print(f"Item {i+1}: Title={title.text if title else 'No title'}, Source={source.text if source else 'No source'}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_google_news()
