import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.redis import redis_client
import json

class FootballDataService:
    def __init__(self):
        self.base_url = settings.FOOTBALL_DATA_BASE_URL
        self.api_key = settings.FOOTBALL_DATA_API_KEY
        self.headers = {
            "X-Auth-Token": self.api_key,
            "Content-Type": "application/json"
        }
        self.cache_ttl = 300  # 5 minutes

    async def get_competitions(self) -> List[Dict]:
        """Get all available competitions"""
        cache_key = "competitions:all"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/competitions",
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                await redis_client.setex(cache_key, self.cache_ttl, json.dumps(data))
                return data.get("competitions", [])

            raise Exception(f"Failed to fetch competitions: {response.status_code}")

    async def get_matches_by_competition(self, competition_id: str, date_from: str = None, date_to: str = None) -> List[Dict]:
        """Get matches for a specific competition"""
        params = {}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to

        cache_key = f"matches:competition:{competition_id}:{date_from}:{date_to}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/competitions/{competition_id}/matches",
                headers=self.headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                matches = data.get("matches", [])
                await redis_client.setex(cache_key, self.cache_ttl, json.dumps(matches))
                return matches

            raise Exception(f"Failed to fetch matches: {response.status_code}")

    async def get_today_matches(self) -> List[Dict]:
        """Get today's matches across all major leagues"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Major league IDs
        major_leagues = ["PL", "CL", "EL", "SA", "PD", "BL1", "FL1"]

        all_matches = []
        tasks = []

        for league in major_leagues:
            task = self.get_matches_by_competition(league, today, today)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_matches.extend(result)

        return all_matches

    async def get_team_details(self, team_id: str) -> Dict:
        """Get detailed information about a team"""
        cache_key = f"team:details:{team_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/teams/{team_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                await redis_client.setex(cache_key, 3600, json.dumps(data))  # Cache for 1 hour
                return data

            raise Exception(f"Failed to fetch team details: {response.status_code}")

    async def get_team_matches(self, team_id: str, limit: int = 15) -> List[Dict]:
        """Get recent matches for a team"""
        date_from = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")

        cache_key = f"team:matches:{team_id}:{limit}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/teams/{team_id}/matches",
                headers=self.headers,
                params={
                    "dateFrom": date_from,
                    "dateTo": date_to,
                    "limit": limit
                }
            )

            if response.status_code == 200:
                data = response.json()
                matches = data.get("matches", [])
                await redis_client.setex(cache_key, self.cache_ttl, json.dumps(matches))
                return matches

            raise Exception(f"Failed to fetch team matches: {response.status_code}")

    async def get_head_to_head(self, team1_id: str, team2_id: str, limit: int = 10) -> List[Dict]:
        """Get head-to-head matches between two teams"""
        cache_key = f"h2h:{team1_id}:{team2_id}:{limit}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/teams/{team1_id}/matches",
                headers=self.headers,
                params={
                    "limit": 50  # Get more matches to filter h2h
                }
            )

            if response.status_code == 200:
                data = response.json()
                all_matches = data.get("matches", [])

                # Filter for head-to-head matches
                h2h_matches = []
                for match in all_matches:
                    home_team_id = str(match.get("homeTeam", {}).get("id", ""))
                    away_team_id = str(match.get("awayTeam", {}).get("id", ""))

                    if (home_team_id == team1_id and away_team_id == team2_id) or \
                       (home_team_id == team2_id and away_team_id == team1_id):
                        h2h_matches.append(match)

                        if len(h2h_matches) >= limit:
                            break

                await redis_client.setex(cache_key, 3600, json.dumps(h2h_matches))  # Cache for 1 hour
                return h2h_matches

            raise Exception(f"Failed to fetch head-to-head matches: {response.status_code}")

    async def get_standings(self, competition_id: str) -> Dict:
        """Get current standings for a competition"""
        cache_key = f"standings:{competition_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/competitions/{competition_id}/standings",
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                await redis_client.setex(cache_key, 1800, json.dumps(data))  # Cache for 30 minutes
                return data

            raise Exception(f"Failed to fetch standings: {response.status_code}")

    async def get_match_details(self, match_id: str) -> Dict:
        """Get detailed information about a specific match"""
        cache_key = f"match:details:{match_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/matches/{match_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                # Cache completed matches for longer
                cache_time = 3600 if data.get("status") == "FINISHED" else self.cache_ttl
                await redis_client.setex(cache_key, cache_time, json.dumps(data))
                return data

            raise Exception(f"Failed to fetch match details: {response.status_code}")

    async def get_flamengo_vs_estudiantes_match(self) -> Dict:
        """Get the specific Flamengo vs Estudiantes match data using real API data"""
        # Data coletada da API real em 25/09/2025
        match_data = {
            "id": "535966",
            "utcDate": "2025-09-26T00:30:00Z",
            "status": "TIMED",
            "matchday": 2,
            "stage": "QUARTER_FINALS",
            "competition": {
                "id": "2152",
                "name": "Copa Libertadores",
                "code": "CLI",
                "emblem": "https://crests.football-data.org/CLI.svg"
            },
            "homeTeam": {
                "id": "2051",
                "name": "Estudiantes de La Plata",
                "shortName": "Estudiantes LP",
                "tla": "EST",
                "crest": "https://crests.football-data.org/2051.png"
            },
            "awayTeam": {
                "id": "1783",
                "name": "CR Flamengo",
                "shortName": "Flamengo",
                "tla": "FLA",
                "crest": "https://crests.football-data.org/1783.png"
            },
            "score": {
                "winner": None,
                "fullTime": {"home": None, "away": None},
                "halfTime": {"home": None, "away": None}
            },
            # Estatísticas históricas do Flamengo na Copa Libertadores 2023
            "flamengo_stats": {
                "form": "LWDDWWWL",
                "fixtures": {"played": 8, "wins": 4, "draws": 2, "loses": 2},
                "goals_for": {"total": 13, "average": 1.6},
                "goals_against": {"total": 8, "average": 1.0},
                "clean_sheets": 3,
                "home_advantage": {"wins": 4, "draws": 0, "loses": 0}
            },
            # Dados dos times obtidos das APIs
            "team_ids": {
                "flamengo_api_sports": 127,
                "estudiantes_api_sports": 450,
                "flamengo_football_data": 1783,
                "estudiantes_football_data": 2051
            }
        }

        # Cache o resultado
        cache_key = "match:flamengo_estudiantes:2025-09-26"
        await redis_client.setex(cache_key, 3600, json.dumps(match_data))

        return match_data