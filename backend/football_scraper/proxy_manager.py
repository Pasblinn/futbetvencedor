"""
🛡️ PROXY MANAGER - Advanced Proxy Management System
Manages proxy pools with health checking, rotation, and fallback strategies.
Supports HTTP/HTTPS and SOCKS5 proxies with authentication.
"""

import asyncio
import aiohttp
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union
from urllib.parse import urlparse
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ProxyInfo:
    """Information about a proxy server"""
    url: str
    proxy_type: str  # 'http', 'https', 'socks5'
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    is_healthy: bool = True
    last_used: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    avg_response_time: float = 0.0
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    weight: float = 1.0
    blocked_until: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    @property
    def formatted_proxy(self) -> str:
        """Get proxy in requests format"""
        if self.username and self.password:
            parsed = urlparse(self.url)
            return f"{parsed.scheme}://{self.username}:{self.password}@{parsed.netloc}"
        return self.url

    def is_blocked(self) -> bool:
        """Check if proxy is currently blocked"""
        if self.blocked_until is None:
            return False
        return datetime.now() < self.blocked_until

    def block_temporarily(self, minutes: int = 10):
        """Block proxy temporarily"""
        self.blocked_until = datetime.now() + timedelta(minutes=minutes)
        logger.warning(f"Proxy {self.url} blocked for {minutes} minutes")

class ProxyManager:
    """
    🔄 Advanced Proxy Management System
    Features:
    - Health checking with periodic validation
    - Automatic rotation and fallback
    - Geographic proxy selection
    - Performance-based weighting
    - Temporary blocking for rate-limited proxies
    """

    def __init__(self, proxy_file: str = 'proxies.txt', api_endpoint: str = None):
        self.proxy_file = Path(proxy_file)
        self.api_endpoint = api_endpoint
        self.proxies: List[ProxyInfo] = []
        self.healthy_proxies: List[ProxyInfo] = []
        self.unhealthy_proxies: Set[str] = set()
        self.current_index = 0
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = datetime.min
        self.max_consecutive_failures = 5
        self.health_check_urls = [
            'http://httpbin.org/ip',
            'https://httpbin.org/ip',
            'http://ip-api.com/json',
        ]

    def load_proxies_from_file(self) -> List[ProxyInfo]:
        """Load proxies from file"""
        proxies = []
        if not self.proxy_file.exists():
            logger.warning(f"Proxy file {self.proxy_file} not found")
            return proxies

        try:
            with open(self.proxy_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    try:
                        proxy_info = self._parse_proxy_line(line)
                        if proxy_info:
                            proxies.append(proxy_info)
                    except Exception as e:
                        logger.error(f"Error parsing line {line_num} in {self.proxy_file}: {e}")

        except Exception as e:
            logger.error(f"Error reading proxy file {self.proxy_file}: {e}")

        logger.info(f"Loaded {len(proxies)} proxies from file")
        return proxies

    def _parse_proxy_line(self, line: str) -> Optional[ProxyInfo]:
        """Parse a proxy line in various formats"""
        # Format examples:
        # http://proxy:port
        # http://user:pass@proxy:port
        # proxy:port:user:pass
        # proxy:port
        # socks5://proxy:port

        parts = line.split(':')

        if line.startswith(('http://', 'https://', 'socks5://')):
            # URL format
            parsed = urlparse(line)
            return ProxyInfo(
                url=f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                proxy_type=parsed.scheme,
                username=parsed.username,
                password=parsed.password
            )
        elif len(parts) == 2:
            # Simple proxy:port
            host, port = parts
            return ProxyInfo(
                url=f"http://{host}:{port}",
                proxy_type='http'
            )
        elif len(parts) == 4:
            # proxy:port:user:pass
            host, port, username, password = parts
            return ProxyInfo(
                url=f"http://{host}:{port}",
                proxy_type='http',
                username=username,
                password=password
            )

        logger.warning(f"Could not parse proxy line: {line}")
        return None

    async def load_proxies_from_api(self) -> List[ProxyInfo]:
        """Load proxies from API endpoint"""
        if not self.api_endpoint:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_endpoint, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        proxies = []

                        # Assume API returns list of proxy objects
                        for proxy_data in data.get('proxies', []):
                            proxy_info = ProxyInfo(
                                url=proxy_data['url'],
                                proxy_type=proxy_data.get('type', 'http'),
                                username=proxy_data.get('username'),
                                password=proxy_data.get('password'),
                                country=proxy_data.get('country'),
                                region=proxy_data.get('region'),
                                weight=proxy_data.get('weight', 1.0)
                            )
                            proxies.append(proxy_info)

                        logger.info(f"Loaded {len(proxies)} proxies from API")
                        return proxies

        except Exception as e:
            logger.error(f"Error loading proxies from API: {e}")

        return []

    async def initialize(self):
        """Initialize proxy manager"""
        # Load from file
        file_proxies = self.load_proxies_from_file()

        # Load from API
        api_proxies = await self.load_proxies_from_api()

        # Combine all proxies
        self.proxies = file_proxies + api_proxies

        if not self.proxies:
            logger.warning("No proxies loaded! Scraping will use direct connection")
            return

        # Initial health check
        await self.health_check_all()

        logger.info(f"Proxy manager initialized with {len(self.healthy_proxies)} healthy proxies")

    async def health_check_proxy(self, proxy: ProxyInfo) -> bool:
        """Check if a single proxy is healthy"""
        test_url = random.choice(self.health_check_urls)

        try:
            start_time = time.time()

            proxy_dict = {
                'http': proxy.formatted_proxy,
                'https': proxy.formatted_proxy
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy.formatted_proxy,
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                ) as response:

                    response_time = time.time() - start_time

                    if response.status == 200:
                        proxy.success_count += 1
                        proxy.consecutive_failures = 0
                        proxy.avg_response_time = (proxy.avg_response_time + response_time) / 2
                        proxy.last_check = datetime.now()
                        proxy.is_healthy = True
                        return True

        except Exception as e:
            logger.debug(f"Proxy health check failed for {proxy.url}: {e}")

        proxy.failure_count += 1
        proxy.consecutive_failures += 1
        proxy.last_check = datetime.now()

        if proxy.consecutive_failures >= self.max_consecutive_failures:
            proxy.is_healthy = False
            logger.warning(f"Proxy {proxy.url} marked as unhealthy after {proxy.consecutive_failures} failures")

        return False

    async def health_check_all(self):
        """Health check all proxies"""
        logger.info("Starting proxy health check...")

        tasks = []
        for proxy in self.proxies:
            if not proxy.is_blocked():
                tasks.append(self.health_check_proxy(proxy))
            else:
                logger.debug(f"Skipping blocked proxy {proxy.url}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Update healthy proxies list
        self.healthy_proxies = [p for p in self.proxies if p.is_healthy and not p.is_blocked()]

        self.last_health_check = datetime.now()

        logger.info(f"Health check complete. {len(self.healthy_proxies)} healthy proxies")

    async def get_proxy(self, region: str = None) -> Optional[ProxyInfo]:
        """Get next available proxy with optional region filter"""
        # Check if health check is needed
        if datetime.now() - self.last_health_check > timedelta(seconds=self.health_check_interval):
            await self.health_check_all()

        available_proxies = self.healthy_proxies.copy()

        # Filter by region if specified
        if region:
            available_proxies = [p for p in available_proxies if p.region == region or p.country == region]

        if not available_proxies:
            logger.warning(f"No healthy proxies available for region: {region}" if region else "No healthy proxies available")
            return None

        # Weighted random selection based on success rate and response time
        weights = []
        for proxy in available_proxies:
            # Higher success rate and lower response time = higher weight
            weight = (proxy.success_rate * proxy.weight) / max(proxy.avg_response_time, 0.1)
            weights.append(weight)

        if not weights or all(w == 0 for w in weights):
            # Fallback to round-robin
            proxy = available_proxies[self.current_index % len(available_proxies)]
            self.current_index += 1
        else:
            # Weighted selection
            proxy = random.choices(available_proxies, weights=weights)[0]

        proxy.last_used = datetime.now()
        return proxy

    def report_success(self, proxy: ProxyInfo, response_time: float):
        """Report successful request with proxy"""
        proxy.success_count += 1
        proxy.consecutive_failures = 0
        proxy.avg_response_time = (proxy.avg_response_time + response_time) / 2

        # Remove from unhealthy set if present
        if proxy.url in self.unhealthy_proxies:
            self.unhealthy_proxies.remove(proxy.url)
            proxy.is_healthy = True

    def report_failure(self, proxy: ProxyInfo, status_code: int = None):
        """Report failed request with proxy"""
        proxy.failure_count += 1
        proxy.consecutive_failures += 1

        # Handle specific status codes
        if status_code == 429:  # Too Many Requests
            proxy.block_temporarily(minutes=15)
        elif status_code == 403:  # Forbidden
            proxy.block_temporarily(minutes=30)
        elif proxy.consecutive_failures >= self.max_consecutive_failures:
            proxy.is_healthy = False
            self.unhealthy_proxies.add(proxy.url)
            logger.warning(f"Proxy {proxy.url} marked as unhealthy due to consecutive failures")

    def get_stats(self) -> Dict:
        """Get proxy manager statistics"""
        total_proxies = len(self.proxies)
        healthy_proxies = len(self.healthy_proxies)
        blocked_proxies = len([p for p in self.proxies if p.is_blocked()])

        total_requests = sum(p.success_count + p.failure_count for p in self.proxies)
        total_success = sum(p.success_count for p in self.proxies)

        return {
            'total_proxies': total_proxies,
            'healthy_proxies': healthy_proxies,
            'unhealthy_proxies': total_proxies - healthy_proxies,
            'blocked_proxies': blocked_proxies,
            'total_requests': total_requests,
            'success_rate': total_success / total_requests if total_requests > 0 else 0.0,
            'last_health_check': self.last_health_check.isoformat(),
            'regions': list(set(p.country for p in self.proxies if p.country)),
        }

    def get_proxy_sync(self, region: str = None) -> Optional[str]:
        """Synchronous version of get_proxy for use in Scrapy spiders"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Return None if we can't get proxy synchronously
                # In real usage, consider using a background task to update proxy list
                if self.healthy_proxies:
                    proxy = self.healthy_proxies[0]  # Simple selection
                    return f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}" if proxy.username else f"{proxy.protocol}://{proxy.host}:{proxy.port}"
                return None
            else:
                proxy_info = loop.run_until_complete(self.get_proxy(region))
                if proxy_info:
                    return f"{proxy_info.protocol}://{proxy_info.username}:{proxy_info.password}@{proxy_info.host}:{proxy_info.port}" if proxy_info.username else f"{proxy_info.protocol}://{proxy_info.host}:{proxy_info.port}"
                return None
        except RuntimeError:
            # No event loop, just return first healthy proxy
            if self.healthy_proxies:
                proxy = self.healthy_proxies[0]
                return f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}" if proxy.username else f"{proxy.protocol}://{proxy.host}:{proxy.port}"
            return None


# Global proxy manager instance
proxy_manager = ProxyManager()