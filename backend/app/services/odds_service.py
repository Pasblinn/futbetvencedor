import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.redis import redis_client
import json

class OddsService:
    def __init__(self):
        self.base_url = settings.ODDS_API_BASE_URL
        self.api_key = settings.ODDS_API_KEY
        self.cache_ttl = 300  # 5 minutes for live odds

    async def get_sports(self) -> List[Dict]:
        """Get available sports"""
        cache_key = "odds:sports"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/sports",
                params={"apiKey": self.api_key}
            )

            if response.status_code == 200:
                data = response.json()
                await redis_client.setex(cache_key, 3600, json.dumps(data))  # Cache for 1 hour
                return data

            raise Exception(f"Failed to fetch sports: {response.status_code}")

    async def get_odds(self, sport: str = "soccer_epl", regions: str = "us,uk,eu", markets: str = "h2h,spreads,totals,btts") -> List[Dict]:
        """Get odds for a specific sport"""
        cache_key = f"odds:{sport}:{regions}:{markets}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/sports/{sport}/odds",
                params={
                    "apiKey": self.api_key,
                    "regions": regions,
                    "markets": markets,
                    "oddsFormat": "decimal",
                    "dateFormat": "iso"
                }
            )

            if response.status_code == 200:
                data = response.json()
                await redis_client.setex(cache_key, self.cache_ttl, json.dumps(data))
                return data

            raise Exception(f"Failed to fetch odds: {response.status_code}")

    async def get_match_odds(self, match_external_id: str) -> Dict:
        """Get odds for a specific match"""
        cache_key = f"odds:match:{match_external_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        # Get odds from multiple sports/leagues
        sports = [
            "soccer_epl",  # Premier League
            "soccer_spain_la_liga",  # La Liga
            "soccer_italy_serie_a",  # Serie A
            "soccer_germany_bundesliga",  # Bundesliga
            "soccer_france_ligue_one",  # Ligue 1
            "soccer_uefa_champs_league",  # Champions League
            "soccer_uefa_europa_league"  # Europa League
        ]

        match_odds = {}

        for sport in sports:
            try:
                odds_data = await self.get_odds(sport)
                for match in odds_data:
                    if match.get("id") == match_external_id:
                        match_odds = match
                        break

                if match_odds:
                    break

            except Exception as e:
                continue  # Try next sport

        if match_odds:
            await redis_client.setex(cache_key, self.cache_ttl, json.dumps(match_odds))

        return match_odds

    async def get_bookmaker_comparison(self, match_external_id: str) -> Dict:
        """Compare odds across different bookmakers for a match"""
        cache_key = f"odds:comparison:{match_external_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        match_odds = await self.get_match_odds(match_external_id)

        if not match_odds:
            return {}

        comparison = {
            "match_id": match_external_id,
            "home_team": match_odds.get("home_team"),
            "away_team": match_odds.get("away_team"),
            "commence_time": match_odds.get("commence_time"),
            "bookmakers": {},
            "best_odds": {
                "home_win": {"odds": 0, "bookmaker": ""},
                "draw": {"odds": 0, "bookmaker": ""},
                "away_win": {"odds": 0, "bookmaker": ""},
                "over_2_5": {"odds": 0, "bookmaker": ""},
                "under_2_5": {"odds": 0, "bookmaker": ""},
                "btts_yes": {"odds": 0, "bookmaker": ""},
                "btts_no": {"odds": 0, "bookmaker": ""}
            }
        }

        for bookmaker in match_odds.get("bookmakers", []):
            bookmaker_name = bookmaker.get("title", "")
            comparison["bookmakers"][bookmaker_name] = {}

            for market in bookmaker.get("markets", []):
                market_key = market.get("key", "")

                if market_key == "h2h":  # Head-to-head (1X2)
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = outcome.get("price", 0)

                        if name == match_odds.get("home_team"):
                            comparison["bookmakers"][bookmaker_name]["home_win"] = price
                            if price > comparison["best_odds"]["home_win"]["odds"]:
                                comparison["best_odds"]["home_win"] = {"odds": price, "bookmaker": bookmaker_name}

                        elif name == match_odds.get("away_team"):
                            comparison["bookmakers"][bookmaker_name]["away_win"] = price
                            if price > comparison["best_odds"]["away_win"]["odds"]:
                                comparison["best_odds"]["away_win"] = {"odds": price, "bookmaker": bookmaker_name}

                        elif name == "Draw":
                            comparison["bookmakers"][bookmaker_name]["draw"] = price
                            if price > comparison["best_odds"]["draw"]["odds"]:
                                comparison["best_odds"]["draw"] = {"odds": price, "bookmaker": bookmaker_name}

                elif market_key == "totals":  # Over/Under
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = outcome.get("price", 0)
                        point = outcome.get("point", 0)

                        if point == 2.5:
                            if name == "Over":
                                comparison["bookmakers"][bookmaker_name]["over_2_5"] = price
                                if price > comparison["best_odds"]["over_2_5"]["odds"]:
                                    comparison["best_odds"]["over_2_5"] = {"odds": price, "bookmaker": bookmaker_name}

                            elif name == "Under":
                                comparison["bookmakers"][bookmaker_name]["under_2_5"] = price
                                if price > comparison["best_odds"]["under_2_5"]["odds"]:
                                    comparison["best_odds"]["under_2_5"] = {"odds": price, "bookmaker": bookmaker_name}

                elif market_key == "btts":  # Both Teams to Score
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = outcome.get("price", 0)

                        if name == "Yes":
                            comparison["bookmakers"][bookmaker_name]["btts_yes"] = price
                            if price > comparison["best_odds"]["btts_yes"]["odds"]:
                                comparison["best_odds"]["btts_yes"] = {"odds": price, "bookmaker": bookmaker_name}

                        elif name == "No":
                            comparison["bookmakers"][bookmaker_name]["btts_no"] = price
                            if price > comparison["best_odds"]["btts_no"]["odds"]:
                                comparison["best_odds"]["btts_no"] = {"odds": price, "bookmaker": bookmaker_name}

        await redis_client.setex(cache_key, self.cache_ttl, json.dumps(comparison))
        return comparison

    async def track_odds_movement(self, match_external_id: str) -> List[Dict]:
        """Track odds movement over time for a match"""
        cache_key = f"odds:movement:{match_external_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            historical_data = json.loads(cached_data)
        else:
            historical_data = []

        # Get current odds
        current_odds = await self.get_match_odds(match_external_id)

        if current_odds:
            timestamp = datetime.now().isoformat()
            odds_snapshot = {
                "timestamp": timestamp,
                "bookmakers": {}
            }

            for bookmaker in current_odds.get("bookmakers", []):
                bookmaker_name = bookmaker.get("title", "")
                odds_snapshot["bookmakers"][bookmaker_name] = {}

                for market in bookmaker.get("markets", []):
                    market_key = market.get("key", "")
                    if market_key == "h2h":
                        for outcome in market.get("outcomes", []):
                            name = outcome.get("name", "").lower().replace(" ", "_")
                            odds_snapshot["bookmakers"][bookmaker_name][name] = outcome.get("price", 0)

            historical_data.append(odds_snapshot)

            # Keep only last 24 hours of data
            cutoff_time = datetime.now() - timedelta(hours=24)
            historical_data = [
                data for data in historical_data
                if datetime.fromisoformat(data["timestamp"]) > cutoff_time
            ]

            await redis_client.setex(cache_key, 86400, json.dumps(historical_data))  # Cache for 24 hours

        return historical_data

    async def calculate_value_bets(self, match_external_id: str, predicted_probabilities: Dict) -> List[Dict]:
        """Calculate value bets based on predicted probabilities vs market odds"""
        comparison = await self.get_bookmaker_comparison(match_external_id)

        if not comparison or not predicted_probabilities:
            return []

        value_bets = []

        for outcome, probability in predicted_probabilities.items():
            if outcome in comparison["best_odds"]:
                best_odds_data = comparison["best_odds"][outcome]
                market_odds = best_odds_data["odds"]

                if market_odds > 0:
                    implied_probability = 1 / market_odds
                    value = (probability * market_odds) - 1

                    if value > 0.05:  # Minimum 5% value
                        value_bets.append({
                            "outcome": outcome,
                            "predicted_probability": probability,
                            "market_odds": market_odds,
                            "implied_probability": implied_probability,
                            "value": value,
                            "value_percentage": value * 100,
                            "bookmaker": best_odds_data["bookmaker"],
                            "kelly_percentage": min(value / (market_odds - 1), 0.25)  # Max 25% Kelly
                        })

        # Sort by value descending
        value_bets.sort(key=lambda x: x["value"], reverse=True)

        return value_bets