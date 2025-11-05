"""
🎭 USER AGENT MANAGER - Realistic User-Agent Rotation System
Manages a pool of realistic User-Agent strings with rotation and platform consistency.
Supports loading from external files and automatic updates.
"""

import random
import logging
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class UserAgentManager:
    """
    🔄 User-Agent Management System
    Features:
    - Realistic browser User-Agent strings
    - Platform-consistent headers
    - Weighted selection based on popularity
    - External file support
    - Anti-detection patterns
    """

    def __init__(self, ua_file: str = 'user_agents.txt'):
        self.ua_file = Path(ua_file)
        self.user_agents = self._get_default_user_agents()
        self.last_used_index = 0

    def _get_default_user_agents(self) -> List[Dict[str, str]]:
        """Get default realistic User-Agent strings with platform headers"""
        return [
            # Windows Chrome (most common)
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"Windows"',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 35
            },
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'sec_ch_ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"Windows"',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 30
            },

            # Windows Edge
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"Windows"',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 15
            },

            # macOS Safari
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 12
            },
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"macOS"',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 10
            },

            # Linux Chrome
            {
                'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"Linux"',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 8
            },

            # Firefox variants
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.5',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 7
            },
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.5',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 5
            },

            # Mobile variants (lower weight for desktop scraping)
            {
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 3
            },
            {
                'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec_ch_ua_mobile': '?1',
                'sec_ch_ua_platform': '"Android"',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'weight': 2
            }
        ]

    def load_external_user_agents(self) -> List[Dict[str, str]]:
        """Load User-Agent strings from external file"""
        external_uas = []

        if not self.ua_file.exists():
            logger.info(f"User-Agent file {self.ua_file} not found, using defaults")
            return external_uas

        try:
            with open(self.ua_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Simple format: just User-Agent string
                    # Advanced format: JSON with full headers
                    try:
                        if line.startswith('{'):
                            import json
                            ua_data = json.loads(line)
                        else:
                            ua_data = {
                                'user_agent': line,
                                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                'accept_language': 'en-US,en;q=0.9',
                                'accept_encoding': 'gzip, deflate, br',
                                'weight': 1
                            }

                        external_uas.append(ua_data)

                    except Exception as e:
                        logger.error(f"Error parsing UA line {line_num}: {e}")

            logger.info(f"Loaded {len(external_uas)} User-Agents from file")

        except Exception as e:
            logger.error(f"Error reading User-Agent file {self.ua_file}: {e}")

        return external_uas

    def initialize(self):
        """Initialize User-Agent manager"""
        # Load external UAs if available
        external_uas = self.load_external_user_agents()

        # Combine with defaults
        if external_uas:
            self.user_agents.extend(external_uas)

        logger.info(f"User-Agent manager initialized with {len(self.user_agents)} User-Agents")

    def get_random_user_agent(self) -> Dict[str, str]:
        """Get random User-Agent with weighted selection"""
        if not self.user_agents:
            # Fallback to basic UA
            return {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br'
            }

        # Weighted random selection
        weights = [ua.get('weight', 1) for ua in self.user_agents]
        selected_ua = random.choices(self.user_agents, weights=weights)[0]

        return selected_ua.copy()

    def get_next_user_agent(self) -> Dict[str, str]:
        """Get next User-Agent in round-robin fashion"""
        if not self.user_agents:
            return self.get_random_user_agent()

        ua = self.user_agents[self.last_used_index % len(self.user_agents)]
        self.last_used_index += 1

        return ua.copy()

    def get_headers_for_ua(self, ua_data: Dict[str, str]) -> Dict[str, str]:
        """Generate complete headers for User-Agent"""
        headers = {
            'User-Agent': ua_data['user_agent'],
            'Accept': ua_data.get('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            'Accept-Language': ua_data.get('accept_language', 'en-US,en;q=0.9'),
            'Accept-Encoding': ua_data.get('accept_encoding', 'gzip, deflate, br'),
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # Add Chrome-specific headers if present
        if 'sec_ch_ua' in ua_data:
            headers.update({
                'Sec-CH-UA': ua_data['sec_ch_ua'],
                'Sec-CH-UA-Mobile': ua_data.get('sec_ch_ua_mobile', '?0'),
                'Sec-CH-UA-Platform': ua_data.get('sec_ch_ua_platform', '"Windows"'),
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })

        return headers

    def get_random_headers(self) -> Dict[str, str]:
        """Get complete random headers with User-Agent"""
        ua_data = self.get_random_user_agent()
        return self.get_headers_for_ua(ua_data)

    def get_stats(self) -> Dict:
        """Get User-Agent manager statistics"""
        return {
            'total_user_agents': len(self.user_agents),
            'external_file_exists': self.ua_file.exists(),
            'last_used_index': self.last_used_index,
            'browsers': self._get_browser_distribution(),
            'platforms': self._get_platform_distribution(),
        }

    def _get_browser_distribution(self) -> Dict[str, int]:
        """Get browser distribution from User-Agents"""
        browsers = {}
        for ua in self.user_agents:
            ua_string = ua['user_agent']
            if 'Chrome' in ua_string and 'Edg' not in ua_string:
                browsers['Chrome'] = browsers.get('Chrome', 0) + 1
            elif 'Edg' in ua_string:
                browsers['Edge'] = browsers.get('Edge', 0) + 1
            elif 'Firefox' in ua_string:
                browsers['Firefox'] = browsers.get('Firefox', 0) + 1
            elif 'Safari' in ua_string and 'Chrome' not in ua_string:
                browsers['Safari'] = browsers.get('Safari', 0) + 1
            else:
                browsers['Other'] = browsers.get('Other', 0) + 1
        return browsers

    def _get_platform_distribution(self) -> Dict[str, int]:
        """Get platform distribution from User-Agents"""
        platforms = {}
        for ua in self.user_agents:
            ua_string = ua['user_agent']
            if 'Windows' in ua_string:
                platforms['Windows'] = platforms.get('Windows', 0) + 1
            elif 'Macintosh' in ua_string:
                platforms['macOS'] = platforms.get('macOS', 0) + 1
            elif 'Linux' in ua_string:
                platforms['Linux'] = platforms.get('Linux', 0) + 1
            elif 'iPhone' in ua_string:
                platforms['iOS'] = platforms.get('iOS', 0) + 1
            elif 'Android' in ua_string:
                platforms['Android'] = platforms.get('Android', 0) + 1
            else:
                platforms['Other'] = platforms.get('Other', 0) + 1
        return platforms

# Global User-Agent manager instance
ua_manager = UserAgentManager()