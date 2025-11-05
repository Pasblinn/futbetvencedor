#!/usr/bin/env python3
"""
⏰ SCHEDULER AUTOMÁTICO - 100% AUTOMATIZADO

Executa tarefas periódicas para Docker/hospedagem:
- Importação de jogos dos próximos 7 dias (4x por dia)
- Atualização de jogos ao vivo (a cada 2 min)
- Geração de predictions automática (a cada 6h)
- Limpeza de jogos finalizados (a cada 1h)
- Normalização de nomes de ligas (1x por dia)
- Análise GREEN/RED de tickets (a cada 15 min)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from app.core.database import get_db_session
from app.services.results_updater import run_results_update
from app.services.daily_matches_importer import run_daily_import, run_cleanup_old_matches

# Novos jobs automáticos
from app.services.automated_pipeline import (
    run_import_upcoming_matches,
    run_update_live_matches,
    run_generate_predictions,
    run_cleanup_finished,
    run_normalize_leagues
)

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def daily_import_job():
    """
    Job para importar jogos do dia automaticamente

    Executa diariamente às 06:00 (horário de Brasília)
    """
    logger.info("📥 Iniciando importação automática de jogos do dia...")

    db = get_db_session()
    try:
        stats = run_daily_import(db)
        logger.info(f"""
        ✅ Importação diária concluída:
        - Ligas verificadas: {stats['leagues_checked']}
        - Jogos encontrados: {stats['fixtures_found']}
        - Novos jogos: {stats['imported']}
        - Jogos atualizados: {stats['updated']}
        - Erros: {stats['errors']}
        """)
    except Exception as e:
        logger.error(f"❌ Erro na importação diária: {e}")
    finally:
        db.close()


def update_results_job():
    """
    Job para atualizar resultados dos jogos

    Executa a cada 1 hora
    """
    logger.info("🔄 Iniciando atualização automática de resultados...")

    db = get_db_session()
    try:
        stats = run_results_update(db)
        logger.info(f"""
        ✅ Atualização concluída:
        - Jogos verificados: {stats['total_matches_checked']}
        - Resultados atualizados: {stats['results_updated']}
        - 🟢 GREENS: {stats['greens']}
        - 🔴 REDS: {stats['reds']}
        """)
    except Exception as e:
        logger.error(f"❌ Erro na atualização automática: {e}")
    finally:
        db.close()


def clean_old_matches_job():
    """
    Job para limpar jogos antigos

    Executa diariamente às 00:00
    """
    from app.models import Match
    from datetime import datetime, timedelta

    logger.info("🧹 Limpando jogos antigos...")

    db = get_db_session()
    try:
        # Jogos de mais de 7 dias que ainda estão marcados como agendados
        cutoff_date = datetime.now() - timedelta(days=7)

        old_matches = db.query(Match).filter(
            Match.match_date < cutoff_date,
            Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
        ).all()

        count = 0
        for match in old_matches:
            match.status = 'FT'
            count += 1

        db.commit()
        logger.info(f"✅ {count} jogos antigos marcados como finalizados")

    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {e}")
    finally:
        db.close()


def update_live_stats_job():
    """
    Job para atualizar estatísticas ao vivo

    Executa a cada 1 minuto
    """
    from app.services.live_stats_service import LiveStatsService

    db = get_db_session()
    try:
        service = LiveStatsService(db)
        live_matches = service.get_live_matches()

        if live_matches:
            # Atualizar placar de cada jogo ao vivo
            for match_data in live_matches:
                service.update_live_match_score(
                    match_id=match_data['match_id'],
                    home_score=match_data['score']['home'],
                    away_score=match_data['score']['away'],
                    status=match_data['status'],
                    elapsed=match_data['elapsed']
                )

            logger.info(f"🔴 {len(live_matches)} jogos ao vivo atualizados")
        else:
            logger.debug("Nenhum jogo ao vivo no momento")

    except Exception as e:
        logger.error(f"❌ Erro na atualização de stats ao vivo: {e}")
    finally:
        db.close()


def start_scheduler():
    """
    Inicia o scheduler com todos os jobs - 100% AUTOMÁTICO
    """
    logger.info("⏰ Iniciando scheduler automático COMPLETO...")

    # ========== JOBS PRINCIPAIS ==========

    # Job 1: Importar jogos dos próximos 7 dias (4x por dia - 00:00, 06:00, 12:00, 18:00)
    for hour in [0, 6, 12, 18]:
        scheduler.add_job(
            run_import_upcoming_matches,
            trigger=CronTrigger(hour=hour, minute=0),
            id=f'import_upcoming_{hour}h',
            name=f'Importar Jogos Próximos 7 Dias ({hour:02d}:00)',
            replace_existing=True
        )

    # Job 2: Atualizar jogos AO VIVO (a cada 2 minutos)
    scheduler.add_job(
        run_update_live_matches,
        trigger='interval',
        minutes=2,
        id='update_live',
        name='Atualizar Jogos AO VIVO (a cada 2 min)',
        replace_existing=True
    )

    # Job 3: Gerar predictions para novos jogos (a cada 6 horas)
    scheduler.add_job(
        run_generate_predictions,
        trigger='interval',
        hours=6,
        id='generate_predictions',
        name='Gerar Predictions ML (a cada 6h)',
        replace_existing=True
    )

    # Job 4: 🧠 Análise AI em lote (a cada 2 horas) - AJUSTADO
    from app.services.automated_pipeline import run_ai_batch_analysis
    scheduler.add_job(
        run_ai_batch_analysis,
        trigger='interval',
        hours=2,
        id='ai_batch_analysis',
        name='🧠 Análise AI em Lote (a cada 2h)',
        replace_existing=True
    )

    # Job 5: 🤖 ML Retraining (diário às 02:00) - NOVO
    from app.services.automated_pipeline import run_ml_retraining_sync
    scheduler.add_job(
        run_ml_retraining_sync,
        trigger=CronTrigger(hour=2, minute=0),
        id='ml_retraining',
        name='🤖 ML Retraining (diário 02:00)',
        replace_existing=True
    )

    # Job 6: Limpar jogos finalizados das predictions (a cada 1 hora)
    scheduler.add_job(
        run_cleanup_finished,
        trigger='interval',
        hours=1,
        id='cleanup_finished',
        name='Limpar Jogos Finalizados (a cada 1h)',
        replace_existing=True
    )

    # Job 7: Normalizar nomes de ligas (1x por dia às 03:00)
    scheduler.add_job(
        run_normalize_leagues,
        trigger=CronTrigger(hour=3, minute=0),
        id='normalize_leagues',
        name='Normalizar Nomes de Ligas (diário 03:00)',
        replace_existing=True
    )

    # Job 8: 🧹 Limpeza e Validação de Predictions (diário às 04:00) - NOVO 2025-10-20
    from app.services.predictions_cleanup import run_cleanup_job_for_scheduler
    scheduler.add_job(
        run_cleanup_job_for_scheduler,
        trigger=CronTrigger(hour=4, minute=0),
        id='cleanup_predictions',
        name='🧹 Limpeza de Predictions (diário 04:00)',
        replace_existing=True
    )

    # ========== JOBS LEGADOS (mantidos para compatibilidade) ==========

    # Job Legacy 1: Atualizar resultados a cada 1 hora
    scheduler.add_job(
        update_results_job,
        trigger='interval',
        hours=1,
        id='update_results',
        name='[LEGACY] Atualização de Resultados (a cada 1h)',
        replace_existing=True
    )

    # Job Legacy 2: Limpar jogos antigos diariamente às 00:00
    scheduler.add_job(
        clean_old_matches_job,
        trigger=CronTrigger(hour=0, minute=30),
        id='clean_old_matches',
        name='[LEGACY] Limpeza de Jogos Antigos (00:30)',
        replace_existing=True
    )

    scheduler.start()
    logger.info("""
    ✅ Scheduler COMPLETO iniciado com sucesso!

    🤖 JOBS AUTOMÁTICOS ATIVOS:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📥 Importar Jogos (próximos 7 dias)  → 4x/dia (00h, 06h, 12h, 18h)
    🔴 Atualizar Jogos AO VIVO           → A cada 2 minutos
    🧠 Gerar Predictions ML (v3)         → A cada 6 horas ✨ CORRIGIDO!
    🧠 Análise AI Agent (TOP 100)        → A cada 2 horas ⚡
    🤖 ML Retraining                     → Diário às 02:00 🎉
    🧹 Limpar Jogos Finalizados          → A cada 1 hora
    🏆 Normalizar Nomes de Ligas         → Diário às 03:00
    🧹 Limpeza de Predictions            → Diário às 04:00 🎉 NOVO!
    🔄 Atualizar Resultados [LEGACY]     → A cada 1 hora
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Sistema 100% AUTOMATIZADO - Pipeline v3 CORRIGIDA! 🚀🤖🧠
    - Seleção inteligente de 1X2 (apenas melhor outcome)
    - DRAW com filtros mais rigorosos (min 35% prob + 15% edge)
    - Confidence calibrado com histórico de accuracy
    - Limpeza automática de predictions inválidas
    """)


def stop_scheduler():
    """
    Para o scheduler gracefully
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("⏰ Scheduler parado")
