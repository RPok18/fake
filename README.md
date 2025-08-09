# 🔍 Enhanced News Verification Tool

A powerful news verification tool that searches multiple news sources and provides credibility scoring to help you determine if news is real or fake.

## ✨ Features

- **Multiple News Sources**: Google News, NewsAPI, Reuters
- **Credibility Scoring**: 0-100 scale for each news source
- **Real-time Verification**: Live search across multiple APIs
- **Duplicate Detection**: Removes duplicate articles automatically
- **Source Ranking**: Sorts results by credibility score
- **Comprehensive Assessment**: Provides overall reliability assessment

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install requests beautifulsoup4 newsapi-python
```

### 2. Get API Keys (Optional but Recommended)

#### NewsAPI (Free tier available)
1. Go to [https://newsapi.org/](https://newsapi.org/)
2. Sign up for a free account
3. Get your API key
4. Set environment variable:
   ```bash
   # Windows
   set NEWS_API_KEY=your_key_here
   
   # Linux/Mac
   export NEWS_API_KEY=your_key_here
   ```

### 3. Run the Tool
```bash
python predict.py
```

## 📊 Credibility Scoring System

| Score Range | Level | Examples |
|-------------|-------|----------|
| 🟢 90-100 | Most Credible | Reuters, AP, BBC, NPR |
| 🟡 80-89 | Highly Credible | NYT, Washington Post, WSJ |
| 🟠 70-79 | Credible | USA Today, CNN, ABC News |
| 🔴 60-69 | Generally Reliable | Guardian, Independent |
| ⚫ 50-59 | Variable Reliability | Forbes, Business Insider |
| ⚪ Below 50 | Unknown/Low Reliability | Unknown sources, blogs |

## 🔧 How It Works

1. **Input**: Enter any news text you want to verify
2. **Multi-Source Search**: Searches across multiple news APIs simultaneously
3. **Credibility Scoring**: Assigns credibility scores to each source
4. **Duplicate Removal**: Eliminates duplicate articles
5. **Ranking**: Sorts results by credibility score
6. **Assessment**: Provides overall reliability assessment

## 📰 Supported News Sources

### Free Sources (No API Key Required)
- **Google News RSS** - Comprehensive news aggregation
- **Reuters** - Basic web scraping (limited)

### Premium Sources (Require API Key)
- **NewsAPI** - 100+ news sources, 100 requests/day free
- **Reuters API** - Premium subscription required
- **Associated Press API** - Premium subscription required
- **BBC API** - Premium subscription required

## 💡 Usage Examples

### Basic Verification
```
Enter news text: Operation Sindoor was successful
```

### Help Command
```
Enter news text: help
```

### Quit
```
Enter news text: quit
```

## 🎯 Sample Output

```
=== Verifying: Operation Sindoor was successful ===

🔍 Searching multiple news sources...
🌐 Searching Google News...
   Found 10 results
📊 Searching Reuters...
   Found 0 results

📊 Total unique results: 10

✅ VERIFICATION RESULT: REAL NEWS
   Found 10 credible sources
   Average credibility score: 67.3/100

🏆 Top 5 most credible sources:
   1. 🟢 Operation Bunyan-al-Marsoos is a clear symbol...
      Source: Associated Press of Pakistan (Credibility: 97/100)
      API: Google News

✅ ASSESSMENT: CREDIBLE - News verified by multiple sources
```

## ⚙️ Configuration

Edit `config.py` to customize:
- API keys
- Credibility weights
- Search timeouts
- Rate limiting
- User agents

## 🔒 Rate Limiting

- **NewsAPI**: 100 requests/day (free tier)
- **Google News**: 60 requests/minute
- **Reuters**: 30 requests/minute

## 🛠️ Customization

### Adding New News Sources
1. Create a new search function in `predict.py`
2. Add the source to the credibility scores
3. Integrate it into `comprehensive_verification()`

### Modifying Credibility Scores
Edit the `CREDIBILITY_SCORES` dictionary in `predict.py` to adjust scores for different sources.

## 🚨 Troubleshooting

### Common Issues

1. **"NewsAPI error"**: Check your API key and rate limits
2. **"No results found"**: Try different search terms or check internet connection
3. **Slow performance**: Some APIs may be slow; this is normal

### Performance Tips

- Use specific, relevant search terms
- Avoid very long text inputs
- Check your internet connection speed

## 🔮 Future Enhancements

- [ ] Fact-checking site integration (Snopes, PolitiFact)
- [ ] Image verification capabilities
- [ ] Social media source verification
- [ ] Machine learning-based credibility assessment
- [ ] Web interface and API endpoints
- [ ] Mobile app development

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section
2. Review the configuration
3. Open an issue on GitHub

---

**Remember**: This tool is designed to help verify news, but always use critical thinking and multiple sources for important decisions!
