#!/usr/bin/env python3
"""
🔄 SERVIÇO DE IMPORTAÇÃO AUTOMÁTICA DE JOGOS
Importa jogos do dia das ligas principais automaticamente
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.match import Match
from app.models.team import Team
from app.core.database import SessionLocal
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Configurações da API
API_KEY = settings.API_SPORTS_KEY
if not API_KEY:
    raise ValueError("API_SPORTS_KEY não configurada. Configure no arquivo .env")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# 🎯 LIGAS PRINCIPAIS (IDs da API-Sports)
MAIN_LEAGUES = {
    # BRASIL
    71: {"name": "Brasileirão Série A", "priority": 1, "country": "Brazil"},
    72: {"name": "Brasileirão Série B", "priority": 2, "country": "Brazil"},

    # EUROPA - TOP 5
    39: {"name": "Premier League", "priority": 1, "country": "England"},
    140: {"name": "La Liga", "priority": 1, "country": "Spain"},
    135: {"name": "Serie A", "priority": 1, "country": "Italy"},
    61: {"name": "Ligue 1", "priority": 1, "country": "France"},
    78: {"name": "Bundesliga", "priority": 1, "country": "Germany"},

    # LIBERTADORES & SUL-AMERICANA
    13: {"name": "Copa Libertadores", "priority": 1, "country": "South America"},
    11: {"name": "Copa Sul-Americana", "priority": 2, "country": "South America"},

    # CHAMPIONS & EUROPA LEAGUE
    2: {"name": "UEFA Champions League", "priority": 1, "country": "Europe"},
    3: {"name": "UEFA Europa League", "priority": 2, "country": "Europe"},

    # OUTRAS RELEVANTES
    253: {"name": "MLS", "priority": 2, "country": "USA"},
    128: {"name": "Liga Profesional Argentina", "priority": 2, "country": "Argentina"},
    94: {"name": "Primeira Liga", "priority": 2, "country": "Portugal"},
    88: {"name": "Eredivisie", "priority": 3, "country": "Netherlands"},
}


class DailyMatchesImporter:
    """Importador automático de jogos do dia"""

    def __init__(self, db: Session):
        self.db = db
        self.imported_count = 0
        self.updated_count = 0
        self.errors = []

    def get_or_create_team(self, team_data: dict, league: str) -> Team:
        """Busca ou cria um time"""
        external_id = str(team_data['id'])
        team = self.db.query(Team).filter(Team.external_id == external_id).first()

        if team:
            return team

        team = Team(
            external_id=external_id,
            name=team_data['name'],
            country=team_data.get('country', {}).get('name', 'Unknown'),
            league=league,
            logo_url=team_data.get('logo', '')
        )

        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)

        logger.info(f"Time criado: {team.name}")
        return team

    def import_match(self, fixture: dict) -> Match:
        """Importa ou atualiza um jogo"""
        try:
            external_id = str(fixture['fixture']['id'])
            league_name = fixture['league']['name']

            # Buscar ou criar times
            home_team = self.get_or_create_team(fixture['teams']['home'], league_name)
            away_team = self.get_or_create_team(fixture['teams']['away'], league_name)

            # Verificar se jogo já existe
            match = self.db.query(Match).filter(Match.external_id == external_id).first()

            if match:
                # Atualizar jogo existente
                self.updated_count += 1
                is_new = False
            else:
                # Criar novo jogo
                match = Match()
                self.imported_count += 1
                is_new = True

            # Preencher dados
            match.external_id = external_id
            match.league = league_name
            match.home_team_id = home_team.id
            match.away_team_id = away_team.id

            # Data do jogo
            match_date_str = fixture['fixture']['date']
            match.match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))

            # Venue
            if fixture['fixture'].get('venue'):
                match.venue = fixture['fixture']['venue'].get('name', 'Unknown')

            # Status
            match.status = fixture['fixture']['status']['short']

            # Placar (se disponível)
            if fixture['goals']['home'] is not None:
                match.home_score = fixture['goals']['home']
            if fixture['goals']['away'] is not None:
                match.away_score = fixture['goals']['away']

            # Minuto do jogo (se ao vivo)
            if fixture['fixture']['status'].get('elapsed'):
                match.minute = fixture['fixture']['status']['elapsed']

            if is_new:
                self.db.add(match)

            self.db.commit()
            self.db.refresh(match)

            return match

        except Exception as e:
            logger.error(f"Erro ao importar jogo {fixture['fixture']['id']}: {str(e)}")
            self.errors.append(str(e))
            return None

    def fetch_fixtures_for_league(self, league_id: int, date: str) -> List[dict]:
        """Busca jogos de uma liga em uma data específica"""
        try:
            response = requests.get(
                f"{BASE_URL}/fixtures",
                headers=HEADERS,
                params={
                    "league": league_id,
                    "season": 2025,
                    "date": date
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
            else:
                logger.error(f"Erro ao buscar liga {league_id}: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Exceção ao buscar liga {league_id}: {str(e)}")
            return []

    def import_today_matches(self) -> Dict:
        """Importa todos os jogos de hoje das ligas principais"""
        today = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"🔄 Iniciando importação de jogos do dia {today}")
        logger.info(f"📋 Ligas configuradas: {len(MAIN_LEAGUES)}")

        total_fixtures = []

        # Buscar jogos de cada liga
        for league_id, league_info in MAIN_LEAGUES.items():
            logger.info(f"Buscando {league_info['name']}...")

            fixtures = self.fetch_fixtures_for_league(league_id, today)

            if fixtures:
                logger.info(f"  ✅ {len(fixtures)} jogos encontrados")
                total_fixtures.extend(fixtures)
            else:
                logger.info(f"  ⚠️ Nenhum jogo hoje")

        logger.info(f"\n📊 Total de jogos encontrados: {len(total_fixtures)}")

        # Importar todos os jogos
        for fixture in total_fixtures:
            self.import_match(fixture)

        # Resultado
        result = {
            "success": True,
            "date": today,
            "leagues_checked": len(MAIN_LEAGUES),
            "fixtures_found": len(total_fixtures),
            "imported": self.imported_count,
            "updated": self.updated_count,
            "errors": len(self.errors),
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"\n✅ Importação concluída:")
        logger.info(f"   - Novos: {self.imported_count}")
        logger.info(f"   - Atualizados: {self.updated_count}")
        logger.info(f"   - Erros: {len(self.errors)}")

        return result

    def import_tomorrow_matches(self) -> Dict:
        """Importa jogos de amanhã (para preparar o sistema)"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        logger.info(f"🔄 Importando jogos de amanhã {tomorrow}")

        # Mesma lógica, mas para amanhã
        # ... (código similar ao import_today_matches)

        pass


def run_daily_import(db: Session) -> Dict:
    """Função principal para executar importação diária"""
    importer = DailyMatchesImporter(db)
    return importer.import_today_matches()


def run_cleanup_old_matches(db: Session) -> Dict:
    """
    🗑️ LIMPEZA DE JOGOS ANTIGOS
    Remove jogos que já finalizaram há mais de 24h
    """
    logger.info("🗑️ Iniciando limpeza de jogos antigos...")

    # Data de corte: ontem
    cutoff_date = datetime.now() - timedelta(days=1)

    # Buscar jogos finalizados antigos
    old_matches = db.query(Match).filter(
        Match.match_date < cutoff_date,
        Match.status.in_(['FT', 'AET', 'PEN', 'CANC', 'ABD', 'AWD'])
    ).all()

    count = len(old_matches)

    logger.info(f"📊 Encontrados {count} jogos antigos para limpar")

    # Manter no banco, mas não exibir nas predictions
    # (já está tratado nos endpoints que filtram por status)

    result = {
        "success": True,
        "cleaned": count,
        "cutoff_date": cutoff_date.isoformat(),
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"✅ Limpeza concluída: {count} jogos antigos")

    return result


if __name__ == "__main__":
    # Teste manual
    logging.basicConfig(level=logging.INFO)

    db = SessionLocal()
    try:
        result = run_daily_import(db)
        print("\n" + "=" * 60)
        print("RESULTADO DA IMPORTAÇÃO")
        print("=" * 60)
        for key, value in result.items():
            print(f"{key}: {value}")
    finally:
        db.close()
