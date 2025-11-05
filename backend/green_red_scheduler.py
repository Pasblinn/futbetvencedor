#!/usr/bin/env python3
"""
⏰ SCHEDULER AUTOMÁTICO GREEN/RED
Executa análise GREEN/RED a cada 30 minutos automaticamente
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import SessionLocal
from app.models import Match, Prediction
from sqlalchemy import func

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GreenRedScheduler:
    """Scheduler para análise automática GREEN/RED"""

    def __init__(self, interval_minutes=30):
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self.last_run = None
        self.total_runs = 0

    def analyze_green_red(self):
        """Executar análise GREEN/RED"""
        logger.info("🟢🔴 Iniciando análise GREEN/RED automática...")

        db = SessionLocal()
        try:
            # Buscar jogos finalizados
            finished_matches = db.query(Match).filter(
                Match.status.in_(['FT', 'FINISHED']),
                Match.home_score.isnot(None),
                Match.away_score.isnot(None)
            ).all()

            greens = 0
            reds = 0
            total_analyzed = 0

            for match in finished_matches:
                # Buscar prediction
                prediction = db.query(Prediction).filter(
                    Prediction.match_id == match.id,
                    Prediction.market_type == '1X2'
                ).first()

                if not prediction:
                    continue

                # Pular se já foi analisado
                if prediction.actual_outcome is not None:
                    continue

                # Determinar resultado real
                if match.home_score > match.away_score:
                    actual_outcome = '1'
                elif match.home_score < match.away_score:
                    actual_outcome = '2'
                else:
                    actual_outcome = 'X'

                # Comparar com prediction
                is_correct = (prediction.predicted_outcome == actual_outcome)

                # Atualizar prediction
                prediction.actual_outcome = actual_outcome
                prediction.is_winner = is_correct

                # Calcular lucro/prejuízo se houver odds
                if hasattr(prediction, 'actual_odds') and prediction.actual_odds:
                    if is_correct:
                        # GREEN: ganhou (odds - 1) * stake
                        prediction.profit_loss = (prediction.actual_odds - 1) * 100  # stake = 100
                    else:
                        # RED: perdeu stake
                        prediction.profit_loss = -100

                total_analyzed += 1
                if is_correct:
                    greens += 1
                    logger.info(f"   🟢 GREEN: {match.home_team.name if match.home_team else '?'} {match.home_score}-{match.away_score} {match.away_team.name if match.away_team else '?'}")
                else:
                    reds += 1
                    logger.info(f"   🔴 RED: {match.home_team.name if match.home_team else '?'} {match.home_score}-{match.away_score} {match.away_team.name if match.away_team else '?'}")

            db.commit()

            # Atualizar estatísticas do scheduler
            self.last_run = datetime.now()
            self.total_runs += 1

            # Log de resultado
            if total_analyzed > 0:
                accuracy = (greens / total_analyzed * 100) if total_analyzed > 0 else 0
                logger.info(f"✅ Análise concluída: {total_analyzed} predictions analisadas")
                logger.info(f"   🟢 GREEN: {greens} ({greens/total_analyzed*100:.1f}%)")
                logger.info(f"   🔴 RED: {reds} ({reds/total_analyzed*100:.1f}%)")
                logger.info(f"   📈 Acurácia: {accuracy:.1f}%")
            else:
                logger.info("ℹ️  Nenhuma nova prediction para analisar")

            return {
                'total_analyzed': total_analyzed,
                'greens': greens,
                'reds': reds,
                'accuracy': (greens / total_analyzed * 100) if total_analyzed > 0 else 0
            }

        except Exception as e:
            logger.error(f"❌ Erro na análise GREEN/RED: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def get_statistics(self):
        """Obter estatísticas do scheduler"""
        db = SessionLocal()
        try:
            # Total de predictions com resultado
            total = db.query(Prediction).filter(
                Prediction.actual_outcome.isnot(None)
            ).count()

            # Greens (acertos)
            greens = db.query(Prediction).filter(
                Prediction.is_winner == True
            ).count()

            # Reds (erros)
            reds = db.query(Prediction).filter(
                Prediction.is_winner == False
            ).count()

            # Predictions pendentes
            pending = db.query(Prediction).filter(
                Prediction.actual_outcome.is_(None)
            ).count()

            return {
                'total_analyzed': total,
                'greens': greens,
                'reds': reds,
                'pending': pending,
                'accuracy': (greens / total * 100) if total > 0 else 0,
                'total_runs': self.total_runs,
                'last_run': self.last_run.isoformat() if self.last_run else None
            }

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return None
        finally:
            db.close()

    def start(self):
        """Iniciar scheduler"""
        logger.info(f"🚀 Iniciando Green/Red Scheduler...")
        logger.info(f"⏰ Intervalo: {self.interval_minutes} minutos")

        # Executar uma vez imediatamente
        logger.info("▶️  Executando análise inicial...")
        self.analyze_green_red()

        # Agendar execução periódica
        self.scheduler.add_job(
            self.analyze_green_red,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='green_red_analyzer',
            name='Green/Red Analyzer',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("✅ Scheduler iniciado com sucesso!")
        logger.info(f"📅 Próxima execução em {self.interval_minutes} minutos")

    def stop(self):
        """Parar scheduler"""
        logger.info("🛑 Parando scheduler...")
        self.scheduler.shutdown()
        logger.info("✅ Scheduler parado")


def main():
    """Função principal"""
    print("=" * 70)
    print("🟢🔴 GREEN/RED ANALYZER - SCHEDULER AUTOMÁTICO")
    print("=" * 70)
    print()

    # Criar e iniciar scheduler (padrão: 30 minutos)
    scheduler = GreenRedScheduler(interval_minutes=30)
    scheduler.start()

    print()
    print("💡 Scheduler rodando em background...")
    print("   Pressione Ctrl+C para parar")
    print()

    try:
        # Manter script rodando
        while True:
            time.sleep(60)  # Sleep 1 minuto

            # Mostrar estatísticas a cada minuto
            stats = scheduler.get_statistics()
            if stats:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"📊 Analisados: {stats['total_analyzed']} | "
                      f"🟢 {stats['greens']} | "
                      f"🔴 {stats['reds']} | "
                      f"⏳ Pendentes: {stats['pending']} | "
                      f"📈 {stats['accuracy']:.1f}% | "
                      f"Execuções: {stats['total_runs']}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupção detectada...")
        scheduler.stop()
        print("\n✅ Scheduler finalizado")
        print("=" * 70)


if __name__ == "__main__":
    main()
