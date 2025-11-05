"""
🚀 SIMPLE API-SPORTS SYNCHRONIZER
Sincronizador simplificado que USA APENAS API-Sports
Criado para resolver o problema de 403 com FootballDataService
"""

import asyncio
import httpx
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.config import settings
from app.models import Match, Team, Odds

logger = logging.getLogger(__name__)


class SimpleAPISportsSync:
    """Sincronizador simples usando APENAS API-Sports"""

    def __init__(self):
        self.api_key = settings.API_SPORTS_KEY
        if not self.api_key:
            raise ValueError("API_SPORTS_KEY não configurada. Configure no arquivo .env")
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": self.api_key
        }

        # Ligas principais com seus IDs na API-Sports
        self.leagues = {
            39: "Premier League",      # Inglaterra
            140: "La Liga",            # Espanha
            135: "Serie A",            # Itália
            78: "Bundesliga",          # Alemanha
            61: "Ligue 1",             # França
            71: "Brasileirão",         # Brasil
        }

    async def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """Fazer requisição à API-Sports"""
        try:
            await asyncio.sleep(0.5)  # Rate limit

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/{endpoint}",
                    headers=self.headers,
                    params=params or {}
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    return {"response": [], "errors": [f"HTTP {response.status_code}"]}

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"response": [], "errors": [str(e)]}

    async def sync_today_matches(self) -> Dict[str, int]:
        """
        Sincroniza jogos de hoje de todas as ligas principais
        """
        logger.info("🚀 INICIANDO SYNC SIMPLES (API-Sports)")

        results = {
            "teams": 0,
            "matches": 0,
            "odds": 0,
            "errors": 0
        }

        today = datetime.now().strftime("%Y-%m-%d")

        with get_db_session() as db:
            # Buscar jogos de hoje
            logger.info(f"📅 Buscando jogos de {today}...")

            data = await self._request("fixtures", {"date": today})

            if "errors" in data and data["errors"]:
                logger.error(f"Erro na API: {data['errors']}")
                results["errors"] += 1
                return results

            fixtures = data.get("response", [])
            logger.info(f"✅ Encontrados {len(fixtures)} jogos")

            for fixture_data in fixtures:
                try:
                    # Processar fixture
                    fixture = fixture_data["fixture"]
                    league = fixture_data["league"]
                    teams_data = fixture_data["teams"]
                    goals = fixture_data["goals"]
                    score = fixture_data["score"]

                    # Pular se não for de uma liga principal
                    if league["id"] not in self.leagues:
                        continue

                    # 1. CRIAR/ATUALIZAR TIMES
                    home_team = await self._get_or_create_team(
                        db, teams_data["home"], league["name"]
                    )
                    away_team = await self._get_or_create_team(
                        db, teams_data["away"], league["name"]
                    )

                    if not home_team or not away_team:
                        continue

                    results["teams"] += 2

                    # 2. CRIAR/ATUALIZAR MATCH
                    match = await self._get_or_create_match(
                        db, fixture, league, home_team, away_team, goals, score
                    )

                    if match:
                        results["matches"] += 1

                    # 3. BUSCAR ODDS (se jogo não começou)
                    if fixture["status"]["short"] in ["NS", "TBD"]:
                        odds_created = await self._create_odds(db, match, fixture["id"])
                        if odds_created:
                            results["odds"] += 1

                    db.commit()

                except Exception as e:
                    logger.error(f"Erro processando fixture {fixture.get('id')}: {e}")
                    db.rollback()
                    results["errors"] += 1
                    continue

        logger.info(f"✅ SYNC COMPLETO: {results}")
        return results

    async def _get_or_create_team(self, db: Session, team_data: Dict, league: str) -> Team:
        """Criar ou obter time"""
        try:
            external_id = str(team_data["id"])

            team = db.query(Team).filter(Team.external_id == external_id).first()

            if not team:
                team = Team(
                    external_id=external_id,
                    name=team_data["name"],
                    logo_url=team_data.get("logo"),
                    league=league
                )
                db.add(team)
                logger.info(f"✅ Criado time: {team.name}")

            return team

        except Exception as e:
            logger.error(f"Erro criando team: {e}")
            return None

    async def _get_or_create_match(
        self, db: Session, fixture: Dict, league: Dict,
        home_team: Team, away_team: Team, goals: Dict, score: Dict
    ) -> Match:
        """Criar ou atualizar match"""
        try:
            external_id = str(fixture["id"])

            match = db.query(Match).filter(Match.external_id == external_id).first()

            match_date = datetime.fromisoformat(
                fixture["date"].replace("Z", "+00:00")
            )

            if not match:
                match = Match(
                    external_id=external_id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    league=league["name"],
                    season=str(league["season"]),
                    match_date=match_date,
                    venue=fixture.get("venue", {}).get("name"),
                    status=self._map_status(fixture["status"]["short"]),
                    home_score=goals.get("home"),
                    away_score=goals.get("away"),
                    home_score_ht=score.get("halftime", {}).get("home"),
                    away_score_ht=score.get("halftime", {}).get("away")
                )
                db.add(match)
                logger.info(f"✅ Criado match: {home_team.name} vs {away_team.name}")
            else:
                # Atualizar status/placar
                match.status = self._map_status(fixture["status"]["short"])
                match.home_score = goals.get("home")
                match.away_score = goals.get("away")
                match.home_score_ht = score.get("halftime", {}).get("home")
                match.away_score_ht = score.get("halftime", {}).get("away")

            return match

        except Exception as e:
            logger.error(f"Erro criando match: {e}")
            return None

    async def _create_odds(self, db: Session, match: Match, fixture_id: int) -> bool:
        """Buscar e criar odds"""
        try:
            # Verificar se já tem odds
            existing = db.query(Odds).filter(Odds.match_id == match.id).first()
            if existing:
                return False

            # Buscar odds da API
            data = await self._request("odds", {"fixture": fixture_id})

            if not data.get("response"):
                logger.warning(f"Sem odds para fixture {fixture_id}")
                return False

            # Extrair primeira bookmaker com market 1X2
            for odds_data in data["response"]:
                bookmakers = odds_data.get("bookmakers", [])

                for bookmaker in bookmakers:
                    bets = bookmaker.get("bets", [])

                    for bet in bets:
                        if bet["name"] == "Match Winner":
                            values = bet["values"]

                            home_odd = next((v["odd"] for v in values if v["value"] == "Home"), None)
                            draw_odd = next((v["odd"] for v in values if v["value"] == "Draw"), None)
                            away_odd = next((v["odd"] for v in values if v["value"] == "Away"), None)

                            if home_odd and draw_odd and away_odd:
                                odds = Odds(
                                    match_id=match.id,
                                    bookmaker=bookmaker["name"],
                                    market="1X2",
                                    home_win=float(home_odd),
                                    draw=float(draw_odd),
                                    away_win=float(away_odd),
                                    odds_timestamp=datetime.now()
                                )
                                db.add(odds)
                                logger.info(f"✅ Criadas odds: {home_odd} / {draw_odd} / {away_odd}")
                                return True

            return False

        except Exception as e:
            logger.error(f"Erro criando odds: {e}")
            return False

    def _map_status(self, api_status: str) -> str:
        """Mapear status da API"""
        mapping = {
            "TBD": "NS",
            "NS": "NS",
            "1H": "1H",
            "HT": "HT",
            "2H": "2H",
            "ET": "2H",
            "P": "2H",
            "FT": "FT",
            "AET": "FT",
            "PEN": "FT",
            "PST": "POSTPONED",
            "CANC": "CANCELLED",
            "ABD": "CANCELLED",
            "AWD": "FT",
            "WO": "FT"
        }
        return mapping.get(api_status, "NS")


# Instância global
simple_sync = SimpleAPISportsSync()
