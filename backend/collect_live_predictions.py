#!/usr/bin/env python3
"""
🚀 COLETOR DE DADOS REAIS PARA PREDIÇÕES
Script para coletar dados atuais da API-Sports e gerar predições em tempo real

Funcionalidades:
1. Coleta jogos dos próximos 7 dias
2. Coleta estatísticas dos times
3. Gera predições baseadas em dados reais
4. Salva no banco de dados
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_db
from app.models import Match, Team, Prediction
from app.services.api_football_service import APIFootballService
from app.services.prediction_service import PredictionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LivePredictionCollector:
    """Coletor de dados reais para predições"""

    def __init__(self):
        self.api_service = APIFootballService()
        self.api_service.rate_limit_delay = 0.5  # Rate limit otimizado
        
        # Ligas principais para coleta
        self.leagues = {
            71: 'Brasileirão Série A',
            39: 'Premier League',
            140: 'La Liga',
            78: 'Bundesliga',
            135: 'Serie A',
            61: 'Ligue 1',
            13: 'Copa Libertadores'
        }

    async def collect_upcoming_matches(self, days_ahead: int = 7):
        """Coleta jogos dos próximos dias"""
        logger.info(f"🔍 Coletando jogos dos próximos {days_ahead} dias...")
        
        matches_collected = 0
        today = datetime.now().date()
        start_date = today - timedelta(days=1)  # Incluir ontem também
        end_date = today + timedelta(days=days_ahead)
        
        for league_id, league_name in self.leagues.items():
            try:
                logger.info(f"📊 Coletando {league_name} (ID: {league_id})...")
                
                # Coletar jogos da liga
                matches = await self.api_service.get_fixtures_by_league(
                    league_id=league_id,
                    season=2024,
                    date_from=start_date.strftime('%Y-%m-%d'),
                    date_to=end_date.strftime('%Y-%m-%d')
                )
                
                if matches:
                    logger.info(f"✅ Encontrados {len(matches)} jogos em {league_name}")
                    
                    # Salvar jogos no banco
                    saved_count = await self.save_matches_to_db(matches, league_name)
                    matches_collected += saved_count
                    
                else:
                    logger.info(f"⚠️ Nenhum jogo encontrado em {league_name}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao coletar {league_name}: {e}")
                continue
        
        logger.info(f"🎯 Total de jogos coletados: {matches_collected}")
        return matches_collected

    async def save_matches_to_db(self, matches: list, league_name: str) -> int:
        """Salva jogos no banco de dados"""
        db = next(get_db())
        saved_count = 0
        
        try:
            for match_data in matches:
                try:
                    # Verificar se o jogo já existe
                    existing_match = db.query(Match).filter(
                        Match.external_id == str(match_data.get('fixture', {}).get('id'))
                    ).first()
                    
                    if existing_match:
                        continue
                    
                    # Extrair dados do jogo
                    fixture = match_data.get('fixture', {})
                    teams = match_data.get('teams', {})
                    league = match_data.get('league', {})
                    
                    # Buscar ou criar times
                    home_team = await self.get_or_create_team(
                        teams.get('home', {}), db
                    )
                    away_team = await self.get_or_create_team(
                        teams.get('away', {}), db
                    )
                    
                    # Criar novo jogo
                    new_match = Match(
                        external_id=str(fixture.get('id')),
                        home_team_id=home_team.id if home_team else None,
                        away_team_id=away_team.id if away_team else None,
                        league=league_name,
                        season=league.get('season', 2024),
                        matchday=league.get('round', 'Regular Season - 1'),
                        match_date=datetime.fromisoformat(
                            fixture.get('date', '').replace('Z', '+00:00')
                        ),
                        venue=fixture.get('venue', {}).get('name'),
                        referee=fixture.get('referee'),
                        status=fixture.get('status', {}).get('short', 'NS'),
                        minute=fixture.get('status', {}).get('elapsed'),
                        home_score=teams.get('home', {}).get('goals'),
                        away_score=teams.get('away', {}).get('goals'),
                        home_score_ht=teams.get('home', {}).get('score', {}).get('halftime'),
                        away_score_ht=teams.get('away', {}).get('score', {}).get('halftime'),
                        is_predicted=False
                    )
                    
                    db.add(new_match)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao salvar jogo: {e}")
                    continue
            
            db.commit()
            logger.info(f"💾 Salvos {saved_count} jogos no banco")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar jogos: {e}")
            db.rollback()
        finally:
            db.close()
        
        return saved_count

    async def get_or_create_team(self, team_data: dict, db: Session) -> Team:
        """Busca ou cria um time no banco"""
        if not team_data:
            return None
            
        team_id = team_data.get('id')
        team_name = team_data.get('name')
        
        if not team_id or not team_name:
            return None
        
        # Buscar time existente
        team = db.query(Team).filter(Team.external_id == str(team_id)).first()
        
        if not team:
            # Criar novo time
            team = Team(
                external_id=str(team_id),
                name=team_name,
                country=team_data.get('country', 'Unknown'),
                founded=team_data.get('founded'),
                logo=team_data.get('logo')
            )
            db.add(team)
            db.commit()
            db.refresh(team)
        
        return team

    async def generate_predictions_for_upcoming_matches(self):
        """Gera predições para jogos futuros"""
        logger.info("🤖 Gerando predições para jogos futuros...")
        
        db = next(get_db())
        predictions_generated = 0
        
        try:
            # Buscar jogos futuros sem predições
            upcoming_matches = db.query(Match).filter(
                Match.status.in_(['NS', 'TBD', 'SCHEDULED']),
                Match.is_predicted == False,
                Match.match_date >= datetime.now()
            ).limit(20).all()  # Limitar para não sobrecarregar
            
            logger.info(f"🎯 Encontrados {len(upcoming_matches)} jogos para predição")
            
            for match in upcoming_matches:
                try:
                    # Criar PredictionService com sessão do banco
                    prediction_service = PredictionService(db)
                    
                    # Gerar predição usando o serviço
                    prediction_data = await prediction_service.generate_real_time_prediction(
                        match_id=match.id
                    )
                    
                    if prediction_data:
                        # Criar predição no banco
                        prediction = Prediction(
                            match_id=match.id,
                            prediction_type='SINGLE',
                            market_type='1X2',
                            predicted_outcome=prediction_data.get('predicted_outcome'),
                            predicted_probability=prediction_data.get('confidence_score'),
                            confidence_score=prediction_data.get('confidence_score'),
                            value_score=prediction_data.get('value_score'),
                            kelly_percentage=prediction_data.get('kelly_percentage'),
                            final_recommendation=prediction_data.get('final_recommendation'),
                            analysis_summary=prediction_data.get('reasoning'),
                            key_factors=prediction_data.get('key_factors', {}),
                            predicted_at=datetime.now()
                        )
                        
                        db.add(prediction)
                        
                        # Marcar jogo como predito
                        match.is_predicted = True
                        match.confidence_score = prediction_data.get('confidence_score')
                        
                        predictions_generated += 1
                        
                        logger.info(f"✅ Predição gerada para {match.home_team.name if match.home_team else 'TBD'} vs {match.away_team.name if match.away_team else 'TBD'}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao gerar predição para jogo {match.id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"🎯 Total de predições geradas: {predictions_generated}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar predições: {e}")
            db.rollback()
        finally:
            db.close()
        
        return predictions_generated

    async def run_full_collection(self):
        """Executa coleta completa de dados e predições"""
        logger.info("🚀 Iniciando coleta completa de dados reais...")
        
        start_time = datetime.now()
        
        try:
            # 1. Coletar jogos futuros
            matches_collected = await self.collect_upcoming_matches(days_ahead=7)
            
            # 2. Gerar predições
            predictions_generated = await self.generate_predictions_for_upcoming_matches()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("🎉 Coleta completa finalizada!")
            logger.info(f"📊 Estatísticas:")
            logger.info(f"   - Jogos coletados: {matches_collected}")
            logger.info(f"   - Predições geradas: {predictions_generated}")
            logger.info(f"   - Tempo total: {duration:.2f}s")
            
            return {
                'matches_collected': matches_collected,
                'predictions_generated': predictions_generated,
                'duration_seconds': duration
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na coleta completa: {e}")
            return None

async def main():
    """Função principal"""
    collector = LivePredictionCollector()
    result = await collector.run_full_collection()
    
    if result:
        print(f"\n🎯 RESULTADO DA COLETA:")
        print(f"   Jogos coletados: {result['matches_collected']}")
        print(f"   Predições geradas: {result['predictions_generated']}")
        print(f"   Tempo: {result['duration_seconds']:.2f}s")
    else:
        print("❌ Falha na coleta de dados")

if __name__ == "__main__":
    asyncio.run(main())
