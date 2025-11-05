import asyncio
import websockets
import json
import aiohttp
import logging
from typing import Dict, List, Set, Optional, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis
from app.core.config import settings
from app.models import Match, Odds, Team, MatchStatistics
from app.services.odds_service import OddsService
from app.services.football_data_service import FootballDataService
import numpy as np

logger = logging.getLogger(__name__)

class RealTimeMonitor:
    """Real-time monitoring system for matches, odds, and predictions"""

    def __init__(self):
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.active_matches: Dict[int, Dict] = {}
        self.odds_cache: Dict[str, Dict] = {}
        self.alert_thresholds = {
            'odds_movement': 0.1,  # 10% change
            'lineup_changes': True,
            'weather_changes': 0.3,
            'injury_updates': True,
            'sentiment_shift': 0.2
        }

        # Initialize services
        self.odds_service = OddsService()
        self.football_service = FootballDataService()

        # Redis for real-time data
        self.redis_client = None

        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'odds_change': [],
            'lineup_update': [],
            'match_event': [],
            'weather_update': [],
            'prediction_update': []
        }

    async def initialize(self):
        """Initialize the monitoring system"""
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(settings.REDIS_URL)

            # Start background monitoring tasks
            await self._start_monitoring_tasks()

            logger.info("Real-time monitoring system initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing real-time monitor: {e}")

    async def _start_monitoring_tasks(self):
        """Start all background monitoring tasks"""
        monitoring_configs = [
            ('odds_monitor', self._monitor_odds_changes, 30),  # Every 30 seconds
            ('lineup_monitor', self._monitor_lineup_changes, 300),  # Every 5 minutes
            ('weather_monitor', self._monitor_weather_updates, 600),  # Every 10 minutes
            ('match_events_monitor', self._monitor_live_matches, 15),  # Every 15 seconds
            ('prediction_validation', self._validate_predictions, 120),  # Every 2 minutes
            ('system_health', self._monitor_system_health, 60)  # Every minute
        ]

        for task_name, task_func, interval in monitoring_configs:
            task = asyncio.create_task(self._run_periodic_task(task_func, interval))
            self.monitoring_tasks[task_name] = task
            logger.info(f"Started monitoring task: {task_name}")

    async def _run_periodic_task(self, task_func: Callable, interval: int):
        """Run a task periodically"""
        while True:
            try:
                await task_func()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic task {task_func.__name__}: {e}")
                await asyncio.sleep(interval)

    async def _monitor_odds_changes(self):
        """Monitor odds changes across all active matches"""
        try:
            # Get today's matches
            today = datetime.now().strftime('%Y-%m-%d')
            engine = create_engine(settings.DATABASE_URL)
            SessionLocal = sessionmaker(bind=engine)

            with SessionLocal() as db:
                matches = db.query(Match).filter(
                    Match.match_date >= datetime.now(),
                    Match.match_date <= datetime.now() + timedelta(days=1),
                    Match.status.in_(['SCHEDULED', 'LIVE'])
                ).all()

                for match in matches:
                    await self._check_odds_for_match(match)

        except Exception as e:
            logger.error(f"Error monitoring odds changes: {e}")

    async def _check_odds_for_match(self, match: Match):
        """Check odds changes for a specific match"""
        try:
            if not match.external_id:
                return

            # Get current odds
            current_odds = await self.odds_service.get_match_odds(match.external_id)

            if not current_odds:
                return

            cache_key = f"odds:{match.external_id}"
            previous_odds = self.odds_cache.get(cache_key)

            if previous_odds:
                # Calculate odds movements
                movements = self._calculate_odds_movements(previous_odds, current_odds)

                # Check for significant movements
                significant_movements = [
                    movement for movement in movements
                    if abs(movement['percentage_change']) >= self.alert_thresholds['odds_movement'] * 100
                ]

                if significant_movements:
                    await self._trigger_odds_alert(match, significant_movements, current_odds)

            # Update cache
            self.odds_cache[cache_key] = current_odds

            # Store in Redis for real-time access
            if self.redis_client:
                await self.redis_client.setex(
                    f"live_odds:{match.id}",
                    300,  # 5 minutes TTL
                    json.dumps(current_odds, default=str)
                )

        except Exception as e:
            logger.error(f"Error checking odds for match {match.id}: {e}")

    def _calculate_odds_movements(self, previous_odds: Dict, current_odds: Dict) -> List[Dict]:
        """Calculate percentage changes in odds"""
        movements = []

        markets_to_check = ['home_win', 'draw', 'away_win', 'over_2_5', 'under_2_5', 'btts_yes', 'btts_no']

        for bookmaker in current_odds.get('bookmakers', []):
            bookmaker_name = bookmaker.get('title', '')

            # Find corresponding previous bookmaker data
            prev_bookmaker = None
            for prev_bm in previous_odds.get('bookmakers', []):
                if prev_bm.get('title') == bookmaker_name:
                    prev_bookmaker = prev_bm
                    break

            if not prev_bookmaker:
                continue

            for market in bookmaker.get('markets', []):
                market_key = market.get('key', '')

                # Find previous market data
                prev_market = None
                for prev_mk in prev_bookmaker.get('markets', []):
                    if prev_mk.get('key') == market_key:
                        prev_market = prev_mk
                        break

                if not prev_market:
                    continue

                # Compare outcomes
                for outcome in market.get('outcomes', []):
                    outcome_name = outcome.get('name', '')
                    current_price = outcome.get('price', 0)

                    # Find previous price
                    prev_price = None
                    for prev_outcome in prev_market.get('outcomes', []):
                        if prev_outcome.get('name') == outcome_name:
                            prev_price = prev_outcome.get('price', 0)
                            break

                    if prev_price and current_price and prev_price != current_price:
                        percentage_change = ((current_price - prev_price) / prev_price) * 100

                        movements.append({
                            'bookmaker': bookmaker_name,
                            'market': market_key,
                            'outcome': outcome_name,
                            'previous_price': prev_price,
                            'current_price': current_price,
                            'price_change': current_price - prev_price,
                            'percentage_change': percentage_change,
                            'timestamp': datetime.now().isoformat()
                        })

        return movements

    async def _trigger_odds_alert(self, match: Match, movements: List[Dict], current_odds: Dict):
        """Trigger alert for significant odds movements"""
        alert_data = {
            'type': 'odds_movement',
            'match_id': match.id,
            'match_name': f"{match.home_team.name} vs {match.away_team.name}",
            'match_date': match.match_date.isoformat(),
            'movements': movements,
            'alert_level': self._determine_alert_level(movements),
            'timestamp': datetime.now().isoformat()
        }

        # Execute callbacks
        for callback in self.event_callbacks.get('odds_change', []):
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error executing odds change callback: {e}")

        # Broadcast to WebSocket clients
        await self._broadcast_to_clients(alert_data)

        # Store alert in Redis
        if self.redis_client:
            await self.redis_client.lpush(
                f"alerts:{match.id}",
                json.dumps(alert_data, default=str)
            )
            await self.redis_client.expire(f"alerts:{match.id}", 86400)  # 24 hours

        logger.info(f"Odds movement alert triggered for match {match.id}: {len(movements)} significant changes")

    def _determine_alert_level(self, movements: List[Dict]) -> str:
        """Determine the severity level of odds movements"""
        max_change = max(abs(movement['percentage_change']) for movement in movements)

        if max_change >= 30:
            return 'critical'
        elif max_change >= 20:
            return 'high'
        elif max_change >= 10:
            return 'medium'
        else:
            return 'low'

    async def _monitor_lineup_changes(self):
        """Monitor for official lineup announcements"""
        try:
            # Get matches starting within next 2 hours
            now = datetime.now()
            upcoming_matches = []

            engine = create_engine(settings.DATABASE_URL)
            SessionLocal = sessionmaker(bind=engine)

            with SessionLocal() as db:
                matches = db.query(Match).filter(
                    Match.match_date >= now,
                    Match.match_date <= now + timedelta(hours=2),
                    Match.status == 'SCHEDULED'
                ).all()

                for match in matches:
                    lineup_data = await self._check_lineup_updates(match)
                    if lineup_data:
                        await self._trigger_lineup_alert(match, lineup_data)

        except Exception as e:
            logger.error(f"Error monitoring lineup changes: {e}")

    async def _check_lineup_updates(self, match: Match) -> Optional[Dict]:
        """Check for lineup updates for a specific match"""
        try:
            # This would integrate with football data APIs that provide lineup information
            # For now, we'll simulate lineup checking

            cache_key = f"lineup:{match.external_id}"

            if self.redis_client:
                cached_lineup = await self.redis_client.get(cache_key)

                # In real implementation, would fetch from football API
                # For demo, we'll simulate lineup data
                current_lineup = {
                    'home_team_lineup': {
                        'formation': '4-3-3',
                        'starting_xi': [],
                        'substitutes': [],
                        'key_changes': []
                    },
                    'away_team_lineup': {
                        'formation': '4-2-3-1',
                        'starting_xi': [],
                        'substitutes': [],
                        'key_changes': []
                    },
                    'confirmed': True,
                    'last_updated': datetime.now().isoformat()
                }

                if cached_lineup:
                    previous_lineup = json.loads(cached_lineup)

                    # Check for significant changes
                    changes = self._detect_lineup_changes(previous_lineup, current_lineup)

                    if changes:
                        await self.redis_client.setex(cache_key, 3600, json.dumps(current_lineup))
                        return {
                            'lineup': current_lineup,
                            'changes': changes,
                            'impact_assessment': self._assess_lineup_impact(changes)
                        }

                else:
                    # First time seeing lineup
                    await self.redis_client.setex(cache_key, 3600, json.dumps(current_lineup))

        except Exception as e:
            logger.error(f"Error checking lineup for match {match.id}: {e}")

        return None

    def _detect_lineup_changes(self, previous: Dict, current: Dict) -> List[Dict]:
        """Detect significant changes between lineups"""
        changes = []

        # This would contain logic to compare lineups and detect:
        # - Key player injuries/absences
        # - Formation changes
        # - Unexpected starting XI changes
        # - Last-minute substitutions

        # Placeholder implementation
        return changes

    def _assess_lineup_impact(self, changes: List[Dict]) -> Dict:
        """Assess the potential impact of lineup changes"""
        impact = {
            'overall_impact': 0.0,
            'affected_areas': [],
            'prediction_adjustments': {},
            'confidence_impact': 0.0
        }

        # This would contain logic to assess impact on:
        # - Team strength
        # - Tactical setup
        # - Individual player importance
        # - Historical performance with/without key players

        return impact

    async def _monitor_weather_updates(self):
        """Monitor weather condition changes"""
        try:
            # Get matches in next 24 hours
            now = datetime.now()
            upcoming_matches = []

            engine = create_engine(settings.DATABASE_URL)
            SessionLocal = sessionmaker(bind=engine)

            with SessionLocal() as db:
                matches = db.query(Match).filter(
                    Match.match_date >= now,
                    Match.match_date <= now + timedelta(days=1),
                    Match.status.in_(['SCHEDULED', 'LIVE'])
                ).all()

                for match in matches:
                    if match.venue:
                        weather_update = await self._check_weather_update(match)
                        if weather_update:
                            await self._trigger_weather_alert(match, weather_update)

        except Exception as e:
            logger.error(f"Error monitoring weather updates: {e}")

    async def _check_weather_update(self, match: Match) -> Optional[Dict]:
        """Check for significant weather changes"""
        try:
            from app.services.weather_service import WeatherService
            weather_service = WeatherService()

            # Get current weather forecast
            venue_parts = match.venue.split(',') if match.venue else ['London']
            city = venue_parts[0].strip()
            country = match.home_team.country or 'GB'

            current_weather = await weather_service.get_match_weather(city, country, match.match_date)

            cache_key = f"weather:{match.id}"

            if self.redis_client:
                cached_weather = await self.redis_client.get(cache_key)

                if cached_weather:
                    previous_weather = json.loads(cached_weather)

                    # Check for significant changes
                    impact_change = abs(
                        current_weather.get('impact_assessment', {}).get('overall_score', 0) -
                        previous_weather.get('impact_assessment', {}).get('overall_score', 0)
                    )

                    if impact_change >= self.alert_thresholds['weather_changes']:
                        await self.redis_client.setex(cache_key, 1800, json.dumps(current_weather))
                        return {
                            'previous_conditions': previous_weather,
                            'current_conditions': current_weather,
                            'impact_change': impact_change,
                            'severity': 'high' if impact_change > 0.5 else 'medium'
                        }

                else:
                    # First time caching weather
                    await self.redis_client.setex(cache_key, 1800, json.dumps(current_weather))

        except Exception as e:
            logger.error(f"Error checking weather for match {match.id}: {e}")

        return None

    async def _monitor_live_matches(self):
        """Monitor live match events and updates"""
        try:
            engine = create_engine(settings.DATABASE_URL)
            SessionLocal = sessionmaker(bind=engine)

            with SessionLocal() as db:
                live_matches = db.query(Match).filter(
                    Match.status == 'LIVE'
                ).all()

                for match in live_matches:
                    await self._update_live_match_data(match)

        except Exception as e:
            logger.error(f"Error monitoring live matches: {e}")

    async def _update_live_match_data(self, match: Match):
        """Update live match data and trigger events"""
        try:
            # Get latest match data
            if match.external_id:
                match_data = await self.football_service.get_match_details(match.external_id)

                if match_data:
                    # Check for score changes
                    if (match_data.get('score', {}).get('fullTime', {}).get('homeTeam') != match.home_score or
                        match_data.get('score', {}).get('fullTime', {}).get('awayTeam') != match.away_score):

                        await self._trigger_score_update(match, match_data)

                    # Check for match events (cards, substitutions, etc.)
                    # This would require detailed event data from the API

                    # Update cache
                    if self.redis_client:
                        await self.redis_client.setex(
                            f"live_match:{match.id}",
                            60,  # 1 minute TTL
                            json.dumps(match_data, default=str)
                        )

        except Exception as e:
            logger.error(f"Error updating live match data for match {match.id}: {e}")

    async def _validate_predictions(self):
        """Validate and update prediction confidence in real-time"""
        try:
            # This would involve:
            # 1. Checking recent odds movements against predictions
            # 2. Validating lineup confirmations
            # 3. Updating confidence scores based on new information
            # 4. Triggering alerts for significant prediction changes

            engine = create_engine(settings.DATABASE_URL)
            SessionLocal = sessionmaker(bind=engine)

            with SessionLocal() as db:
                # Get matches with predictions in next 24 hours
                upcoming_matches = db.query(Match).filter(
                    Match.match_date >= datetime.now(),
                    Match.match_date <= datetime.now() + timedelta(days=1),
                    Match.is_predicted == True
                ).all()

                for match in upcoming_matches:
                    validation_result = await self._validate_match_prediction(match)
                    if validation_result:
                        await self._trigger_prediction_update(match, validation_result)

        except Exception as e:
            logger.error(f"Error validating predictions: {e}")

    async def _validate_match_prediction(self, match: Match) -> Optional[Dict]:
        """Validate a specific match prediction"""
        # Placeholder for prediction validation logic
        return None

    async def _monitor_system_health(self):
        """Monitor system health and performance"""
        try:
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'active_monitors': len(self.monitoring_tasks),
                'websocket_clients': len(self.websocket_clients),
                'active_matches': len(self.active_matches),
                'cache_size': len(self.odds_cache),
                'memory_usage': 0,  # Would implement actual memory monitoring
                'api_response_times': {},
                'error_counts': {}
            }

            # Store health data
            if self.redis_client:
                await self.redis_client.setex(
                    'system_health',
                    120,  # 2 minutes TTL
                    json.dumps(health_data)
                )

            # Check for issues and trigger alerts if needed
            await self._check_system_issues(health_data)

        except Exception as e:
            logger.error(f"Error monitoring system health: {e}")

    async def _check_system_issues(self, health_data: Dict):
        """Check for system performance issues"""
        issues = []

        # Check for high memory usage, slow response times, etc.
        # Trigger alerts if needed

        if issues:
            alert = {
                'type': 'system_health',
                'severity': 'warning',
                'issues': issues,
                'timestamp': datetime.now().isoformat()
            }

            await self._broadcast_to_clients(alert)

    # WebSocket management
    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new WebSocket client"""
        self.websocket_clients.add(websocket)
        logger.info(f"New WebSocket client registered. Total clients: {len(self.websocket_clients)}")

        # Send initial data
        await self._send_initial_data(websocket)

    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a WebSocket client"""
        self.websocket_clients.discard(websocket)
        logger.info(f"WebSocket client unregistered. Total clients: {len(self.websocket_clients)}")

    async def _send_initial_data(self, websocket: websockets.WebSocketServerProtocol):
        """Send initial data to newly connected client"""
        try:
            initial_data = {
                'type': 'initial_data',
                'active_matches': list(self.active_matches.values()),
                'system_status': 'operational',
                'timestamp': datetime.now().isoformat()
            }

            await websocket.send(json.dumps(initial_data))

        except Exception as e:
            logger.error(f"Error sending initial data to client: {e}")

    async def _broadcast_to_clients(self, data: Dict):
        """Broadcast data to all connected WebSocket clients"""
        if not self.websocket_clients:
            return

        message = json.dumps(data, default=str)
        disconnected_clients = []

        for client in self.websocket_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.append(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.websocket_clients.discard(client)

    # Event system
    def add_event_callback(self, event_type: str, callback: Callable):
        """Add callback for specific event type"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)

    def remove_event_callback(self, event_type: str, callback: Callable):
        """Remove callback for specific event type"""
        if event_type in self.event_callbacks and callback in self.event_callbacks[event_type]:
            self.event_callbacks[event_type].remove(callback)

    # Alert triggers
    async def _trigger_lineup_alert(self, match: Match, lineup_data: Dict):
        """Trigger alert for lineup changes"""
        alert_data = {
            'type': 'lineup_update',
            'match_id': match.id,
            'match_name': f"{match.home_team.name} vs {match.away_team.name}",
            'lineup_data': lineup_data,
            'timestamp': datetime.now().isoformat()
        }

        for callback in self.event_callbacks.get('lineup_update', []):
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error executing lineup callback: {e}")

        await self._broadcast_to_clients(alert_data)

    async def _trigger_weather_alert(self, match: Match, weather_data: Dict):
        """Trigger alert for weather changes"""
        alert_data = {
            'type': 'weather_update',
            'match_id': match.id,
            'match_name': f"{match.home_team.name} vs {match.away_team.name}",
            'weather_data': weather_data,
            'timestamp': datetime.now().isoformat()
        }

        for callback in self.event_callbacks.get('weather_update', []):
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error executing weather callback: {e}")

        await self._broadcast_to_clients(alert_data)

    async def _trigger_score_update(self, match: Match, match_data: Dict):
        """Trigger alert for score updates"""
        alert_data = {
            'type': 'score_update',
            'match_id': match.id,
            'match_name': f"{match.home_team.name} vs {match.away_team.name}",
            'score_data': match_data,
            'timestamp': datetime.now().isoformat()
        }

        for callback in self.event_callbacks.get('match_event', []):
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error executing match event callback: {e}")

        await self._broadcast_to_clients(alert_data)

    async def _trigger_prediction_update(self, match: Match, validation_data: Dict):
        """Trigger alert for prediction updates"""
        alert_data = {
            'type': 'prediction_update',
            'match_id': match.id,
            'match_name': f"{match.home_team.name} vs {match.away_team.name}",
            'validation_data': validation_data,
            'timestamp': datetime.now().isoformat()
        }

        for callback in self.event_callbacks.get('prediction_update', []):
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error executing prediction update callback: {e}")

        await self._broadcast_to_clients(alert_data)

    async def shutdown(self):
        """Shutdown the monitoring system"""
        logger.info("Shutting down real-time monitoring system...")

        # Cancel all monitoring tasks
        for task_name, task in self.monitoring_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        # Close WebSocket connections
        for client in self.websocket_clients:
            await client.close()

        logger.info("Real-time monitoring system shutdown complete")