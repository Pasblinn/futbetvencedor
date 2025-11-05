# 🕷️ Football Analytics Scraper System

> **Advanced multi-strategy web scraping system for football data with ML integration**

## 📋 Overview

The Football Analytics Scraper is a robust, production-ready web scraping system designed specifically for gathering football/soccer data from various sources. It implements multiple fallback strategies, anti-bot protection, and seamless ML pipeline integration.

### ✨ Key Features

- **🔄 Multi-Strategy Fetching**: Automatic fallback through Scrapy → requests → requests_html → Selenium
- **🛡️ Anti-Bot Protection**: Proxy rotation, User-Agent rotation, rate limiting, CAPTCHA handling
- **⚡ High Performance**: Concurrent requests with intelligent throttling
- **📊 ML Integration**: Direct pipeline to ML feature engineering and training
- **🎯 Site-Specific Configs**: Optimized strategies for each target site
- **📈 Monitoring**: Comprehensive logging and success rate tracking

---

## 🏗️ Architecture

```
📦 football_scraper/
├── 🕷️ spiders/
│   └── football_spider.py     # Main spider with multi-strategy support
├── 🔧 Core Modules
│   ├── fetcher.py             # Multi-strategy fetching engine
│   ├── proxy_manager.py       # Proxy rotation and health checking
│   ├── ua_manager.py          # User-Agent rotation
│   ├── retry_backoff.py       # Exponential backoff with jitter
│   ├── middlewares.py         # Anti-bot middlewares
│   └── pipelines.py           # Data processing and export
├── ⚙️ Configuration
│   ├── settings.py            # Scrapy settings with anti-bot measures
│   ├── proxies.txt            # Proxy configuration
│   └── user_agents.txt        # User-Agent list
└── 📊 ML Integration
    ├── ingest.py              # Raw data → ML features pipeline
    └── preprocess.py          # Advanced feature engineering
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to backend directory
cd football-analytics/backend

# Install dependencies
pip install -r requirements.txt

# Install additional ML dependencies
pip install pandas pyarrow scikit-learn
```

### 2. Basic Usage

```bash
# Single URL scraping
scrapy crawl football_spider -a url="https://fbref.com/en/comps/24/Serie-A-Stats"

# Multiple URLs
scrapy crawl football_spider -a url="https://fbref.com/en/comps/24/Serie-A-Stats,https://en.wikipedia.org/wiki/2024_Campeonato_Brasileiro_Série_A"

# Competition-based scraping
scrapy crawl football_spider -a competition="brasileirao" -a season="2024"

# With output format
scrapy crawl football_spider -a url="https://fbref.com/en/comps/24/Serie-A-Stats" -s FEED_FORMAT=jsonlines -s FEED_URI=output.jsonl
```

### 3. Run Sample Tests

```bash
# Run comprehensive sample tests
python run_sample.py

# Check output
ls -la scraped_data/
```

---

## ⚙️ Configuration

### Proxy Configuration (`proxies.txt`)

```txt
# HTTP proxies
http://proxy1.example.com:8080
http://user:pass@proxy2.example.com:3128

# SOCKS5 proxies
socks5://proxy3.example.com:1080

# Free proxies (use with caution)
http://103.149.162.194:80
```

### Site-Specific Configurations

The spider automatically adapts to different sites:

```python
SITE_CONFIGS = {
    'oddspedia.com': {
        'strategy': ['selenium', 'requests_html'],
        'wait_time': 5,
        'use_proxy': True,
        'delay': 3
    },
    'fbref.com': {
        'strategy': ['requests_pandas', 'scrapy'],
        'delay': 3,
        'headers_extra': {'Referer': 'https://google.com'}
    },
    'soccerway.com': {
        'strategy': ['requests_html', 'selenium'],
        'wait_time': 4,
        'use_proxy': True,
        'delay': 4
    }
}
```

---

## 🎯 Supported Sites & Strategies

| Site | Primary Strategy | Fallback | Success Rate | Notes |
|------|------------------|----------|--------------|-------|
| **FBref.com** | requests + pandas | scrapy | ~85% | Statistical tables |
| **Oddspedia.com** | selenium | requests_html | ~70% | JS-heavy, requires browser |
| **Soccerway.com** | requests_html | selenium | ~75% | Dynamic content |
| **RSSSF.com** | requests + pandas | scrapy | ~90% | Simple HTML tables |
| **Wikipedia** | scrapy | requests | ~95% | Standard HTML tables |

### Strategy Details

1. **📊 Scrapy (Primary)**: Fast, efficient for static HTML
2. **🐼 requests + pandas**: Excellent for HTML tables
3. **🎭 requests_html**: Handles basic JavaScript rendering
4. **🤖 Selenium**: Full browser simulation for complex sites

---

## 📊 ML Integration Pipeline

### Step 1: Data Scraping
```bash
# Scrape data
scrapy crawl football_spider -a competition="brasileirao" -a season="2024"
```

### Step 2: ML Data Ingestion
```bash
# Convert scraped data to ML features
python ingest.py --input scraped_data --output ml_ready

# Output files:
# - ml_ready/features.parquet (ML-ready features)
# - ml_ready/labels.parquet (target variables)
# - ml_ready/metadata.json (dataset metadata)
```

### Step 3: Feature Engineering
```python
from preprocess import FootballFeatureEngineer

engineer = FootballFeatureEngineer()
features_df = engineer.engineer_features(raw_data)
```

### ML-Ready Output Schema

```json
{
  "id": "uuid",
  "team": "Flamengo",
  "match_date": "2024-08-01",
  "home": true,
  "goals_for": 2,
  "goals_against": 1,
  "goals_for_avg": 1.6,
  "win_rate": 0.6,
  "xg": 1.7,
  "elo_rating": 1650,
  "form_last_5": "WWDWL",
  "h2h_win_rate": 0.4,
  "features": {...}
}
```

---

## 🛡️ Anti-Bot Protection

### Built-in Protection Measures

1. **🔄 Proxy Rotation**: Automatic proxy switching with health checks
2. **🎭 User-Agent Rotation**: Realistic browser headers
3. **⏱️ Rate Limiting**: Intelligent delays and throttling
4. **🔄 Retry Logic**: Exponential backoff with jitter
5. **🍪 Cookie Handling**: Session management
6. **🛡️ CAPTCHA Handling**: Selenium fallback for protected sites

### Response Handling

- **403 Forbidden**: Switch proxy + User-Agent → retry with requests_html → Selenium
- **429 Too Many Requests**: Exponential backoff → proxy rotation → circuit breaker
- **5xx Server Errors**: Limited retries → proxy switch → alternative strategy

---

## 📈 Monitoring & Logging

### Log Levels
```python
# Configure logging level
import logging
logging.basicConfig(level=logging.INFO)

# Available levels:
# DEBUG: Detailed request/response info
# INFO: General progress and statistics
# WARNING: Retries and fallback strategies
# ERROR: Failed requests and critical issues
```

### Success Metrics
The system tracks:
- ✅ Requests succeeded/failed per site
- ⏱️ Average response time per strategy
- 🔄 Strategy usage distribution
- 🎯 Data extraction success rate

---

## 🔧 Advanced Usage

### Custom Site Configuration

```python
custom_config = {
    'newsite.com': {
        'strategy': ['requests_html', 'selenium'],
        'wait_time': 6,
        'use_proxy': True,
        'table_selectors': ['.custom-table', '.data-grid'],
        'delay': 5,
        'headers_extra': {'X-API-Key': 'your-key'}
    }
}
```

### Custom Feature Engineering

```python
from preprocess import FootballFeatureEngineer

config = {
    'form_windows': [3, 7, 14],
    'rolling_windows': [5, 10, 20],
    'elo_k_factor': 40,
    'home_advantage': 0.15
}

engineer = FootballFeatureEngineer(config)
features = engineer.engineer_features(data)
```

### Batch Processing

```python
import subprocess

urls = [
    "https://fbref.com/en/comps/24/Serie-A-Stats",
    "https://fbref.com/en/comps/9/Premier-League-Stats",
    "https://fbref.com/en/comps/12/La-Liga-Stats"
]

for i, url in enumerate(urls):
    subprocess.run([
        'scrapy', 'crawl', 'football_spider',
        '-a', f'url={url}',
        '-s', f'FEED_URI=batch_output_{i}.jsonl'
    ])
```

---

## 🚨 Legal & Ethical Guidelines

### ⚖️ Legal Considerations
- **Always check `robots.txt`** before scraping (use `--ignore-robots` only when legally justified)
- **Respect rate limits** to avoid overloading target servers
- **Commercial use** may require explicit permission from site owners
- **Data protection laws** (GDPR, CCPA) may apply to scraped personal data

### 🤝 Best Practices
1. **Be respectful**: Use reasonable delays between requests
2. **Identify yourself**: Use descriptive User-Agent strings
3. **Handle errors gracefully**: Don't retry aggressively on permanent failures
4. **Cache data**: Avoid re-scraping the same content unnecessarily
5. **Monitor impact**: Watch for signs that you're affecting site performance

### 🔒 Security Notes
- **Never commit credentials** to version control
- **Use HTTPS proxies** when possible
- **Rotate credentials regularly** for paid proxy services
- **Monitor for IP blocking** and have mitigation strategies

---

## 🐛 Troubleshooting

### Common Issues

#### 1. All Strategies Failing (403/429 Errors)
```bash
# Solutions:
# - Add more diverse proxies to proxies.txt
# - Increase delays in SITE_CONFIGS
# - Check if site has new anti-bot measures
# - Verify User-Agent strings are current
```

#### 2. No Data Extracted
```bash
# Check table selectors:
scrapy shell "https://example.com"
response.css('table').getall()

# Test parsing manually:
import pandas as pd
pd.read_html(response.text)
```

#### 3. Selenium Driver Issues
```bash
# Update Chrome driver:
pip install --upgrade selenium webdriver-manager

# Check Chrome version compatibility:
google-chrome --version
```

#### 4. Proxy Connection Failures
```bash
# Test proxy manually:
curl --proxy http://proxy:port http://httpbin.org/ip

# Check proxy health:
python -c "from football_scraper.proxy_manager import proxy_manager; print(proxy_manager.get_healthy_proxies())"
```

### Performance Optimization

```python
# Scrapy settings for better performance:
CONCURRENT_REQUESTS = 2  # Conservative for anti-bot
DOWNLOAD_DELAY = 3
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# For faster but riskier scraping:
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_ENABLED = False
```

---

## 📦 Dependencies

```txt
# Core scraping
scrapy>=2.8.0
requests>=2.31.0
requests-html>=0.10.0
selenium>=4.15.0
webdriver-manager>=4.0.0

# Data processing
pandas>=2.0.0
pyarrow>=12.0.0
beautifulsoup4>=4.12.0

# ML integration
scikit-learn>=1.3.0
numpy>=1.24.0

# Utilities
fake-useragent>=1.4.0
furl>=2.1.3
aiohttp>=3.8.0
```

---

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone <repository>
cd football-analytics/backend

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Run linting
flake8 football_scraper/
```

### Adding New Sites
1. Add site configuration to `SITE_CONFIGS` in `football_spider.py`
2. Add field mappings in `ingest.py`
3. Test with sample URLs
4. Update documentation

### Reporting Issues
Please include:
- Target URL that failed
- Error messages from logs
- Scrapy version and Python version
- Steps to reproduce

---

## 📊 Example Output

### Scraped Data (JSONL)
```json
{
  "source_url": "https://fbref.com/en/comps/24/Serie-A-Stats",
  "source_site": "fbref.com",
  "competition": "brasileirao",
  "season": "2024",
  "table_name": "league_table",
  "data": {...},
  "scraped_at": "2024-01-26T15:30:00",
  "strategy": "requests_pandas",
  "response_time_ms": 1250
}
```

### ML Features (Parquet)
| team | match_date | goals_for_avg | win_rate | elo_rating | form_last_5 |
|------|------------|---------------|----------|------------|--------------|
| Flamengo | 2024-08-01 | 1.8 | 0.65 | 1680 | WWDWL |
| Palmeiras | 2024-08-01 | 1.6 | 0.60 | 1650 | WDWWL |

---

## 📞 Support

For issues and questions:
- 📖 Check this README first
- 🐛 Search existing issues on GitHub
- 💬 Create new issue with detailed description
- 📧 Contact maintainers for urgent matters

---

**⚠️ Important**: This tool is for educational and research purposes. Always respect website terms of service and applicable laws when scraping data.