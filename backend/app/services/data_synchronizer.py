import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db_session
from app.core.redis import redis_client
from app.models.team import Team
from app.models.match import Match
from app.models.odds import Odds
from app.services.football_data_service import FootballDataService
from app.services.odds_service import OddsService
from app.services.prediction_integration import prediction_integration
from app.services.api_football_service import APIFootballService

logger = logging.getLogger(__name__)

class DataSynchronizer:
    """
    Centralized service for synchronizing real football data across all systems.
    Handles data fetching, normalization, storage, and triggers predictions.
    """

    def __init__(self):
        self.football_service = FootballDataService()
        self.odds_service = OddsService()
        self.api_football = APIFootballService()  # API real com odds

        # Major leagues to monitor
        self.leagues = {
            "PL": "Premier League",
            "BL1": "Bundesliga",
            "PD": "La Liga",
            "SA": "Serie A",
            "FL1": "Ligue 1",
            "CL": "Champions League",
            "EL": "Europa League"
        }

    async def full_sync(self) -> Dict[str, int]:
        """
        Complete synchronization of all football data.
        Returns count of synchronized entities.
        """
        logger.info("🔄 Starting full data synchronization...")

        results = {
            "teams": 0,
            "matches": 0,
            "odds": 0,
            "predictions": 0,
            "errors": 0
        }

        try:
            # 1. Sync teams first (required for matches)
            results["teams"] = await self._sync_teams()

            # 2. Sync recent and upcoming matches
            results["matches"] = await self._sync_matches()

            # 3. Sync odds for upcoming matches
            results["odds"] = await self._sync_odds()

            # 4. Generate predictions for new matches
            results["predictions"] = await self._sync_predictions()

            # Update last sync time
            await redis_client.setex("last_full_sync", 3600, datetime.now().isoformat())

            logger.info(f"✅ Full sync completed: {results}")

        except Exception as e:
            logger.error(f"❌ Full sync failed: {str(e)}")
            results["errors"] += 1

        return results

    async def quick_sync(self) -> Dict[str, int]:
        """
        Quick synchronization for live updates.
        Only updates match scores, status, and live odds.
        """
        logger.info("⚡ Starting quick data sync...")

        results = {
            "live_matches": 0,
            "updated_odds": 0,
            "errors": 0
        }

        try:
            # Update live match data
            results["live_matches"] = await self._update_live_matches()

            # Update odds for today's matches
            results["updated_odds"] = await self._update_live_odds()

            # Update last quick sync time
            await redis_client.setex("last_quick_sync", 300, datetime.now().isoformat())

            logger.info(f"⚡ Quick sync completed: {results}")

        except Exception as e:
            logger.error(f"❌ Quick sync failed: {str(e)}")
            results["errors"] += 1

        return results

    async def _sync_teams(self) -> int:
        """Synchronize team data from all major leagues"""
        logger.info("🏆 Syncing teams...")

        teams_count = 0

        with get_db_session() as db:
            for league_code, league_name in self.leagues.items():
                try:
                    # Get teams from standings (most reliable way to get current teams)
                    standings_data = await self.football_service.get_standings(league_code)

                    if "standings" in standings_data:
                        for standing_group in standings_data["standings"]:
                            for team_data in standing_group.get("table", []):
                                team_info = team_data["team"]

                                # Check if team exists
                                existing_team = db.query(Team).filter(
                                    Team.external_id == str(team_info["id"])
                                ).first()

                                if not existing_team:
                                    # Create new team
                                    new_team = Team(
                                        external_id=str(team_info["id"]),
                                        name=team_info["name"],
                                        short_name=team_info.get("shortName", team_info["name"][:3]),
                                        country=team_info.get("area", {}).get("name", "Unknown"),
                                        founded=team_info.get("founded"),
                                        logo_url=team_info.get("crest"),
                                        venue=team_info.get("venue"),
                                        league=league_name
                                    )

                                    db.add(new_team)
                                    teams_count += 1
                                else:
                                    # Update existing team data
                                    existing_team.name = team_info["name"]
                                    existing_team.short_name = team_info.get("shortName", team_info["name"][:3])
                                    existing_team.logo_url = team_info.get("crest")
                                    existing_team.league = league_name

                    db.commit()
                    logger.info(f"✅ Synced teams for {league_name}")

                except Exception as e:
                    logger.error(f"❌ Failed to sync teams for {league_name}: {str(e)}")
                    db.rollback()
                    continue

        logger.info(f"🏆 Teams sync completed: {teams_count} teams processed")
        return teams_count

    async def _sync_matches(self) -> int:
        """Synchronize match data for recent and upcoming games"""
        logger.info("⚽ Syncing matches...")

        matches_count = 0
        # APENAS jogos atuais (hoje) e futuros - sem dados históricos
        date_from = datetime.now().strftime("%Y-%m-%d")  # A partir de hoje
        date_to = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")  # Próximas 3 semanas

        with get_db_session() as db:
            for league_code, league_name in self.leagues.items():
                try:
                    matches_data = await self.football_service.get_matches_by_competition(
                        league_code, date_from, date_to
                    )

                    for match_data in matches_data:
                        try:
                            # Check if match exists
                            existing_match = db.query(Match).filter(
                                Match.external_id == str(match_data["id"])
                            ).first()

                            # Get teams
                            home_team = db.query(Team).filter(
                                Team.external_id == str(match_data["homeTeam"]["id"])
                            ).first()
                            away_team = db.query(Team).filter(
                                Team.external_id == str(match_data["awayTeam"]["id"])
                            ).first()

                            if not home_team or not away_team:
                                logger.warning(f"Teams not found for match {match_data['id']}")
                                continue

                            match_datetime = datetime.fromisoformat(
                                match_data["utcDate"].replace("Z", "+00:00")
                            )

                            # FILTRO: Apenas jogos atuais ou futuros (não históricos)
                            now = datetime.now(match_datetime.tzinfo)
                            if match_datetime < now - timedelta(hours=3):  # 3h de margem para jogos em andamento
                                match_status = self._map_match_status(match_data["status"])
                                if match_status == "FINISHED":
                                    continue  # Pular jogos já finalizados no passado

                            # Extract scores
                            score = match_data.get("score", {})
                            full_time = score.get("fullTime", {})
                            half_time = score.get("halfTime", {})

                            if not existing_match:
                                # Create new match
                                new_match = Match(
                                    external_id=str(match_data["id"]),
                                    home_team_id=home_team.id,
                                    away_team_id=away_team.id,
                                    league=league_name,
                                    season=str(match_data.get("season", {}).get("startDate", "")[:4]),
                                    matchday=match_data.get("matchday"),
                                    match_date=match_datetime,
                                    venue=match_data.get("venue"),
                                    referee=match_data.get("referees", [{}])[0].get("name") if match_data.get("referees") else None,
                                    status=self._map_match_status(match_data["status"]),
                                    home_score=full_time.get("home"),
                                    away_score=full_time.get("away"),
                                    home_score_ht=half_time.get("home"),
                                    away_score_ht=half_time.get("away")
                                )

                                db.add(new_match)
                                matches_count += 1

                            else:
                                # Update existing match
                                existing_match.status = self._map_match_status(match_data["status"])
                                existing_match.home_score = full_time.get("home")
                                existing_match.away_score = full_time.get("away")
                                existing_match.home_score_ht = half_time.get("home")
                                existing_match.away_score_ht = half_time.get("away")
                                existing_match.venue = match_data.get("venue")

                                if match_data.get("referees"):
                                    existing_match.referee = match_data["referees"][0].get("name")

                        except Exception as e:
                            logger.error(f"❌ Failed to process match {match_data.get('id', 'unknown')}: {str(e)}")
                            continue

                    db.commit()
                    logger.info(f"✅ Synced matches for {league_name}")

                except Exception as e:
                    logger.error(f"❌ Failed to sync matches for {league_name}: {str(e)}")
                    db.rollback()
                    continue

        logger.info(f"⚽ Matches sync completed: {matches_count} matches processed")
        return matches_count

    async def _sync_odds(self) -> int:
        """Synchronize betting odds for upcoming matches from API-Football"""
        logger.info("💰 Syncing odds from API-Football...")

        odds_count = 0

        with get_db_session() as db:
            # Get upcoming matches that need odds (próximos 7 dias)
            upcoming_matches = db.query(Match).filter(
                Match.match_date > datetime.now(),
                Match.match_date < datetime.now() + timedelta(days=7),
                Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
            ).all()

            logger.info(f"📊 {len(upcoming_matches)} jogos encontrados para buscar odds")

            for match in upcoming_matches:
                try:
                    # Verificar se já tem odds (não sobrescrever sempre)
                    existing_odds = db.query(Odds).filter(
                        Odds.match_id == match.id
                    ).first()

                    # Pular se já tem odds recentes (< 1 hora)
                    if existing_odds and existing_odds.updated_at:
                        time_diff = datetime.now() - existing_odds.updated_at
                        if time_diff < timedelta(hours=1):
                            continue

                    # Buscar odds da API-Football usando o external_id
                    if not match.external_id:
                        continue

                    fixture_id = int(match.external_id)
                    odds_data = await self.api_football.get_odds(fixture_id)

                    if odds_data and len(odds_data) > 0:
                        # Processar odds (pegar a primeira casa de apostas ou melhor odd)
                        best_odds = self._extract_best_odds(odds_data)

                        if not best_odds:
                            continue

                        if not existing_odds:
                            new_odds = Odds(
                                match_id=match.id,
                                bookmaker=best_odds.get("bookmaker_name", "API-Football"),  # Nome real da bookmaker
                                market="1X2",
                                home_win=best_odds.get("home_win", 2.0),
                                draw=best_odds.get("draw", 3.0),
                                away_win=best_odds.get("away_win", 2.5),
                                over_2_5=best_odds.get("over_2_5"),
                                under_2_5=best_odds.get("under_2_5"),
                                btts_yes=best_odds.get("btts_yes"),
                                btts_no=best_odds.get("btts_no"),
                                odds_timestamp=datetime.now()
                            )

                            db.add(new_odds)
                            odds_count += 1
                            logger.info(f"✅ Odds criadas para {match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}: [{new_odds.bookmaker}] Home={new_odds.home_win}, Draw={new_odds.draw}, Away={new_odds.away_win}")
                        else:
                            # Update existing odds
                            existing_odds.bookmaker = best_odds.get("bookmaker_name", existing_odds.bookmaker)  # Atualizar bookmaker
                            existing_odds.home_win = best_odds.get("home_win", existing_odds.home_win)
                            existing_odds.draw = best_odds.get("draw", existing_odds.draw)
                            existing_odds.away_win = best_odds.get("away_win", existing_odds.away_win)
                            existing_odds.over_2_5 = best_odds.get("over_2_5")
                            existing_odds.under_2_5 = best_odds.get("under_2_5")
                            existing_odds.btts_yes = best_odds.get("btts_yes")
                            existing_odds.btts_no = best_odds.get("btts_no")
                            existing_odds.odds_timestamp = datetime.now()
                            odds_count += 1
                            logger.info(f"✅ Odds atualizadas para {match.home_team.name if match.home_team else '?'} vs {match.away_team.name if match.away_team else '?'}: [{existing_odds.bookmaker}]")

                except Exception as e:
                    logger.error(f"❌ Failed to sync odds for match {match.id}: {str(e)}")
                    continue

            db.commit()

        logger.info(f"💰 Odds sync completed: {odds_count} odds processed")
        return odds_count

    def _extract_best_odds(self, odds_data: List[Dict]) -> Optional[Dict]:
        """
        Extrai as melhores odds dos dados retornados pela API-Football.
        Retorna um dicionário com as odds principais + nome da bookmaker.
        """
        try:
            if not odds_data or len(odds_data) == 0:
                return None

            # Pegar a primeira casa de apostas (geralmente é uma das principais)
            first_bookmaker = odds_data[0]
            bookmaker = first_bookmaker.get('bookmakers', [])

            if not bookmaker or len(bookmaker) == 0:
                return None

            # Extrair nome da bookmaker
            bookmaker_name = bookmaker[0].get('name', 'API-Football')

            # Pegar os valores (bets)
            bets = bookmaker[0].get('bets', [])

            result = {
                'bookmaker_name': bookmaker_name  # Adicionar nome da bookmaker
            }

            for bet in bets:
                bet_name = bet.get('name', '')
                values = bet.get('values', [])

                # Match Winner (1X2)
                if bet_name == 'Match Winner':
                    for value in values:
                        label = value.get('value', '')
                        odd = float(value.get('odd', 2.0))

                        if label == 'Home':
                            result['home_win'] = odd
                        elif label == 'Draw':
                            result['draw'] = odd
                        elif label == 'Away':
                            result['away_win'] = odd

                # Goals Over/Under
                elif bet_name == 'Goals Over/Under':
                    for value in values:
                        label = value.get('value', '')
                        odd = float(value.get('odd', 2.0))

                        if 'Over' in label:
                            result['over_2_5'] = odd
                        elif 'Under' in label:
                            result['under_2_5'] = odd

                # Both Teams Score
                elif bet_name == 'Both Teams Score' or bet_name == 'BTTS':
                    for value in values:
                        label = value.get('value', '')
                        odd = float(value.get('odd', 2.0))

                        if label == 'Yes':
                            result['btts_yes'] = odd
                        elif label == 'No':
                            result['btts_no'] = odd

            # Validação: pelo menos precisa ter home, draw, away
            if 'home_win' in result and 'draw' in result and 'away_win' in result:
                return result

            return None

        except Exception as e:
            logger.error(f"Erro ao extrair odds: {e}")
            return None

    async def _sync_predictions(self) -> int:
        """Generate predictions for matches without predictions"""
        logger.info("🔮 Syncing predictions...")

        predictions_count = 0

        with get_db_session() as db:
            # Get matches that need predictions
            matches_needing_predictions = db.query(Match).filter(
                Match.match_date > datetime.now(),
                Match.is_predicted == False,
                Match.status == "SCHEDULED"
            ).limit(50).all()  # Limit to avoid overload

            for match in matches_needing_predictions:
                try:
                    # Generate prediction using integrated prediction service
                    prediction_result = await prediction_integration.predict_match(
                        match_id=match.id,
                        home_team_id=match.home_team_id,
                        away_team_id=match.away_team_id
                    )

                    if prediction_result and prediction_result.get("success"):
                        match.is_predicted = True
                        match.confidence_score = prediction_result.get("confidence", 0.5)
                        predictions_count += 1

                        logger.info(f"✅ Generated prediction for {match.home_team.name} vs {match.away_team.name} (confidence: {match.confidence_score:.2f})")

                except Exception as e:
                    logger.error(f"❌ Failed to generate prediction for match {match.id}: {str(e)}")
                    continue

            db.commit()

        logger.info(f"🔮 Predictions sync completed: {predictions_count} predictions generated")
        return predictions_count

    async def _update_live_matches(self) -> int:
        """Update live match data (scores, status, minute)"""
        live_updates = 0

        with get_db_session() as db:
            # Get today's matches
            today = datetime.now().date()
            live_matches = db.query(Match).filter(
                Match.match_date >= today,
                Match.match_date < today + timedelta(days=1),
                Match.status.in_(["LIVE", "IN_PLAY", "PAUSED"])
            ).all()

            logger.info(f"🔴 Checking {len(live_matches)} live matches for updates...")

            for match in live_matches:
                try:
                    # Get updated match data
                    match_details = await self.football_service.get_match_details(match.external_id)

                    if match_details:
                        old_status = match.status
                        new_status = self._map_match_status(match_details["status"])

                        # Update match status and scores
                        score = match_details.get("score", {})
                        full_time = score.get("fullTime", {})

                        match.status = new_status
                        match.home_score = full_time.get("home")
                        match.away_score = full_time.get("away")

                        # Log status changes (especially LIVE → FT)
                        if old_status != new_status:
                            logger.info(
                                f"  ⚽ Match {match.id} status changed: {old_status} → {new_status} "
                                f"({match.home_team.name if match.home_team else 'Unknown'} vs "
                                f"{match.away_team.name if match.away_team else 'Unknown'}) "
                                f"Score: {match.home_score}-{match.away_score}"
                            )

                        # Try to estimate current minute for live matches
                        if match.status == "LIVE":
                            match.minute = self._estimate_match_minute(match_details)

                        live_updates += 1

                except Exception as e:
                    logger.error(f"❌ Failed to update live match {match.id}: {str(e)}")
                    continue

            db.commit()

            if live_updates > 0:
                logger.info(f"✅ Updated {live_updates} live matches")

        return live_updates

    async def _update_live_odds(self) -> int:
        """Update odds for today's matches"""
        odds_updates = 0

        with get_db_session() as db:
            today = datetime.now().date()
            today_matches = db.query(Match).filter(
                Match.match_date >= today,
                Match.match_date < today + timedelta(days=1),
                Match.status == "SCHEDULED"
            ).all()

            for match in today_matches:
                try:
                    odds_data = await self.odds_service.get_match_odds(
                        home_team=match.home_team.name,
                        away_team=match.away_team.name,
                        match_date=match.match_date
                    )

                    if odds_data:
                        existing_odds = db.query(Odds).filter(
                            Odds.match_id == match.id
                        ).first()

                        if existing_odds:
                            existing_odds.home_win = odds_data.get("home_win", existing_odds.home_win)
                            existing_odds.draw = odds_data.get("draw", existing_odds.draw)
                            existing_odds.away_win = odds_data.get("away_win", existing_odds.away_win)
                            odds_updates += 1

                except Exception as e:
                    logger.error(f"❌ Failed to update odds for match {match.id}: {str(e)}")
                    continue

            db.commit()

        return odds_updates

    def _map_match_status(self, api_status: str) -> str:
        """Map API status to internal status"""
        status_mapping = {
            "SCHEDULED": "SCHEDULED",
            "TIMED": "SCHEDULED",
            "IN_PLAY": "LIVE",
            "PAUSED": "LIVE",
            "FINISHED": "FINISHED",
            "POSTPONED": "POSTPONED",
            "SUSPENDED": "POSTPONED",
            "CANCELLED": "CANCELLED"
        }

        return status_mapping.get(api_status, "SCHEDULED")

    def _estimate_match_minute(self, match_data: Dict) -> Optional[int]:
        """Estimate current match minute for live games"""
        try:
            match_date = datetime.fromisoformat(match_data["utcDate"].replace("Z", "+00:00"))
            now = datetime.now(match_date.tzinfo)
            elapsed_minutes = int((now - match_date).total_seconds() / 60)

            # Basic estimation (doesn't account for stoppage time, half-time break)
            if elapsed_minutes <= 45:
                return elapsed_minutes
            elif elapsed_minutes <= 60:  # Half-time break
                return 45
            elif elapsed_minutes <= 105:  # Second half
                return 45 + (elapsed_minutes - 60)
            else:
                return 90  # Full time

        except:
            return None

    async def health_check(self) -> Dict[str, any]:
        """Check the health of all external services"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "healthy"
        }

        # Check Football Data API
        try:
            football_health = await self.football_service.get_competitions()
            health_status["services"]["football_data"] = {
                "status": "healthy",
                "response_time": "< 1s"
            }
        except Exception as e:
            health_status["services"]["football_data"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"

        # Check Odds API
        try:
            await self.odds_service.get_available_sports()
            health_status["services"]["odds_api"] = {
                "status": "healthy",
                "response_time": "< 1s"
            }
        except Exception as e:
            health_status["services"]["odds_api"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"

        # Check Redis
        try:
            await redis_client.ping()
            health_status["services"]["redis"] = {
                "status": "healthy"
            }
        except Exception as e:
            health_status["services"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "unhealthy"

        return health_status

# Global instance
data_synchronizer = DataSynchronizer()