"""
🕷️ SCRAPY MIDDLEWARES - Advanced Anti-Bot Protection Middlewares
Custom middlewares for proxy rotation, User-Agent management, and retry logic.
Integrates with proxy_manager, ua_manager, and retry_backoff systems.
"""

import random
import time
import logging
from typing import Optional, Dict, Any
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.utils.response import response_status_message
from scrapy.spiders import Spider
from twisted.internet.error import TimeoutError, DNSLookupError, ConnectionRefusedError

from .proxy_manager import proxy_manager
from .ua_manager import ua_manager
from .retry_backoff import retry_manager, RetryReason

logger = logging.getLogger(__name__)

class FootballSpiderMiddleware:
    """
    🏈 Football Spider Middleware
    Handles spider-level functionality
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info(f'Spider opened: {spider.name}')

class ProxyMiddleware(HttpProxyMiddleware):
    """
    🛡️ Advanced Proxy Middleware
    Intelligent proxy rotation with health checking and fallback
    """

    def __init__(self, crawler_stats=None):
        self.crawler_stats = crawler_stats
        self.proxy_initialized = False

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.stats)

    async def _initialize_proxy_manager(self):
        """Initialize proxy manager if not already done"""
        if not self.proxy_initialized:
            await proxy_manager.initialize()
            self.proxy_initialized = True

    def process_request(self, request, spider):
        """Process request with proxy rotation"""
        # Skip proxy for certain URLs if needed
        if hasattr(spider, 'no_proxy_urls'):
            for url_pattern in spider.no_proxy_urls:
                if url_pattern in request.url:
                    return None

        # Initialize proxy manager asynchronously if needed
        if not self.proxy_initialized:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._initialize_proxy_manager())
            except:
                pass

        # Get proxy for request
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            proxy = loop.run_until_complete(proxy_manager.get_proxy())

            if proxy:
                request.meta['proxy'] = proxy.formatted_proxy
                request.meta['proxy_info'] = proxy
                request.meta['download_timeout'] = 30

                # Add proxy authentication if needed
                if proxy.username and proxy.password:
                    import base64
                    credentials = base64.b64encode(
                        f"{proxy.username}:{proxy.password}".encode()
                    ).decode()
                    request.headers['Proxy-Authorization'] = f'Basic {credentials}'

                logger.debug(f"Using proxy {proxy.url} for {request.url}")
            else:
                logger.warning(f"No proxy available for {request.url}")

        except Exception as e:
            logger.error(f"Error setting proxy: {e}")

        return None

    def process_response(self, request, response, spider):
        """Process response and update proxy stats"""
        if 'proxy_info' in request.meta:
            proxy = request.meta['proxy_info']
            response_time = time.time() - request.meta.get('download_slot', time.time())

            if response.status == 200:
                proxy_manager.report_success(proxy, response_time)
            else:
                proxy_manager.report_failure(proxy, response.status)

        return response

    def process_exception(self, request, exception, spider):
        """Handle proxy-related exceptions"""
        if 'proxy_info' in request.meta:
            proxy = request.meta['proxy_info']
            proxy_manager.report_failure(proxy)

            # Mark proxy as unhealthy for certain exceptions
            if isinstance(exception, (TimeoutError, ConnectionRefusedError)):
                proxy.consecutive_failures += 1

        return None

class UserAgentMiddleware:
    """
    🎭 User-Agent Rotation Middleware
    Rotates User-Agents and maintains consistent headers
    """

    def __init__(self):
        self.ua_initialized = False

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def _initialize_ua_manager(self):
        """Initialize UA manager if needed"""
        if not self.ua_initialized:
            ua_manager.initialize()
            self.ua_initialized = True

    def process_request(self, request, spider):
        """Set User-Agent and related headers"""
        if not self.ua_initialized:
            self._initialize_ua_manager()

        # Get random headers
        headers = ua_manager.get_random_headers()

        # Update request headers
        for header_name, header_value in headers.items():
            request.headers[header_name] = header_value

        # Store UA info in meta for stats
        request.meta['user_agent_info'] = headers

        return None

class RetryMiddleware(RetryMiddleware):
    """
    🔄 Advanced Retry Middleware
    Implements exponential backoff with jitter and circuit breaker
    """

    EXCEPTIONS_TO_RETRY = (
        DNSLookupError,
        ConnectionRefusedError,
        TimeoutError,
    )

    def __init__(self, settings):
        super().__init__(settings)
        self.retry_initialized = False

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def _initialize_retry_manager(self):
        """Initialize retry manager with settings"""
        if not self.retry_initialized:
            retry_manager.configure_backoff(
                initial_delay=1.0,
                max_delay=60.0,
                multiplier=2.0,
                jitter_type="full",
                max_attempts=3
            )
            retry_manager.configure_circuit_breaker(
                failure_threshold=5,
                timeout_duration=60,
                success_threshold=2
            )
            self.retry_initialized = True

    def process_response(self, request, response, spider):
        """Process response and determine if retry is needed"""
        if not self.retry_initialized:
            self._initialize_retry_manager()

        if request.meta.get('dont_retry', False):
            return response

        retries = request.meta.get('retry_times', 0) + 1
        retry_times = self.max_retry_times

        if retries <= retry_times:
            should_retry = retry_manager.should_retry(
                retries,
                response.status,
                None
            )

            if should_retry:
                reason = f"status_{response.status}"
                return self._retry(request, reason, spider) or response

        return response

    def process_exception(self, request, exception, spider):
        """Process exception and determine if retry is needed"""
        if not self.retry_initialized:
            self._initialize_retry_manager()

        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
            retries = request.meta.get('retry_times', 0) + 1

            should_retry = retry_manager.should_retry(
                retries,
                500,  # Treat exceptions as 500 errors
                exception
            )

            if should_retry:
                reason = f"exception_{exception.__class__.__name__}"
                return self._retry(request, reason, spider)

    def _retry(self, request, reason, spider):
        """Retry request with backoff delay"""
        retries = request.meta.get('retry_times', 0) + 1
        retry_times = self.max_retry_times

        if retries <= retry_times:
            # Calculate delay
            delay = retry_manager.calculate_delay(retries, 500)

            logger.info(f"Retrying {request.url} (attempt {retries}/{retry_times}), "
                       f"delay: {delay:.2f}s, reason: {reason}")

            # Add delay to request meta
            request.meta['download_delay'] = delay
            request.meta['retry_times'] = retries

            # Change proxy if available for proxy-related failures
            if 'proxy' in reason or 'timeout' in reason.lower():
                if 'proxy_info' in request.meta:
                    try:
                        import asyncio
                        loop = asyncio.get_event_loop()
                        new_proxy = loop.run_until_complete(proxy_manager.get_proxy())

                        if new_proxy:
                            request.meta['proxy'] = new_proxy.formatted_proxy
                            request.meta['proxy_info'] = new_proxy
                            logger.debug(f"Switching to new proxy {new_proxy.url} for retry")
                    except Exception as e:
                        logger.warning(f"Failed to get new proxy for retry: {e}")

            # Get new User-Agent for retry
            headers = ua_manager.get_random_headers()
            for header_name, header_value in headers.items():
                request.headers[header_name] = header_value

            return request.copy()
        else:
            logger.error(f"Gave up retrying {request.url} (tried {retries} times): {reason}")

class JavaScriptMiddleware:
    """
    🌐 JavaScript Rendering Middleware
    Uses Selenium for JavaScript-heavy sites as fallback
    """

    def __init__(self):
        self.selenium_enabled = False
        self.driver = None

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        if not settings.getbool('SELENIUM_ENABLED', False):
            raise NotConfigured('Selenium middleware not enabled')

        return cls()

    def _get_driver(self):
        """Get Selenium WebDriver instance"""
        if self.driver is None:
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from webdriver_manager.chrome import ChromeDriverManager

                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-web-security')
                chrome_options.add_argument('--allow-running-insecure-content')

                self.driver = webdriver.Chrome(
                    ChromeDriverManager().install(),
                    options=chrome_options
                )
                self.selenium_enabled = True

            except Exception as e:
                logger.error(f"Failed to initialize Selenium driver: {e}")
                self.selenium_enabled = False

        return self.driver

    def process_request(self, request, spider):
        """Process request with Selenium if needed"""
        # Only use Selenium for specific sites or when explicitly requested
        use_selenium = (
            request.meta.get('use_selenium', False) or
            any(site in request.url for site in ['oddspedia.com', 'fbref.com'])
        )

        if use_selenium and self.selenium_enabled:
            driver = self._get_driver()
            if driver:
                try:
                    # Set headers via Selenium (limited capability)
                    if 'user_agent_info' in request.meta:
                        user_agent = request.meta['user_agent_info']['User-Agent']
                        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                            'userAgent': user_agent
                        })

                    # Load page
                    driver.get(request.url)

                    # Wait for page to load
                    import time
                    time.sleep(3)

                    # Get page source
                    html = driver.page_source

                    # Create response
                    response = HtmlResponse(
                        url=request.url,
                        body=html.encode('utf-8'),
                        encoding='utf-8',
                        request=request
                    )

                    logger.info(f"Rendered {request.url} with Selenium")
                    return response

                except Exception as e:
                    logger.error(f"Selenium rendering failed for {request.url}: {e}")

        return None

    def process_response(self, request, response, spider):
        """Check if response needs JavaScript rendering"""
        # If response indicates JavaScript is needed, retry with Selenium
        if (response.status == 200 and
            not request.meta.get('use_selenium', False) and
            self._needs_javascript(response)):

            logger.info(f"Response from {request.url} appears to need JavaScript, retrying with Selenium")

            # Create new request with Selenium
            new_request = request.copy()
            new_request.meta['use_selenium'] = True

            return new_request

        return response

    def _needs_javascript(self, response) -> bool:
        """Detect if response needs JavaScript rendering"""
        body_text = response.text.lower()

        # Common indicators that JavaScript is needed
        js_indicators = [
            'please enable javascript',
            'javascript is required',
            'loading...',
            'cloudflare',
            'please wait while we verify',
            'just a moment',
            'browser check',
            'enable cookies',
        ]

        return any(indicator in body_text for indicator in js_indicators)

    def spider_closed(self, spider):
        """Clean up Selenium driver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing Selenium driver: {e}")

class RobotsTxtMiddleware:
    """
    🤖 Enhanced Robots.txt Middleware
    Respects robots.txt by default but allows override
    """

    def __init__(self, crawler):
        self.crawler = crawler
        self.ignore_robots = crawler.settings.getbool('IGNORE_ROBOTS_TXT', False)

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('ROBOTSTXT_OBEY', True):
            raise NotConfigured('Robots.txt middleware disabled')
        return cls(crawler)

    def process_request(self, request, spider):
        """Check robots.txt compliance"""
        if self.ignore_robots:
            logger.warning(f"IGNORING robots.txt for {request.url} - USE AT YOUR OWN RISK!")
            return None

        # Let default Scrapy robots.txt middleware handle this
        return None