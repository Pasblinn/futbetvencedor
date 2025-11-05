# Scrapy settings for football_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'football_scraper'

SPIDER_MODULES = ['football_scraper.spiders']
NEWSPIDER_MODULE = 'football_scraper.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True  # Can be overridden with --ignore-robots

# Configure delays for requests (be respectful!)
DOWNLOAD_DELAY = 3  # 3 second delay
RANDOMIZE_DOWNLOAD_DELAY = 0.5  # 0.5 * to 1.5 * DOWNLOAD_DELAY
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telemetry sending (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'football_scraper.middlewares.FootballSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'football_scraper.middlewares.ProxyMiddleware': 350,
    'football_scraper.middlewares.UserAgentMiddleware': 400,
    'football_scraper.middlewares.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,  # Disable default
}

# Enable or disable extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
}

# Configure pipelines
ITEM_PIPELINES = {
    'football_scraper.pipelines.DataCleaningPipeline': 300,
    'football_scraper.pipelines.MetadataPipeline': 400,
    'football_scraper.pipelines.ExportPipeline': 500,
}

# Enable autothrottling
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Retry configuration
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# Cache configuration (for development)
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'

# Custom settings
PROXY_LIST_PATH = 'proxies.txt'
USER_AGENTS_LIST_PATH = 'user_agents.txt'
OUTPUT_DIR = 'scraped_data'
EXPORT_FORMATS = ['jsonl', 'parquet', 'csv']

# Compliance and ethics
DOWNLOAD_TIMEOUT = 180
DOWNLOAD_MAXSIZE = 1073741824  # 1GB
DOWNLOAD_WARNSIZE = 33554432   # 32MB

# Anti-detection settings
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = None  # Use webdriver-manager
SELENIUM_DRIVER_ARGUMENTS = [
    '--headless',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--disable-web-security',
    '--allow-running-insecure-content',
    '--disable-extensions',
    '--disable-plugins',
    '--disable-images',
    '--disable-javascript',  # Can be enabled per request
]