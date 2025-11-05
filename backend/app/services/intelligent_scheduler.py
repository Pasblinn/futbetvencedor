"""
⏰ INTELLIGENT SCHEDULER - Scheduler inteligente com rate limiting rigoroso
Executa tarefas de coleta respeitando limites das APIs para não deixar dados "pela metade"
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
import time
import threading
from dataclasses import dataclass

from app.services.gradual_population_service import gradual_population_service
from app.services.api_sports_collector import api_sports_collector
from app.core.database import get_db_session
from app.models.match import Match

logger = logging.getLogger(__name__)

@dataclass
class ApiRateLimit:
    """Controle rigoroso de rate limits por API"""
    name: str
    max_requests_per_hour: int
    max_requests_per_minute: int
    current_hour_count: int = 0
    current_minute_count: int = 0
    last_reset_hour: datetime = None
    last_reset_minute: datetime = None

class IntelligentScheduler:
    """
    ⏰ Scheduler inteligente com controle rigoroso de rate limits
    """

    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None

        # Rate limits rigorosos para cada API
        self.api_limits = {
            'football_data': ApiRateLimit(
                name='Football-Data.org',
                max_requests_per_hour=600,  # 10 por minuto
                max_requests_per_minute=10
            ),
            'api_sports': ApiRateLimit(
                name='API-Sports',
                max_requests_per_hour=5000,  # Plano free: ~83 por minuto
                max_requests_per_minute=80  # Margem de segurança
            ),
            'sportdb': ApiRateLimit(
                name='SportDB',
                max_requests_per_hour=1800,  # 30 por minuto
                max_requests_per_minute=30
            ),
            'openliga': ApiRateLimit(
                name='OpenLigaDB',
                max_requests_per_hour=1200,  # 20 por minuto
                max_requests_per_minute=20
            )
        }

        self.last_execution_stats = {
            'last_run': None,
            'matches_added': 0,
            'errors': [],
            'api_calls_made': {}
        }

    def start_scheduler(self):
        """
        🚀 Iniciar scheduler em thread separada
        """
        if self.is_running:
            logger.warning("⚠️ Scheduler já está rodando")
            return

        logger.info("🚀 INICIANDO SCHEDULER INTELIGENTE...")

        # Agendar tarefas com intervalos seguros
        self._schedule_tasks()

        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("✅ Scheduler iniciado com sucesso")

    def stop_scheduler(self):
        """
        🛑 Parar scheduler
        """
        if not self.is_running:
            logger.warning("⚠️ Scheduler não está rodando")
            return

        self.is_running = False
        schedule.clear()
        logger.info("🛑 Scheduler parado")

    def _schedule_tasks(self):
        """
        📅 Agendar tarefas com horários inteligentes
        """
        # 1. Coleta de jogos ao vivo: A cada 15 minutos (alta prioridade)
        schedule.every(15).minutes.do(self._collect_live_matches_safely)

        # 2. População gradual: A cada 2 horas (respeitando rate limits)
        schedule.every(2).hours.do(self._populate_gradually_safely)

        # 3. Coleta de ligas brasileiras: 3x por dia (8h, 14h, 20h)
        schedule.every().day.at("08:00").do(self._collect_brazilian_leagues_safely)
        schedule.every().day.at("14:00").do(self._collect_brazilian_leagues_safely)
        schedule.every().day.at("20:00").do(self._collect_brazilian_leagues_safely)

        # 4. Coleta de La Liga: 2x por dia (12h, 18h)
        schedule.every().day.at("12:00").do(self._collect_spanish_leagues_safely)
        schedule.every().day.at("18:00").do(self._collect_spanish_leagues_safely)

        # 5. Limpeza de rate limits: A cada hora (exato)
        schedule.every().hour.at(":00").do(self._reset_rate_limits)

        # 6. Relatório diário: 23:30
        schedule.every().day.at("23:30").do(self._generate_daily_report)

        logger.info("📅 Tarefas agendadas:")
        logger.info("  ⚡ Jogos ao vivo: a cada 15 minutos")
        logger.info("  🔄 População gradual: a cada 2 horas")
        logger.info("  🇧🇷 Brasileirão: 8h, 14h, 20h")
        logger.info("  🇪🇸 La Liga: 12h, 18h")
        logger.info("  🧹 Reset rate limits: a cada hora")
        logger.info("  📊 Relatório: 23:30")

    def _run_scheduler(self):
        """
        🔄 Loop principal do scheduler
        """
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check a cada 30 segundos
            except Exception as e:
                logger.error(f"❌ Erro no scheduler: {e}")
                time.sleep(60)  # Wait mais tempo em caso de erro

    def _collect_live_matches_safely(self):
        """
        ⚡ Coletar jogos ao vivo com segurança
        """
        asyncio.run(self._async_collect_live_matches_safely())

    async def _async_collect_live_matches_safely(self):
        """
        ⚡ Implementação async da coleta de jogos ao vivo
        """
        try:
            logger.info("⚡ Executando coleta de jogos ao vivo...")

            # Verificar rate limits antes de prosseguir
            if not self._can_make_api_calls(['api_sports']):
                logger.warning("⚠️ Rate limit atingido para jogos ao vivo, pulando...")
                return

            # Coletar apenas jogos ao vivo (poucas chamadas)
            result = await api_sports_collector._get_live_matches()

            if result:
                with get_db_session() as session:
                    added_count = 0
                    for match_data in result[:5]:  # Máximo 5 ao vivo
                        try:
                            added = await gradual_population_service._insert_match_safely(session, match_data)
                            if added:
                                added_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Erro inserindo jogo ao vivo: {e}")

                    session.commit()
                    logger.info(f"⚡ {added_count} jogos ao vivo adicionados")

                self._update_api_usage('api_sports', 1)

        except Exception as e:
            logger.error(f"❌ Erro na coleta de jogos ao vivo: {e}")

    def _populate_gradually_safely(self):
        """
        🔄 População gradual com controle rigoroso
        """
        asyncio.run(self._async_populate_gradually_safely())

    async def _async_populate_gradually_safely(self):
        """
        🔄 População gradual com controle rigoroso
        """
        try:
            logger.info("🔄 Executando população gradual...")

            # Verificar se temos rate limit suficiente
            apis_needed = ['football_data', 'api_sports', 'sportdb', 'openliga']
            if not self._can_make_api_calls(apis_needed):
                logger.warning("⚠️ Rate limits insuficientes para população completa, pulando...")
                return

            # Executar com limite menor para ser conservador
            result = await gradual_population_service.populate_gradually(target_matches=200)

            self.last_execution_stats = {
                'last_run': datetime.now(),
                'matches_added': result['matches_added'],
                'errors': result.get('errors', []),
                'api_calls_made': self._estimate_api_calls(result)
            }

            # Atualizar contadores de uso
            self._update_api_usage('football_data', 5)
            self._update_api_usage('api_sports', 3)
            self._update_api_usage('sportdb', 4)
            self._update_api_usage('openliga', 2)

            logger.info(f"🔄 População gradual concluída: {result['matches_added']} jogos adicionados")

        except Exception as e:
            logger.error(f"❌ Erro na população gradual: {e}")

    async def _collect_brazilian_leagues_safely(self):
        """
        🇧🇷 Coletar ligas brasileiras com foco
        """
        try:
            logger.info("🇧🇷 Executando coleta focada no Brasileirão...")

            if not self._can_make_api_calls(['api_sports']):
                logger.warning("⚠️ Rate limit insuficiente para Brasileirão, pulando...")
                return

            # Usar API-Sports especificamente para Brasileirão
            result = await api_sports_collector._get_league_upcoming_matches({
                'id': 71,  # Brasileirão Série A
                'name': 'Brasileirão Série A',
                'country': 'Brazil',
                'season': 2024
            })

            if result:
                with get_db_session() as session:
                    added_count = 0
                    for match_data in result[:10]:  # Máximo 10 por execução
                        try:
                            added = await gradual_population_service._insert_match_safely(session, match_data)
                            if added:
                                added_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Erro inserindo jogo brasileiro: {e}")

                    session.commit()
                    logger.info(f"🇧🇷 {added_count} jogos brasileiros adicionados")

            self._update_api_usage('api_sports', 2)

        except Exception as e:
            logger.error(f"❌ Erro na coleta brasileira: {e}")

    async def _collect_spanish_leagues_safely(self):
        """
        🇪🇸 Coletar La Liga com foco
        """
        try:
            logger.info("🇪🇸 Executando coleta focada na La Liga...")

            if not self._can_make_api_calls(['api_sports']):
                logger.warning("⚠️ Rate limit insuficiente para La Liga, pulando...")
                return

            # Usar API-Sports especificamente para La Liga
            result = await api_sports_collector._get_league_upcoming_matches({
                'id': 140,  # La Liga
                'name': 'La Liga',
                'country': 'Spain',
                'season': 2024
            })

            if result:
                with get_db_session() as session:
                    added_count = 0
                    for match_data in result[:10]:  # Máximo 10 por execução
                        try:
                            added = await gradual_population_service._insert_match_safely(session, match_data)
                            if added:
                                added_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Erro inserindo jogo espanhol: {e}")

                    session.commit()
                    logger.info(f"🇪🇸 {added_count} jogos espanhóis adicionados")

            self._update_api_usage('api_sports', 2)

        except Exception as e:
            logger.error(f"❌ Erro na coleta espanhola: {e}")

    def _can_make_api_calls(self, apis: List[str]) -> bool:
        """
        ✅ Verificar se pode fazer chamadas sem exceder rate limits
        """
        now = datetime.now()

        for api_name in apis:
            if api_name not in self.api_limits:
                continue

            api_limit = self.api_limits[api_name]

            # Reset contadores se necessário
            if api_limit.last_reset_hour is None or now - api_limit.last_reset_hour >= timedelta(hours=1):
                api_limit.current_hour_count = 0
                api_limit.last_reset_hour = now

            if api_limit.last_reset_minute is None or now - api_limit.last_reset_minute >= timedelta(minutes=1):
                api_limit.current_minute_count = 0
                api_limit.last_reset_minute = now

            # Verificar limites
            if (api_limit.current_hour_count >= api_limit.max_requests_per_hour or
                api_limit.current_minute_count >= api_limit.max_requests_per_minute):
                logger.warning(f"⚠️ Rate limit atingido para {api_limit.name}")
                return False

        return True

    def _update_api_usage(self, api_name: str, calls_made: int):
        """
        📊 Atualizar contador de uso da API
        """
        if api_name in self.api_limits:
            self.api_limits[api_name].current_hour_count += calls_made
            self.api_limits[api_name].current_minute_count += calls_made

    def _reset_rate_limits(self):
        """
        🧹 Reset rate limits a cada hora
        """
        now = datetime.now()
        for api_limit in self.api_limits.values():
            if api_limit.last_reset_hour is None or now - api_limit.last_reset_hour >= timedelta(hours=1):
                api_limit.current_hour_count = 0
                api_limit.last_reset_hour = now

        logger.info("🧹 Rate limits resetados")

    def _estimate_api_calls(self, result: Dict) -> Dict:
        """
        📊 Estimar calls de API feitas
        """
        return {
            'football_data': result.get('matches_added', 0) // 10,
            'api_sports': result.get('live_matches', 0) + 2,
            'sportdb': 4,
            'openliga': 2
        }

    async def _generate_daily_report(self):
        """
        📊 Gerar relatório diário
        """
        try:
            logger.info("📊 Gerando relatório diário...")

            with get_db_session() as session:
                total_matches = session.query(Match).count()
                today_matches = session.query(Match).filter(
                    Match.created_at >= datetime.now().date()
                ).count()

                # Ligas no banco
                leagues = session.query(Match.league).distinct().all()

                report = f"""
📊 RELATÓRIO DIÁRIO - {datetime.now().strftime('%d/%m/%Y')}
{'='*50}
⚽ Total de jogos no banco: {total_matches}
📅 Jogos adicionados hoje: {today_matches}
🏆 Ligas ativas: {len(leagues)}

🔄 Última execução:
  • Horário: {self.last_execution_stats.get('last_run', 'N/A')}
  • Jogos adicionados: {self.last_execution_stats.get('matches_added', 0)}
  • Erros: {len(self.last_execution_stats.get('errors', []))}

📡 Status das APIs:
"""
                for api_name, api_limit in self.api_limits.items():
                    usage_percent = (api_limit.current_hour_count / api_limit.max_requests_per_hour) * 100
                    report += f"  • {api_limit.name}: {api_limit.current_hour_count}/{api_limit.max_requests_per_hour} ({usage_percent:.1f}%)\n"

                logger.info(report)

        except Exception as e:
            logger.error(f"❌ Erro gerando relatório: {e}")

    def get_status(self) -> Dict:
        """
        📊 Obter status atual do scheduler
        """
        return {
            'is_running': self.is_running,
            'last_execution': self.last_execution_stats,
            'api_limits': {
                name: {
                    'hour_usage': f"{limit.current_hour_count}/{limit.max_requests_per_hour}",
                    'minute_usage': f"{limit.current_minute_count}/{limit.max_requests_per_minute}"
                }
                for name, limit in self.api_limits.items()
            },
            'next_scheduled_jobs': [str(job) for job in schedule.jobs]
        }

# Instância global
intelligent_scheduler = IntelligentScheduler()