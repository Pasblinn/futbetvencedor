"""
⏰ AGENDADOR GLOBAL - SISTEMA AUTOMATIZADO
Executa tarefas automáticas para monitoramento e análise mundial

Tarefas Agendadas:
1. Descoberta de jogos - 6:00 UTC (diariamente)
2. Geração de previsões - 8:00 UTC (diariamente)
3. Monitoramento ao vivo - Contínuo
4. Coleta de resultados - Após jogos terminarem
5. Retreino de ML - Semanalmente (domingo 4:00 UTC)
6. Análise de performance - Diariamente
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import schedule
import time
from app.services.global_match_system import global_match_system, run_daily_analysis
from app.ml.automated_retraining import automated_retraining_system, run_daily_retraining

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GlobalScheduler:
    """Agendador global para tarefas automatizadas"""

    def __init__(self):
        self.running = False
        self.active_tasks = {}
        self.execution_history = []

    def setup_schedules(self):
        """Configura todos os agendamentos"""
        logger.info("⏰ Configurando agendamentos globais")

        # 1. Descoberta de jogos - Diariamente às 6:00 UTC
        schedule.every().day.at("06:00").do(self.run_daily_discovery).tag('discovery')

        # 2. Geração de previsões - Diariamente às 8:00 UTC
        schedule.every().day.at("08:00").do(self.run_daily_predictions).tag('predictions')

        # 3. Análise de performance - Diariamente às 23:00 UTC
        schedule.every().day.at("23:00").do(self.run_daily_performance_analysis).tag('analysis')

        # 4. Retreino de ML - Domingos às 4:00 UTC
        schedule.every().sunday.at("04:00").do(self.run_weekly_retraining).tag('retraining')

        # 5. Limpeza de dados antigos - Sábados às 2:00 UTC
        schedule.every().saturday.at("02:00").do(self.run_data_cleanup).tag('cleanup')

        # 6. Verificação de saúde do sistema - A cada 4 horas
        schedule.every(4).hours.do(self.run_health_check).tag('health')

        logger.info("✅ Agendamentos configurados:")
        logger.info("   📊 06:00 UTC - Descoberta de jogos")
        logger.info("   🧠 08:00 UTC - Geração de previsões")
        logger.info("   📈 23:00 UTC - Análise de performance")
        logger.info("   🔄 Dom 04:00 UTC - Retreino de ML")
        logger.info("   🧹 Sáb 02:00 UTC - Limpeza de dados")
        logger.info("   ❤️ A cada 4h - Verificação de saúde")

    async def run_daily_discovery(self):
        """Executa descoberta diária de jogos"""
        task_name = "daily_discovery"
        logger.info(f"🔍 Iniciando: {task_name}")

        try:
            self.active_tasks[task_name] = {
                'status': 'running',
                'started_at': datetime.now(),
                'progress': 'Descobrindo jogos de todas as ligas...'
            }

            # Descobrir jogos dos próximos 7 dias
            matches = await global_match_system.discover_matches_globally(days_ahead=7)

            result = {
                'task': task_name,
                'status': 'completed',
                'matches_discovered': len(matches),
                'leagues_scanned': len(global_match_system.supported_leagues),
                'execution_time': (datetime.now() - self.active_tasks[task_name]['started_at']).total_seconds(),
                'completed_at': datetime.now()
            }

            self.active_tasks[task_name]['status'] = 'completed'
            self.execution_history.append(result)

            logger.info(f"✅ {task_name}: {len(matches)} jogos descobertos")

        except Exception as e:
            logger.error(f"❌ Erro em {task_name}: {e}")
            self.active_tasks[task_name]['status'] = 'error'
            self.active_tasks[task_name]['error'] = str(e)

    async def run_daily_predictions(self):
        """Executa geração diária de previsões"""
        task_name = "daily_predictions"
        logger.info(f"🧠 Iniciando: {task_name}")

        try:
            self.active_tasks[task_name] = {
                'status': 'running',
                'started_at': datetime.now(),
                'progress': 'Gerando previsões para todos os jogos...'
            }

            # Gerar previsões para hoje
            predictions = await global_match_system.generate_predictions_for_all_matches()

            result = {
                'task': task_name,
                'status': 'completed',
                'predictions_generated': len(predictions),
                'markets_analyzed': 13 * len(predictions),  # 13 mercados por jogo
                'execution_time': (datetime.now() - self.active_tasks[task_name]['started_at']).total_seconds(),
                'completed_at': datetime.now()
            }

            self.active_tasks[task_name]['status'] = 'completed'
            self.execution_history.append(result)

            logger.info(f"✅ {task_name}: {len(predictions)} previsões geradas")

        except Exception as e:
            logger.error(f"❌ Erro em {task_name}: {e}")
            self.active_tasks[task_name]['status'] = 'error'
            self.active_tasks[task_name]['error'] = str(e)

    async def run_daily_performance_analysis(self):
        """Executa análise diária de performance"""
        task_name = "performance_analysis"
        logger.info(f"📈 Iniciando: {task_name}")

        try:
            self.active_tasks[task_name] = {
                'status': 'running',
                'started_at': datetime.now(),
                'progress': 'Analisando performance das previsões...'
            }

            # Analisar acurácia dos últimos 7 dias
            accuracy_analysis = await automated_retraining_system.analyze_prediction_accuracy(days_back=7)

            result = {
                'task': task_name,
                'status': 'completed',
                'matches_analyzed': accuracy_analysis.get('total_matches', 0),
                'average_accuracy': self._calculate_overall_accuracy(accuracy_analysis),
                'improvements_needed': len(accuracy_analysis.get('improvements_needed', [])),
                'execution_time': (datetime.now() - self.active_tasks[task_name]['started_at']).total_seconds(),
                'completed_at': datetime.now(),
                'details': accuracy_analysis
            }

            self.active_tasks[task_name]['status'] = 'completed'
            self.execution_history.append(result)

            logger.info(f"✅ {task_name}: {accuracy_analysis.get('total_matches', 0)} jogos analisados")

        except Exception as e:
            logger.error(f"❌ Erro em {task_name}: {e}")
            self.active_tasks[task_name]['status'] = 'error'
            self.active_tasks[task_name]['error'] = str(e)

    async def run_weekly_retraining(self):
        """Executa retreino semanal de ML"""
        task_name = "weekly_retraining"
        logger.info(f"🔄 Iniciando: {task_name}")

        try:
            self.active_tasks[task_name] = {
                'status': 'running',
                'started_at': datetime.now(),
                'progress': 'Retreinando modelos de ML...'
            }

            # Executar retreino automático
            retrain_result = await automated_retraining_system.retrain_models_automatically(min_new_samples=30)

            result = {
                'task': task_name,
                'status': 'completed',
                'retrain_status': retrain_result.get('status', 'unknown'),
                'model_performance': retrain_result.get('performance', {}),
                'training_samples': retrain_result.get('training_samples', 0),
                'execution_time': (datetime.now() - self.active_tasks[task_name]['started_at']).total_seconds(),
                'completed_at': datetime.now(),
                'details': retrain_result
            }

            self.active_tasks[task_name]['status'] = 'completed'
            self.execution_history.append(result)

            logger.info(f"✅ {task_name}: {retrain_result.get('status', 'unknown')}")

        except Exception as e:
            logger.error(f"❌ Erro em {task_name}: {e}")
            self.active_tasks[task_name]['status'] = 'error'
            self.active_tasks[task_name]['error'] = str(e)

    async def run_data_cleanup(self):
        """Executa limpeza de dados antigos"""
        task_name = "data_cleanup"
        logger.info(f"🧹 Iniciando: {task_name}")

        try:
            self.active_tasks[task_name] = {
                'status': 'running',
                'started_at': datetime.now(),
                'progress': 'Limpando dados antigos...'
            }

            # Limpar arquivos de resultados mais antigos que 60 dias
            cleanup_stats = await self._cleanup_old_files(days_old=60)

            result = {
                'task': task_name,
                'status': 'completed',
                'files_removed': cleanup_stats['files_removed'],
                'space_freed': cleanup_stats['space_freed'],
                'execution_time': (datetime.now() - self.active_tasks[task_name]['started_at']).total_seconds(),
                'completed_at': datetime.now()
            }

            self.active_tasks[task_name]['status'] = 'completed'
            self.execution_history.append(result)

            logger.info(f"✅ {task_name}: {cleanup_stats['files_removed']} arquivos removidos")

        except Exception as e:
            logger.error(f"❌ Erro em {task_name}: {e}")
            self.active_tasks[task_name]['status'] = 'error'
            self.active_tasks[task_name]['error'] = str(e)

    async def run_health_check(self):
        """Executa verificação de saúde do sistema"""
        task_name = "health_check"

        try:
            self.active_tasks[task_name] = {
                'status': 'running',
                'started_at': datetime.now(),
                'progress': 'Verificando saúde do sistema...'
            }

            # Verificar status do sistema
            system_status = await global_match_system.get_system_status()

            # Verificar status de retreino
            retraining_status = await automated_retraining_system.get_retraining_status()

            health_score = self._calculate_health_score(system_status, retraining_status)

            result = {
                'task': task_name,
                'status': 'completed',
                'health_score': health_score,
                'system_operational': system_status.get('system_status') == 'operational',
                'active_matches': system_status.get('active_matches', 0),
                'live_matches': system_status.get('live_matches', 0),
                'models_performance': retraining_status.get('current_performance', {}),
                'execution_time': (datetime.now() - self.active_tasks[task_name]['started_at']).total_seconds(),
                'completed_at': datetime.now()
            }

            self.active_tasks[task_name]['status'] = 'completed'

            # Log apenas se houver problemas
            if health_score < 0.8:
                logger.warning(f"⚠️ Sistema com problemas - Score: {health_score:.2f}")
            else:
                logger.debug(f"✅ Sistema saudável - Score: {health_score:.2f}")

        except Exception as e:
            logger.error(f"❌ Erro em {task_name}: {e}")
            self.active_tasks[task_name]['status'] = 'error'
            self.active_tasks[task_name]['error'] = str(e)

    def _calculate_overall_accuracy(self, accuracy_analysis: Dict) -> float:
        """Calcula acurácia geral"""
        markets = accuracy_analysis.get('markets_accuracy', {})
        if not markets:
            return 0.0

        accuracies = [market['accuracy'] for market in markets.values()]
        return sum(accuracies) / len(accuracies)

    async def _cleanup_old_files(self, days_old: int = 60) -> Dict:
        """Remove arquivos antigos"""
        import os
        from pathlib import Path

        cutoff_date = datetime.now() - timedelta(days=days_old)
        files_removed = 0
        space_freed = 0

        # Diretórios para limpar
        directories = ['retraining_data', 'daily_predictions', 'match_results']

        for directory in directories:
            if not os.path.exists(directory):
                continue

            for file_path in Path(directory).iterdir():
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        files_removed += 1
                        space_freed += size

        return {
            'files_removed': files_removed,
            'space_freed': space_freed
        }

    def _calculate_health_score(self, system_status: Dict, retraining_status: Dict) -> float:
        """Calcula score de saúde do sistema"""
        score = 1.0

        # Penalizar se sistema não está operacional
        if system_status.get('system_status') != 'operational':
            score -= 0.3

        # Penalizar se não há jogos ativos (pode indicar problema na descoberta)
        if system_status.get('active_matches', 0) == 0:
            score -= 0.2

        # Penalizar se modelos têm performance baixa
        current_performance = retraining_status.get('current_performance', {})
        if current_performance and current_performance.get('f1_score', 1.0) < 0.6:
            score -= 0.2

        # Penalizar se há muitos dados novos sem retreino
        if retraining_status.get('new_data_available', 0) > 100:
            score -= 0.1

        return max(0.0, score)

    async def start_scheduler(self):
        """Inicia o agendador"""
        self.running = True
        logger.info("🚀 Iniciando agendador global")

        # Configurar agendamentos
        self.setup_schedules()

        # Executar monitoramento ao vivo em background
        asyncio.create_task(self._start_live_monitoring())

        # Loop principal do agendador
        while self.running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Verificar a cada minuto

            except Exception as e:
                logger.error(f"❌ Erro no agendador: {e}")
                await asyncio.sleep(300)  # Aguardar 5 minutos em caso de erro

    async def _start_live_monitoring(self):
        """Inicia monitoramento ao vivo em background"""
        logger.info("🔴 Iniciando monitoramento ao vivo global")

        try:
            await global_match_system.monitor_live_matches_globally()
        except Exception as e:
            logger.error(f"❌ Erro no monitoramento ao vivo: {e}")
            # Reiniciar após 10 minutos
            await asyncio.sleep(600)
            await self._start_live_monitoring()

    def stop_scheduler(self):
        """Para o agendador"""
        logger.info("⏹️ Parando agendador global")
        self.running = False
        schedule.clear()

    def get_scheduler_status(self) -> Dict:
        """Retorna status do agendador"""
        return {
            'running': self.running,
            'next_jobs': [
                {
                    'job': str(job.job_func.__name__),
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'tags': list(job.tags)
                }
                for job in schedule.jobs
            ],
            'active_tasks': self.active_tasks,
            'execution_history': self.execution_history[-10:],  # Últimas 10 execuções
            'total_executions': len(self.execution_history)
        }

# Instância global do agendador
global_scheduler = GlobalScheduler()

async def start_global_scheduler():
    """Inicia agendador global"""
    await global_scheduler.start_scheduler()

def stop_global_scheduler():
    """Para agendador global"""
    global_scheduler.stop_scheduler()

if __name__ == "__main__":
    # Para teste
    import asyncio
    asyncio.run(start_global_scheduler())