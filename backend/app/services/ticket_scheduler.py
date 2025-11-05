"""
⏰ TICKET ANALYSIS SCHEDULER
Executa análise de tickets automaticamente em background
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.core.database import SessionLocal
from app.services.ticket_analyzer import analyze_all_tickets

logger = logging.getLogger(__name__)


class TicketAnalysisScheduler:
    """Scheduler para análise automática de tickets"""

    def __init__(self, interval_minutes: int = 15):
        """
        Inicializa o scheduler

        Args:
            interval_minutes: Intervalo entre execuções em minutos (padrão: 15)
        """
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self.last_run = None
        self.total_runs = 0
        self.is_running = False

    def _analyze_tickets_job(self):
        """Job que executa a análise de tickets"""
        if self.is_running:
            logger.warning("⚠️  Análise já em execução, pulando...")
            return

        self.is_running = True
        logger.info("🎯 Executando análise automática de tickets...")

        db = SessionLocal()
        try:
            # Executar análise
            stats = analyze_all_tickets(db)

            # Atualizar estatísticas do scheduler
            self.last_run = datetime.utcnow()
            self.total_runs += 1

            # Log resultado
            if stats['analyzed'] > 0:
                logger.info(
                    f"✅ Análise concluída | "
                    f"Analisados: {stats['analyzed']} | "
                    f"🟢 Ganhos: {stats['won']} (R$ {stats['total_profit']:.2f}) | "
                    f"🔴 Perdas: {stats['lost']} (R$ {stats['total_loss']:.2f})"
                )
            else:
                logger.debug("ℹ️  Nenhum ticket novo para analisar")

        except Exception as e:
            logger.error(f"❌ Erro na análise automática de tickets: {e}", exc_info=True)
        finally:
            db.close()
            self.is_running = False

    def start(self):
        """Inicia o scheduler"""
        if self.scheduler.running:
            logger.warning("⚠️  Scheduler já está rodando")
            return

        logger.info("🚀 Iniciando Ticket Analysis Scheduler...")
        logger.info(f"⏰ Intervalo: {self.interval_minutes} minutos")

        # Executar uma vez imediatamente ao iniciar
        logger.info("▶️  Executando análise inicial...")
        self._analyze_tickets_job()

        # Agendar execução periódica
        self.scheduler.add_job(
            self._analyze_tickets_job,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='ticket_analyzer',
            name='Ticket Analyzer',
            replace_existing=True,
            max_instances=1  # Evita execuções simultâneas
        )

        self.scheduler.start()
        logger.info("✅ Ticket Analysis Scheduler iniciado com sucesso!")
        logger.info(f"📅 Próxima execução em {self.interval_minutes} minutos")

    def stop(self):
        """Para o scheduler"""
        if not self.scheduler.running:
            logger.warning("⚠️  Scheduler não está rodando")
            return

        logger.info("🛑 Parando Ticket Analysis Scheduler...")
        self.scheduler.shutdown(wait=True)
        logger.info("✅ Scheduler parado com sucesso")

    def get_stats(self):
        """Retorna estatísticas do scheduler"""
        return {
            'is_running': self.scheduler.running if self.scheduler else False,
            'interval_minutes': self.interval_minutes,
            'total_runs': self.total_runs,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': (
                self.scheduler.get_jobs()[0].next_run_time.isoformat()
                if self.scheduler and self.scheduler.running and self.scheduler.get_jobs()
                else None
            )
        }


# Instância global do scheduler
_scheduler_instance = None


def get_scheduler() -> TicketAnalysisScheduler:
    """Retorna a instância global do scheduler"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TicketAnalysisScheduler(interval_minutes=15)
    return _scheduler_instance


def start_scheduler():
    """Inicia o scheduler global"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Para o scheduler global"""
    scheduler = get_scheduler()
    scheduler.stop()
