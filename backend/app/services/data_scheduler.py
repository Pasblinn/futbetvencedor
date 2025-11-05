"""
⏰ DATA SCHEDULER - AUTOMAÇÃO DE COLETA
Scheduler inteligente para automação completa do pipeline de dados

Rotinas automáticas:
- Coleta diária incremental (6h da manhã)
- Atualização de jogos ao vivo (a cada 10min durante jogos)
- Sincronização cache → DB (a cada hora)
- Limpeza de cache antigo (semanal)
- Retreinamento de modelos ML (conforme novos dados)
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import asyncio

from app.services.data_pipeline import DataPipeline
from app.services.api_quota_manager import APIQuotaManager
from app.services.ml_prediction_generator import run_daily_ml_prediction_generation
from app.services.ai_agent_batch import analyze_unanalyzed_predictions
from app.services.automated_ml_retraining import AutomatedMLRetraining

logger = logging.getLogger(__name__)

class DataScheduler:
    """Scheduler automatizado de coleta de dados"""

    def __init__(self, db: Session):
        self.db = db
        self.pipeline = DataPipeline(db)
        self.quota_manager = APIQuotaManager(db)
        self.scheduler = AsyncIOScheduler()

        # Estado
        self.is_running = False

    def start(self):
        """Iniciar scheduler"""
        if self.is_running:
            logger.warning("⚠️ Scheduler já está rodando")
            return

        logger.info("🚀 Iniciando Data Scheduler...")

        # Rotina 1: COLETA DIÁRIA INCREMENTAL
        # Todo dia às 6h da manhã (horário ideal - poucos jogos acontecendo)
        self.scheduler.add_job(
            self.daily_incremental_job,
            CronTrigger(hour=6, minute=0),
            id='daily_incremental',
            name='Coleta Diária Incremental',
            replace_existing=True
        )
        logger.info("✅ Job agendado: Coleta diária às 6h")

        # Rotina 2: ATUALIZAÇÃO DE JOGOS AO VIVO
        # A cada 10 minutos durante horários de jogos
        self.scheduler.add_job(
            self.live_matches_update_job,
            IntervalTrigger(minutes=10),
            id='live_updates',
            name='Atualização de Jogos ao Vivo',
            replace_existing=True
        )
        logger.info("✅ Job agendado: Atualização ao vivo a cada 10min")

        # Rotina 3: SINCRONIZAÇÃO CACHE → DATABASE
        # A cada hora, sincronizar dados do cache para o banco principal
        self.scheduler.add_job(
            self.sync_cache_job,
            IntervalTrigger(hours=1),
            id='sync_cache',
            name='Sincronização de Cache',
            replace_existing=True
        )
        logger.info("✅ Job agendado: Sync cache a cada 1h")

        # Rotina 4: VERIFICAÇÃO DE QUOTA
        # A cada 30 minutos, verificar saúde da quota
        self.scheduler.add_job(
            self.quota_health_check_job,
            IntervalTrigger(minutes=30),
            id='quota_check',
            name='Verificação de Quota',
            replace_existing=True
        )
        logger.info("✅ Job agendado: Verificação de quota a cada 30min")

        # Rotina 5: LIMPEZA DE CACHE
        # Todo domingo às 3h da manhã
        self.scheduler.add_job(
            self.cleanup_cache_job,
            CronTrigger(day_of_week='sun', hour=3, minute=0),
            id='cleanup_cache',
            name='Limpeza de Cache',
            replace_existing=True
        )
        logger.info("✅ Job agendado: Limpeza de cache aos domingos 3h")

        # Rotina 6: GERAÇÃO DE ML PREDICTIONS
        # Todo dia às 8h da manhã (após coleta de dados às 6h)
        self.scheduler.add_job(
            self.ml_predictions_job,
            CronTrigger(hour=8, minute=0),
            id='ml_predictions',
            name='Geração de ML Predictions (4500/dia)',
            replace_existing=True
        )
        logger.info("✅ Job agendado: Geração de ML Predictions diária às 8h")

        # Rotina 7: ML RETRAINING
        # Todo dia às 2h da manhã (aprende com resultados GREEN/RED)
        self.scheduler.add_job(
            self.ml_retraining_job,
            CronTrigger(hour=2, minute=0),
            id='ml_retraining',
            name='ML Retraining (aprendizado contínuo)',
            replace_existing=True
        )
        logger.info("✅ Job agendado: ML Retraining diário às 2h")

        # Rotina 8: AI AGENT BATCH ANALYSIS
        # A cada 2 horas (refina predictions com contexto)
        self.scheduler.add_job(
            self.ai_agent_batch_job,
            IntervalTrigger(hours=2),
            id='ai_agent_batch',
            name='AI Agent Batch Analysis (100/batch)',
            replace_existing=True
        )
        logger.info("✅ Job agendado: AI Agent batch a cada 2h")

        # Iniciar scheduler
        self.scheduler.start()
        self.is_running = True

        logger.info("🎉 Data Scheduler iniciado com sucesso!")

    def stop(self):
        """Parar scheduler"""
        if not self.is_running:
            return

        logger.info("⏹️ Parando Data Scheduler...")
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("✅ Scheduler parado")

    async def daily_incremental_job(self):
        """
        JOB DIÁRIO: Coleta incremental

        Executado às 6h da manhã
        Coleta novos jogos e atualiza resultados
        """
        logger.info("🌅 Executando coleta diária incremental...")

        try:
            # Verificar saúde da quota primeiro
            health = self.quota_manager.check_health()

            if health['status'] == 'CRITICAL':
                logger.error(f"❌ Quota crítica! Abortando coleta diária: {health['message']}")
                return

            # Coletar dados de ontem (resultados finais)
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            result_yesterday = await self.pipeline.collect_daily_incremental(yesterday)

            logger.info(f"✅ Ontem: {result_yesterday}")

            # Coletar dados de hoje (novos jogos)
            result_today = await self.pipeline.collect_daily_incremental()

            logger.info(f"✅ Hoje: {result_today}")

            # Coletar dados de amanhã (próximos jogos)
            tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
            result_tomorrow = await self.pipeline.collect_daily_incremental(tomorrow)

            logger.info(f"✅ Amanhã: {result_tomorrow}")

            logger.info("🎉 Coleta diária concluída com sucesso!")

        except Exception as e:
            logger.error(f"❌ Erro na coleta diária: {e}")

    async def live_matches_update_job(self):
        """
        JOB AO VIVO: Atualizar jogos em andamento

        Executado a cada 10 minutos
        Atualiza apenas jogos LIVE para economizar requests
        """
        try:
            # Verificar se há jogos ao vivo
            from app.models.api_tracking import FixtureCache

            live_fixtures = self.db.query(FixtureCache).filter(
                FixtureCache.status.in_(['1H', '2H', 'HT', 'LIVE']),
                FixtureCache.needs_update == True
            ).limit(20).all()  # Máximo 20 jogos ao vivo

            if not live_fixtures:
                logger.debug("ℹ️ Nenhum jogo ao vivo no momento")
                return

            logger.info(f"⚽ Atualizando {len(live_fixtures)} jogos ao vivo...")

            updated = 0

            for cache in live_fixtures:
                # Verificar quota
                if not self.quota_manager.can_make_request(1):
                    logger.warning("⚠️ Quota insuficiente. Parando atualizações ao vivo.")
                    break

                try:
                    # Atualizar fixture
                    fixture = await self.api_service.get_fixture_details(cache.fixture_id)

                    if fixture:
                        cache.raw_fixture_data = fixture
                        cache.status = fixture.get('fixture', {}).get('status', {}).get('short', 'NS')
                        cache.last_synced = datetime.now()

                        # Se finalizou, coletar estatísticas
                        if cache.status == 'FT':
                            cache.needs_update = True

                        updated += 1

                    # Registrar request
                    self.quota_manager.record_request(
                        endpoint='live_update',
                        success=True,
                        results_count=1,
                        params={'fixture': cache.fixture_id}
                    )

                    # Delay adaptativo
                    await asyncio.sleep(self.quota_manager.get_recommended_delay())

                except Exception as e:
                    logger.error(f"Erro ao atualizar fixture {cache.fixture_id}: {e}")

            self.db.commit()

            logger.info(f"✅ {updated} jogos ao vivo atualizados")

        except Exception as e:
            logger.error(f"❌ Erro na atualização ao vivo: {e}")

    async def sync_cache_job(self):
        """
        JOB DE SINCRONIZAÇÃO: Cache → Database

        Executado a cada hora
        Converte dados brutos do cache em modelos estruturados
        """
        logger.info("🔄 Executando sincronização de cache...")

        try:
            result = await self.pipeline.sync_cache_to_database(limit=200)
            logger.info(f"✅ Sync completo: {result}")

        except Exception as e:
            logger.error(f"❌ Erro na sincronização: {e}")

    async def quota_health_check_job(self):
        """
        JOB DE VERIFICAÇÃO: Saúde da quota

        Executado a cada 30 minutos
        Monitora uso e alerta se necessário
        """
        try:
            health = self.quota_manager.check_health()

            if health['status'] in ['WARNING', 'CRITICAL']:
                logger.warning(f"⚠️ ALERTA DE QUOTA: {health['message']}")
                logger.warning(f"   Ação recomendada: {health['recommended_action']}")
            else:
                logger.info(f"✅ Quota saudável: {health['available_requests']} requests disponíveis")

            # Log estatísticas
            stats = self.quota_manager.get_usage_stats()
            logger.info(f"📊 Uso diário: {stats['requests_used']}/{stats['daily_limit']} ({stats['usage_percentage']:.1f}%)")

        except Exception as e:
            logger.error(f"❌ Erro na verificação de quota: {e}")

    async def cleanup_cache_job(self):
        """
        JOB DE LIMPEZA: Remover cache antigo

        Executado semanalmente (domingos 3h)
        Remove dados antigos e desnecessários
        """
        logger.info("🧹 Executando limpeza de cache...")

        try:
            from app.models.api_tracking import FixtureCache, APIRequestLog

            # Remover fixtures antigos (mais de 2 anos)
            cutoff_date = datetime.now() - timedelta(days=730)

            old_fixtures = self.db.query(FixtureCache).filter(
                FixtureCache.fixture_date < cutoff_date
            ).delete()

            # Remover logs antigos (mais de 30 dias)
            log_cutoff = datetime.now() - timedelta(days=30)

            old_logs = self.db.query(APIRequestLog).filter(
                APIRequestLog.request_date < log_cutoff
            ).delete()

            self.db.commit()

            logger.info(f"✅ Limpeza concluída:")
            logger.info(f"   - Fixtures removidos: {old_fixtures}")
            logger.info(f"   - Logs removidos: {old_logs}")

        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")

    def get_status(self) -> dict:
        """Obter status do scheduler"""
        if not self.is_running:
            return {'status': 'STOPPED'}

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            })

        return {
            'status': 'RUNNING',
            'jobs': jobs,
            'quota_health': self.quota_manager.check_health()
        }

    def ml_predictions_job(self):
        """
        JOB DIÁRIO: Geração de ML Predictions

        Executado às 8h da manhã (após coleta de dados às 6h)
        Gera 4500 predictions por dia usando ML + Poisson
        """
        logger.info("🧠 Executando geração de ML Predictions...")

        try:
            # Gerar 4500 predictions (target ajustado de 2500 para 4500)
            result = run_daily_ml_prediction_generation(target=4500)

            if result.get('success'):
                logger.info(f"✅ ML Predictions geradas: {result.get('predictions_created', 0)} predictions")
                logger.info(f"📊 Singles: {result.get('singles', 0)}, Doubles: {result.get('doubles', 0)}, Trebles: {result.get('trebles', 0)}, Quads: {result.get('quads', 0)}")
            else:
                logger.error(f"❌ Erro ao gerar predictions: {result.get('error', 'Unknown')}")

        except Exception as e:
            logger.error(f"❌ Erro crítico no job de ML predictions: {e}")

    async def ml_retraining_job(self):
        """
        JOB DIÁRIO: ML Retraining

        Executado às 2h da manhã (antes da coleta de dados)
        Retreina modelos com resultados GREEN/RED acumulados
        Melhora accuracy continuamente
        """
        logger.info("🤖 Executando ML Retraining...")

        try:
            # Verificar dados suficientes para treino
            from app.models.prediction import Prediction

            results_count = self.db.query(Prediction).filter(
                Prediction.is_winner.isnot(None)  # Tem resultado GREEN/RED
            ).count()

            min_samples = 20  # Mínimo de resultados para treinar

            if results_count < min_samples:
                logger.info(f"ℹ️ Dados insuficientes para retraining: {results_count}/{min_samples}")
                return

            logger.info(f"📊 {results_count} resultados disponíveis para treino")

            # Inicializar retraining service
            retraining_service = AutomatedMLRetraining()

            # Retreinar cada modelo
            models_to_train = ['1x2_classifier', 'over_under_classifier', 'btts_classifier']

            for model_name in models_to_train:
                try:
                    trigger = {
                        'trigger_type': 'schedule',
                        'threshold_value': 0.0,
                        'current_value': 0.0,
                        'reason': 'Daily scheduled retraining'
                    }

                    result = retraining_service.retrain_model(model_name, trigger)

                    if result and result.success:
                        improvement = result.improvement * 100
                        logger.info(f"✅ {model_name}: {result.old_accuracy:.1%} → {result.new_accuracy:.1%} ({improvement:+.1f}%)")
                    else:
                        logger.warning(f"⚠️ {model_name}: Retraining não melhorou performance")

                except Exception as e:
                    logger.error(f"❌ Erro ao retreinar {model_name}: {e}")

            logger.info("🎉 ML Retraining concluído")

        except Exception as e:
            logger.error(f"❌ Erro crítico no ML retraining: {e}")

    async def ai_agent_batch_job(self):
        """
        JOB PERIÓDICO: AI Agent Batch Analysis

        Executado a cada 2 horas
        Analisa predictions pendentes com contexto profundo
        Refina confidence scores e recomendações
        """
        logger.info("🧠 Executando AI Agent Batch Analysis...")

        try:
            # Processar 100 predictions pendentes por batch
            result = await analyze_unanalyzed_predictions(limit=100)

            if result.get('success'):
                stats = result.get('stats', {})
                logger.info(f"✅ AI Agent batch concluído:")
                logger.info(f"   - Processadas: {stats.get('processed', 0)}")
                logger.info(f"   - Sucesso: {stats.get('success', 0)}")
                logger.info(f"   - Falhas: {stats.get('failed', 0)}")
                logger.info(f"   - Puladas: {stats.get('skipped', 0)}")
            else:
                error = result.get('error', 'Unknown')
                logger.error(f"❌ AI Agent batch falhou: {error}")

        except Exception as e:
            logger.error(f"❌ Erro crítico no AI Agent batch: {e}")
