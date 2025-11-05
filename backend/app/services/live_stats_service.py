#!/usr/bin/env python3
"""
🔴 SERVIÇO DE ESTATÍSTICAS AO VIVO

Busca e atualiza estatísticas de jogos em tempo real da API
"""
import requests
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app.models import Match
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# API-Sports PRO
API_KEY = settings.API_SPORTS_KEY
if not API_KEY:
    raise ValueError("API_SPORTS_KEY não configurada. Configure no arquivo .env")
BASE_URL = 'https://v3.football.api-sports.io'
HEADERS = {'x-apisports-key': API_KEY}


class LiveStatsService:
    """Gerencia estatísticas ao vivo dos jogos"""

    def __init__(self, db: Session):
        self.db = db

    def get_live_matches(self) -> List[Dict]:
        """
        Busca todos os jogos ao vivo com estatísticas

        Returns:
            List de dicts com dados dos jogos ao vivo
        """
        # Buscar jogos com status LIVE do banco
        live_matches = self.db.query(Match).filter(
            Match.status.in_(['LIVE', 'HT', '1H', '2H'])
        ).all()

        logger.info(f"🔴 Encontrados {len(live_matches)} jogos ao vivo no banco")

        results = []
        for match in live_matches:
            if match.external_id and match.external_id.isdigit():
                live_data = self._fetch_live_stats(match.external_id)

                if live_data:
                    results.append({
                        'match_id': match.id,
                        'external_id': match.external_id,
                        'home_team': match.home_team,
                        'away_team': match.away_team,
                        'league': match.league,
                        'status': live_data['status'],
                        'elapsed': live_data['elapsed'],
                        'score': live_data['score'],
                        'statistics': live_data.get('statistics', {}),
                        'events': live_data.get('events', [])
                    })

        return results

    def _fetch_live_stats(self, fixture_id: str) -> Optional[Dict]:
        """
        Busca estatísticas ao vivo de um jogo específico

        Args:
            fixture_id: ID do jogo na API-Sports

        Returns:
            Dict com status, placar, estatísticas e eventos
        """
        try:
            # Buscar dados do jogo
            url = f"{BASE_URL}/fixtures"
            params = {'id': fixture_id}
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()

            fixture_data = response.json()

            if not fixture_data['response']:
                return None

            fixture = fixture_data['response'][0]

            # Buscar estatísticas
            stats_url = f"{BASE_URL}/fixtures/statistics"
            stats_response = requests.get(stats_url, headers=HEADERS, params=params, timeout=10)
            stats_response.raise_for_status()
            stats_data = stats_response.json()

            # Buscar eventos (gols, cartões, etc)
            events_url = f"{BASE_URL}/fixtures/events"
            events_response = requests.get(events_url, headers=HEADERS, params=params, timeout=10)
            events_response.raise_for_status()
            events_data = events_response.json()

            # Processar estatísticas
            statistics = {}
            if stats_data['response']:
                for team_stats in stats_data['response']:
                    team_name = team_stats['team']['name']
                    stats_dict = {}

                    for stat in team_stats['statistics']:
                        stats_dict[stat['type']] = stat['value']

                    statistics[team_name] = stats_dict

            # Processar eventos
            events = []
            if events_data['response']:
                for event in events_data['response'][:10]:  # Últimos 10 eventos
                    events.append({
                        'time': event['time']['elapsed'],
                        'team': event['team']['name'],
                        'player': event['player']['name'] if event.get('player') else 'N/A',
                        'type': event['type'],
                        'detail': event['detail']
                    })

            return {
                'status': fixture['fixture']['status']['short'],
                'elapsed': fixture['fixture']['status']['elapsed'],
                'score': {
                    'home': fixture['goals']['home'],
                    'away': fixture['goals']['away']
                },
                'statistics': statistics,
                'events': events
            }

        except Exception as e:
            logger.error(f"Erro ao buscar stats ao vivo fixture {fixture_id}: {e}")
            return None

    def update_live_match_score(self, match_id: int, home_score: int, away_score: int, status: str, elapsed: int):
        """
        Atualiza placar de jogo ao vivo no banco

        Args:
            match_id: ID do match no banco
            home_score: Gols casa
            away_score: Gols fora
            status: Status do jogo (LIVE, HT, etc)
            elapsed: Minutos decorridos
        """
        match = self.db.query(Match).filter(Match.id == match_id).first()

        if match:
            match.home_score = home_score
            match.away_score = away_score
            match.status = status
            # Podemos adicionar um campo elapsed_time se necessário

            self.db.commit()
            logger.info(f"✅ Placar atualizado: {match.home_team} {home_score}-{away_score} {match.away_team} ({elapsed}')")


def get_all_live_matches(db: Session) -> List[Dict]:
    """
    Helper function para buscar jogos ao vivo

    Args:
        db: Session do SQLAlchemy

    Returns:
        Lista de jogos ao vivo com estatísticas
    """
    service = LiveStatsService(db)
    return service.get_live_matches()
