"""
🌍 SISTEMA GLOBAL DE ANÁLISE DE FUTEBOL
Sistema escalável para monitorar e analisar TODAS as ligas e jogos mundiais

Funcionalidades:
1. Descoberta automática de jogos de todas as ligas
2. Geração de previsões para todos os mercados
3. Monitoramento em tempo real de jogos ao vivo
4. Sistema de retreino automático baseado em resultados
5. Pipeline de dados para múltiplas fontes
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.football_data_service import FootballDataService
from app.services.prediction_service import PredictionService
import httpx

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class League:
    """Definição de uma liga"""
    id: str
    name: str
    country: str
    api_code: str
    tier: int = 1  # 1 = Principal, 2 = Segunda divisão, etc.
    active: bool = True
    season_start: Optional[str] = None
    season_end: Optional[str] = None

@dataclass
class Match:
    """Definição de uma partida"""
    id: str
    external_id: str
    home_team_id: str
    home_team_name: str
    away_team_id: str
    away_team_name: str
    league_id: str
    league_name: str
    match_date: datetime
    status: str
    venue: Optional[str] = None
    predictions_generated: bool = False
    monitoring_active: bool = False
    results_collected: bool = False

@dataclass
class LiveMatchData:
    """Dados de uma partida ao vivo"""
    match_id: str
    minute: int
    status: str
    home_score: int
    away_score: int
    stats: Dict = field(default_factory=dict)
    events: List = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

class GlobalMatchSystem:
    """Sistema global para gerenciamento de partidas"""

    def __init__(self):
        self.supported_leagues = self._initialize_leagues()
        self.active_matches: Dict[str, Match] = {}
        self.live_matches: Dict[str, LiveMatchData] = {}
        self.prediction_service = None
        self.football_service = FootballDataService()

    def _initialize_leagues(self) -> List[League]:
        """Inicializa lista de ligas suportadas"""
        return [
            # Principais Ligas Europeias
            League("PL", "Premier League", "England", "PL", 1),
            League("PD", "La Liga", "Spain", "PD", 1),
            League("BL1", "Bundesliga", "Germany", "BL1", 1),
            League("SA", "Serie A", "Italy", "SA", 1),
            League("FL1", "Ligue 1", "France", "FL1", 1),
            League("PPL", "Primeira Liga", "Portugal", "PPL", 1),
            League("DED", "Eredivisie", "Netherlands", "DED", 1),

            # Competições Internacionais
            League("CL", "Champions League", "Europe", "CL", 1),
            League("EL", "Europa League", "Europe", "EL", 1),
            League("WC", "World Cup", "World", "WC", 1),
            League("EC", "European Championship", "Europe", "EC", 1),

            # América do Sul
            League("CLI", "Copa Libertadores", "South America", "CLI", 1),
            League("CSA", "Copa Sudamericana", "South America", "CSA", 1),
            League("BSA", "Brasileirão Série A", "Brazil", "BSA", 1),
            League("ASA", "Primera División Argentina", "Argentina", "ASA", 1),

            # América do Norte
            League("MLS", "Major League Soccer", "USA", "MLS", 1),
            League("LMX", "Liga MX", "Mexico", "LMX", 1),

            # Outras Ligas Importantes
            League("CSL", "Chinese Super League", "China", "CSL", 2),
            League("J1", "J1 League", "Japan", "J1", 2),
            League("KL1", "K League 1", "South Korea", "KL1", 2),
        ]

    async def discover_matches_globally(self, days_ahead: int = 7) -> List[Match]:
        """Descobre jogos de todas as ligas nos próximos N dias"""
        logger.info(f"🔍 Descobrindo jogos globalmente - próximos {days_ahead} dias")

        all_matches = []
        date_from = datetime.now().strftime("%Y-%m-%d")
        date_to = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        for league in self.supported_leagues:
            if not league.active:
                continue

            try:
                logger.info(f"📡 Buscando jogos: {league.name} ({league.country})")

                league_matches = await self.football_service.get_matches_by_competition(
                    league.api_code, date_from, date_to
                )

                for match_data in league_matches:
                    match = self._parse_match_data(match_data, league)
                    if match:
                        all_matches.append(match)
                        self.active_matches[match.id] = match

                logger.info(f"✅ {league.name}: {len(league_matches)} jogos encontrados")

            except Exception as e:
                logger.warning(f"⚠️ Erro ao buscar {league.name}: {e}")
                continue

        logger.info(f"🎯 Total descoberto: {len(all_matches)} jogos em {len(self.supported_leagues)} ligas")
        return all_matches

    def _parse_match_data(self, match_data: Dict, league: League) -> Optional[Match]:
        """Converte dados da API em objeto Match"""
        try:
            return Match(
                id=f"{league.id}_{match_data.get('id', 'unknown')}",
                external_id=str(match_data.get('id', '')),
                home_team_id=str(match_data.get('homeTeam', {}).get('id', '')),
                home_team_name=match_data.get('homeTeam', {}).get('name', 'TBD'),
                away_team_id=str(match_data.get('awayTeam', {}).get('id', '')),
                away_team_name=match_data.get('awayTeam', {}).get('name', 'TBD'),
                league_id=league.id,
                league_name=league.name,
                match_date=datetime.fromisoformat(match_data.get('utcDate', '').replace('Z', '+00:00')),
                status=match_data.get('status', 'SCHEDULED'),
                venue=match_data.get('venue', {}).get('name') if match_data.get('venue') else None
            )
        except Exception as e:
            logger.error(f"❌ Erro ao parsear jogo: {e}")
            return None

    async def generate_predictions_for_all_matches(self, target_date: Optional[datetime] = None) -> Dict[str, Dict]:
        """Gera previsões para todos os jogos de um dia"""
        if not target_date:
            target_date = datetime.now()

        logger.info(f"🧠 Gerando previsões para {target_date.strftime('%Y-%m-%d')}")

        # Filtrar jogos do dia
        day_matches = [
            match for match in self.active_matches.values()
            if match.match_date.date() == target_date.date()
            and not match.predictions_generated
            and match.status in ['SCHEDULED', 'TIMED']
        ]

        if not day_matches:
            logger.info("📭 Nenhum jogo encontrado para o dia especificado")
            return {}

        logger.info(f"🎯 {len(day_matches)} jogos para análise")

        all_predictions = {}
        prediction_service = PredictionService(next(get_db()))

        for match in day_matches:
            try:
                logger.info(f"⚽ Analisando: {match.home_team_name} vs {match.away_team_name} ({match.league_name})")

                # Gerar previsão usando o motor real
                prediction = await prediction_service.real_engine.generate_real_prediction(
                    match_id=match.external_id,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    match_date=match.match_date,
                    venue=match.venue
                )

                # Expandir para todos os mercados
                comprehensive_prediction = self._expand_to_all_markets(prediction, match)

                all_predictions[match.id] = {
                    'match_info': {
                        'home_team': match.home_team_name,
                        'away_team': match.away_team_name,
                        'league': match.league_name,
                        'date': match.match_date.isoformat(),
                        'venue': match.venue
                    },
                    'predictions': comprehensive_prediction,
                    'generated_at': datetime.now().isoformat()
                }

                # Marcar como processado
                match.predictions_generated = True
                logger.info(f"✅ Previsão gerada: {match.home_team_name} vs {match.away_team_name}")

            except Exception as e:
                logger.error(f"❌ Erro na previsão {match.home_team_name} vs {match.away_team_name}: {e}")
                continue

        # Salvar todas as previsões
        await self._save_daily_predictions(target_date, all_predictions)

        logger.info(f"🎉 Processamento concluído: {len(all_predictions)} previsões geradas")
        return all_predictions

    def _expand_to_all_markets(self, base_prediction: Dict, match: Match) -> Dict:
        """Expande previsão base para todos os mercados disponíveis"""

        # Extrair probabilidades base
        outcome = base_prediction.get('match_outcome', {})
        goals = base_prediction.get('goals_prediction', {})
        btts = base_prediction.get('btts_prediction', {})
        corners = base_prediction.get('corners_prediction', {})

        home_prob = outcome.get('home_win_probability', 0.33)
        draw_prob = outcome.get('draw_probability', 0.33)
        away_prob = outcome.get('away_win_probability', 0.33)

        return {
            # Mercados principais
            '1x2': {
                'home_win': home_prob,
                'draw': draw_prob,
                'away_win': away_prob,
                'prediction': 'home' if home_prob > max(draw_prob, away_prob) else 'away' if away_prob > draw_prob else 'draw'
            },

            'over_under_goals': {
                'total_expected': goals.get('expected_total_goals', 2.5),
                'over_1_5': goals.get('over_1_5_probability', 0.7),
                'under_1_5': goals.get('under_1_5_probability', 0.3),
                'over_2_5': goals.get('over_2_5_probability', 0.5),
                'under_2_5': goals.get('under_2_5_probability', 0.5),
                'over_3_5': goals.get('over_3_5_probability', 0.3),
                'under_3_5': goals.get('under_3_5_probability', 0.7)
            },

            'both_teams_score': {
                'yes': btts.get('btts_yes_probability', 0.5),
                'no': btts.get('btts_no_probability', 0.5),
                'prediction': btts.get('predicted_outcome', 'No')
            },

            'asian_handicap': {
                'home_plus_0_5': home_prob + (away_prob - home_prob) * 0.3,
                'away_minus_0_5': away_prob - (away_prob - home_prob) * 0.2,
                'draw_no_bet_home': home_prob / (home_prob + away_prob),
                'draw_no_bet_away': away_prob / (home_prob + away_prob)
            },

            'corners': {
                'total_expected': corners.get('expected_total_corners', 10),
                'over_8_5': corners.get('over_8_5_probability', 0.7),
                'over_9_5': corners.get('over_9_5_probability', 0.6),
                'over_10_5': corners.get('over_10_5_probability', 0.5)
            },

            'cards': self._estimate_cards_market(match),

            'double_chance': {
                '1x': home_prob + draw_prob,
                'x2': draw_prob + away_prob,
                '12': home_prob + away_prob
            },

            'correct_score': self._estimate_correct_scores(
                goals.get('expected_home_goals', 1.2),
                goals.get('expected_away_goals', 1.3)
            ),

            # Metadados
            'confidence_overall': outcome.get('confidence', 0.5),
            'data_quality': base_prediction.get('confidence_system', {}).get('overall_confidence', 0.5),
            'league_tier': next((l.tier for l in self.supported_leagues if l.id == match.league_id), 1)
        }

    def _estimate_cards_market(self, match: Match) -> Dict:
        """Estima mercado de cartões baseado na liga e tipo de jogo"""

        # Fatores por liga
        league_factors = {
            'CLI': 5.2,  # Copa Libertadores - muito agressiva
            'CSA': 4.8,  # Copa Sul-Americana
            'CL': 4.0,   # Champions League
            'PL': 3.8,   # Premier League
            'PD': 4.2,   # La Liga
            'SA': 4.5,   # Serie A
            'BL1': 3.5,  # Bundesliga
            'FL1': 3.9,  # Ligue 1
        }

        expected_cards = league_factors.get(match.league_id, 4.0)

        return {
            'total_expected': expected_cards,
            'over_3_5': 0.72 if expected_cards > 4.5 else 0.58,
            'over_4_5': 0.58 if expected_cards > 4.5 else 0.42,
            'over_5_5': 0.41 if expected_cards > 4.5 else 0.28,
            'factors': [f"Liga: {match.league_name}", f"Expectativa: {expected_cards} cartões"]
        }

    def _estimate_correct_scores(self, home_xg: float, away_xg: float) -> Dict:
        """Estima placares mais prováveis usando distribuição de Poisson"""
        import math

        def poisson_prob(k: int, lam: float) -> float:
            return (lam ** k) * math.exp(-lam) / math.factorial(k)

        scores = {}

        # Calcular probabilidades para placares até 4x4
        for home_goals in range(5):
            for away_goals in range(5):
                prob = poisson_prob(home_goals, home_xg) * poisson_prob(away_goals, away_xg)
                score_key = f"{home_goals}-{away_goals}"
                scores[score_key] = round(prob, 4)

        # Retornar os 6 mais prováveis
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:6]

        return {
            'most_likely': dict(sorted_scores),
            'home_xg': home_xg,
            'away_xg': away_xg
        }

    async def monitor_live_matches_globally(self) -> None:
        """Monitor global de jogos ao vivo"""
        logger.info("🔴 Iniciando monitoramento global de jogos ao vivo")

        while True:
            try:
                # Buscar jogos que estão acontecendo agora
                live_matches = [
                    match for match in self.active_matches.values()
                    if match.status in ['IN_PLAY', 'PAUSED', 'LIVE']
                    and not match.results_collected
                ]

                if not live_matches:
                    logger.info("⏸️ Nenhum jogo ao vivo no momento")
                    await asyncio.sleep(60)  # Aguardar 1 minuto
                    continue

                logger.info(f"🔴 {len(live_matches)} jogos sendo monitorados ao vivo")

                # Monitorar cada jogo
                for match in live_matches:
                    await self._monitor_single_match(match)

                # Aguardar 30 segundos antes da próxima rodada
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"❌ Erro no monitoramento global: {e}")
                await asyncio.sleep(60)

    async def _monitor_single_match(self, match: Match) -> None:
        """Monitora uma partida específica"""
        try:
            # Buscar dados ao vivo
            live_data = await self._fetch_live_match_data(match)

            if not live_data:
                return

            # Atualizar dados do jogo ao vivo
            self.live_matches[match.id] = live_data

            # Se jogo terminou, coletar resultados finais
            if live_data.status in ['FINISHED', 'FULL_TIME']:
                await self._collect_final_results(match, live_data)
                match.results_collected = True

        except Exception as e:
            logger.error(f"❌ Erro ao monitorar {match.home_team_name} vs {match.away_team_name}: {e}")

    async def _fetch_live_match_data(self, match: Match) -> Optional[LiveMatchData]:
        """Busca dados ao vivo de uma partida"""
        try:
            match_data = await self.football_service.get_match_details(match.external_id)

            if not match_data:
                return None

            return LiveMatchData(
                match_id=match.id,
                minute=match_data.get('minute', 0),
                status=match_data.get('status', 'UNKNOWN'),
                home_score=match_data.get('score', {}).get('fullTime', {}).get('home', 0),
                away_score=match_data.get('score', {}).get('fullTime', {}).get('away', 0),
                stats=match_data.get('stats', {}),
                events=match_data.get('events', [])
            )

        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados ao vivo: {e}")
            return None

    async def _collect_final_results(self, match: Match, live_data: LiveMatchData) -> None:
        """Coleta resultados finais e prepara para retreino"""
        logger.info(f"🏁 Coletando resultados finais: {match.home_team_name} vs {match.away_team_name}")

        # Calcular resultados de todos os mercados
        final_results = self._calculate_all_market_results(live_data)

        # Salvar para retreino
        await self._save_results_for_retraining(match, final_results)

        logger.info(f"✅ Resultados coletados: {match.home_team_name} {live_data.home_score}-{live_data.away_score} {match.away_team_name}")

    def _calculate_all_market_results(self, live_data: LiveMatchData) -> Dict:
        """Calcula resultados reais de todos os mercados"""
        home_score = live_data.home_score
        away_score = live_data.away_score
        total_goals = home_score + away_score

        return {
            # Resultado 1X2
            'match_result': 'home' if home_score > away_score else ('away' if away_score > home_score else 'draw'),

            # Gols
            'total_goals': total_goals,
            'over_1_5': total_goals > 1.5,
            'over_2_5': total_goals > 2.5,
            'over_3_5': total_goals > 3.5,

            # BTTS
            'btts': home_score > 0 and away_score > 0,

            # Outros mercados
            'home_scored': home_score > 0,
            'away_scored': away_score > 0,
            'clean_sheet_home': away_score == 0,
            'clean_sheet_away': home_score == 0,

            # Dupla chance
            '1x': home_score >= away_score,
            'x2': away_score >= home_score,
            '12': home_score != away_score,

            # Placar exato
            'correct_score': f"{home_score}-{away_score}",

            # Estatísticas (se disponíveis)
            'corners_total': live_data.stats.get('corners_total', 0),
            'cards_total': live_data.stats.get('cards_total', 0),

            # Metadados
            'final_minute': live_data.minute,
            'match_events': len(live_data.events)
        }

    async def _save_daily_predictions(self, date: datetime, predictions: Dict) -> None:
        """Salva previsões diárias em arquivo"""
        filename = f"daily_predictions_{date.strftime('%Y%m%d')}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Previsões salvas: {filename}")

    async def _save_results_for_retraining(self, match: Match, results: Dict) -> None:
        """Salva resultados para retreino automático"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"match_results_{match.league_id}_{timestamp}.json"

        retraining_data = {
            'match_info': {
                'id': match.id,
                'home_team': match.home_team_name,
                'away_team': match.away_team_name,
                'league': match.league_name,
                'date': match.match_date.isoformat()
            },
            'final_results': results,
            'collected_at': datetime.now().isoformat()
        }

        with open(f"retraining_data/{filename}", 'w', encoding='utf-8') as f:
            json.dump(retraining_data, f, indent=2, ensure_ascii=False)

        logger.info(f"🔄 Dados de retreino salvos: {filename}")

    async def get_system_status(self) -> Dict:
        """Retorna status completo do sistema"""
        active_count = len([m for m in self.active_matches.values() if m.status != 'FINISHED'])
        live_count = len(self.live_matches)
        predictions_count = len([m for m in self.active_matches.values() if m.predictions_generated])

        return {
            'system_status': 'operational',
            'supported_leagues': len(self.supported_leagues),
            'active_matches': active_count,
            'live_matches': live_count,
            'predictions_generated': predictions_count,
            'leagues': [
                {
                    'id': league.id,
                    'name': league.name,
                    'country': league.country,
                    'tier': league.tier,
                    'active': league.active
                }
                for league in self.supported_leagues if league.active
            ],
            'last_updated': datetime.now().isoformat()
        }

# Instância global do sistema
global_match_system = GlobalMatchSystem()

async def run_daily_analysis():
    """Executa análise diária completa"""
    logger.info("🌍 Iniciando análise diária global")

    # 1. Descobrir jogos
    matches = await global_match_system.discover_matches_globally()

    # 2. Gerar previsões
    predictions = await global_match_system.generate_predictions_for_all_matches()

    # 3. Status do sistema
    status = await global_match_system.get_system_status()

    logger.info(f"📊 Análise concluída: {len(matches)} jogos, {len(predictions)} previsões")
    return {'matches': len(matches), 'predictions': len(predictions), 'status': status}

async def start_global_monitoring():
    """Inicia monitoramento global contínuo"""
    logger.info("🔴 Iniciando monitoramento global contínuo")
    await global_match_system.monitor_live_matches_globally()

if __name__ == "__main__":
    # Para teste
    import asyncio
    asyncio.run(run_daily_analysis())