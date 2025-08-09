# 🔑 API Key Setup Guide

## Quick Setup

### 1. Get Your NewsAPI Key
1. Go to [https://newsapi.org/](https://newsapi.org/)
2. Click "Get API Key" 
3. Sign up for a free account
4. Copy your API key (looks like: `abc123def456ghi789jkl012mno345pqr678stu901`)

### 2. Configure Your API Key
1. **Edit `config_local.py`** (already created for you)
2. Replace `"your_actual_news_api_key_here"` with your real API key
3. Save the file

Example:
```python
NEWS_API_KEY = "abc123def456ghi789jkl012mno345pqr678stu901"
```

### 3. Test Your Setup
Run the test script to verify everything works:
```bash
python test_api_key.py
```

## What This Gives You

✅ **Full NewsAPI functionality** - 100 requests/day (free tier)  
✅ **Comprehensive news verification** across multiple sources  
✅ **Real-time news data** for fact-checking  
✅ **Source credibility scoring**  

## Current Status

The program now has **3 ways** to get news data:

1. **NewsAPI** (requires your key) - Most comprehensive
2. **Google News RSS** (free) - No key needed  
3. **Reuters scraping** (free) - No key needed

## Troubleshooting

### If you get "No valid NewsAPI key found":
- Make sure you edited `config_local.py`
- Check that your API key is correct
- Run `python test_api_key.py` to test

### If you get "API key is invalid":
- Verify your key at [https://newsapi.org/](https://newsapi.org/)
- Make sure you copied the entire key
- Check if you've exceeded the free tier limit (100 requests/day)

## Security Notes

- ✅ `config_local.py` is in `.gitignore` (won't be committed)
- ✅ Your API key stays local to your machine
- ✅ Never share your API key publicly
- ✅ Free tier is sufficient for testing and personal use

## Next Steps

Once your API key is working:
1. Run `python app.py` to start the web application
2. Use the `/verify` endpoint for comprehensive news verification
3. The app will now use NewsAPI + free sources for maximum coverage
