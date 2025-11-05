#!/usr/bin/env python3
"""
🚀 SETUP DO PIPELINE DE DADOS
Script de configuração inicial do sistema de coleta de dados

Este script:
1. Configura ligas prioritárias
2. Inicia coleta histórica inicial
3. Configura scheduler automático
4. Valida configurações

Usage:
    python setup_data_pipeline.py --initial-historical
    python setup_data_pipeline.py --configure-leagues
    python setup_data_pipeline.py --start-scheduler
"""

import asyncio
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.api_tracking import LeagueConfig, DailyAPIQuota
from app.services.data_pipeline import DataPipeline
from app.services.data_scheduler import DataScheduler
from app.services.api_quota_manager import APIQuotaManager

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração de ligas prioritárias
PRIORITY_LEAGUES = [
    {
        'league_id': 71,
        'league_name': 'Brasileirão Série A',
        'country': 'Brazil',
        'priority': 1,
        'seasons': [2023, 2024, 2025],
        'current_season': 2024,
        'collect_statistics': True
    },
    {
        'league_id': 2,
        'league_name': 'UEFA Champions League',
        'country': 'World',
        'priority': 2, # Prioridade alta
        'seasons': [2023, 2024, 2025],
        'current_season': 2024,
        'collect_statistics': True
    },
    {
        'league_id': 72,
        'league_name': 'Brasileirão Série B',
        'country': 'Brazil',
        'priority': 2,
        'seasons': [2023, 2024],
        'current_season': 2024,
        'collect_statistics': True
    },
    {
        'league_id': 13,
        'league_name': 'Copa Libertadores',
        'country': 'World',
        'priority': 3,
        'seasons': [2023, 2024, 2025],
        'current_season': 2024,
        'collect_statistics': True
    },
    {
        'league_id': 11,
        'league_name': 'Copa Sul-Americana',
        'country': 'World',
        'priority': 4,
        'seasons': [2023, 2024],
        'current_season': 2024,
        'collect_statistics': True
    },
    {
        'league_id': 39,
        'league_name': 'Premier League',
        'country': 'England',
        'priority': 5,
        'seasons': [2023, 2024],
        'current_season': 2024,
        'collect_statistics': False  # Economizar requests
    },
    {
        'league_id': 1322, # ID correto para Copa do Brasil (o ID 71 é do Brasileirão A)
        'league_name': 'Copa do Brasil',
        'country': 'Brazil',
        'priority': 5,
        'seasons': [2023, 2024, 2025],
        'current_season': 2024,
        'collect_statistics': True
    },
    {
        'league_id': 140,
        'league_name': 'La Liga',
        'country': 'Spain',
        'priority': 6,
        'seasons': [2023, 2024],
        'current_season': 2024,
        'collect_statistics': False
    },
    {
        'league_id': 78,
        'league_name': 'Bundesliga',
        'country': 'Germany',
        'priority': 7,
        'seasons': [2023, 2024],
        'current_season': 2024,
        'collect_statistics': False
    },
    {
        'league_id': 135,
        'league_name': 'Serie A',
        'country': 'Italy',
        'priority': 8,
        'seasons': [2023, 2024],
        'current_season': 2024,
        'collect_statistics': False
    },
    {
        'league_id': 3,
        'league_name': 'UEFA Europa League',
        'country': 'World',
        'priority': 9,
        'seasons': [2023, 2024],
        'current_season': 2024,
        'collect_statistics': False
    }
]

def create_tables():
    """Criar todas as tabelas do banco"""
    logger.info("📊 Criando tabelas do banco de dados...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tabelas criadas com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        return False

def configure_leagues(db: Session):
    """Configurar ligas prioritárias"""
    logger.info("🏆 Configurando ligas prioritárias...")

    configured = 0

    for league_data in PRIORITY_LEAGUES:
        # Verificar se já existe
        existing = db.query(LeagueConfig).filter(
            LeagueConfig.league_id == league_data['league_id']
        ).first()

        if existing:
            logger.info(f"   ✅ {league_data['league_name']} já configurada")
            continue

        # Criar nova configuração
        league_config = LeagueConfig(
            league_id=league_data['league_id'],
            league_name=league_data['league_name'],
            country=league_data['country'],
            priority=league_data['priority'],
            is_active=True,
            collect_historical=True,
            collect_daily=True,
            collect_statistics=league_data['collect_statistics'],
            seasons=league_data['seasons'],
            current_season=league_data['current_season']
        )

        db.add(league_config)
        configured += 1
        logger.info(f"   ➕ {league_data['league_name']} adicionada")

    db.commit()

    logger.info(f"✅ {configured} novas ligas configuradas!")
    logger.info(f"📊 Total de ligas ativas: {len(PRIORITY_LEAGUES)}")

async def collect_initial_historical(db: Session, max_leagues: int = None):
    """
    Coletar histórico inicial de todas as ligas

    Args:
        db: Sessão do banco
        max_leagues: Limite de ligas (None = todas)
    """
    logger.info("📚 INICIANDO COLETA HISTÓRICA INICIAL")
    logger.info("="*60)

    pipeline = DataPipeline(db)
    quota_manager = APIQuotaManager(db)

    # Verificar quota disponível
    health = quota_manager.check_health()
    logger.info(f"💊 Status da quota: {health['status']}")
    logger.info(f"   {health['message']}")
    logger.info(f"   Requests disponíveis: {health['available_requests']}")

    if health['status'] == 'CRITICAL':
        logger.error("❌ Quota insuficiente para coleta histórica!")
        return

    # Buscar ligas ativas
    leagues = db.query(LeagueConfig).filter(
        LeagueConfig.is_active == True,
        LeagueConfig.collect_historical == True
    ).order_by(LeagueConfig.priority).all()

    if max_leagues:
        leagues = leagues[:max_leagues]

    logger.info(f"\n🎯 {len(leagues)} ligas serão coletadas:")
    for league in leagues:
        logger.info(f"   {league.priority}. {league.league_name} ({len(league.seasons)} temporadas)")

    # Confirmar
    print("\n⚠️  Esta operação pode usar centenas de requests!")
    print(f"   Estimativa: ~{len(leagues) * 2} requests (sem estatísticas)")
    print(f"   Com estatísticas: ~{len(leagues) * 100} requests adicionais")

    response = input("\nDeseja continuar? (s/N): ")
    if response.lower() != 's':
        logger.info("❌ Coleta cancelada pelo usuário")
        return

    # Coletar cada liga
    total_fixtures = 0
    total_requests = 0

    for league in leagues:
        logger.info(f"\n{'='*60}")
        logger.info(f"🏆 {league.league_name}")
        logger.info(f"{'='*60}")

        # Coletar cada temporada
        for season in league.seasons:
            result = await pipeline.collect_historical_batch(
                league_id=league.league_id,
                season=season
            )

            if result['status'] == 'COMPLETED':
                total_fixtures += result.get('fixtures_collected', 0)
                total_requests += result.get('requests_used', 0)

            elif result['status'] == 'SKIPPED':
                logger.info(f"   ⏭️  Temporada {season} já coletada")

            # Verificar quota
            remaining = quota_manager.get_available_requests()
            if remaining < 50:
                logger.warning(f"⚠️ Quota baixa ({remaining} requests). Pausando...")
                break

        # Delay entre ligas
        await asyncio.sleep(2)

    # Resumo final
    logger.info(f"\n{'='*60}")
    logger.info("🎉 COLETA HISTÓRICA CONCLUÍDA!")
    logger.info(f"{'='*60}")
    logger.info(f"📊 Total de fixtures: {total_fixtures}")
    logger.info(f"📡 Requests usados: {total_requests}")
    logger.info(f"💊 Quota restante: {quota_manager.get_available_requests()}")

def start_scheduler_daemon(db: Session):
    """Iniciar scheduler em modo daemon"""
    logger.info("⏰ Iniciando scheduler automático...")

    scheduler = DataScheduler(db)

    try:
        scheduler.start()

        logger.info("\n✅ Scheduler iniciado com sucesso!")
        logger.info("\nJobs agendados:")

        status = scheduler.get_status()
        for job in status['jobs']:
            logger.info(f"   - {job['name']}: próxima execução em {job['next_run']}")

        logger.info("\n⚠️  Pressione Ctrl+C para parar o scheduler")

        # Manter rodando
        try:
            # Usar loop simples em vez de run_forever() para compatibilidade com systemd
            import signal
            import time

            # Handler para sinais de sistema
            stop_event = False
            def signal_handler(sig, frame):
                nonlocal stop_event
                stop_event = True

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Loop infinito simples
            while not stop_event:
                time.sleep(1)

        except KeyboardInterrupt:
            pass
        finally:
            logger.info("\n⏹️  Parando scheduler...")
            scheduler.stop()
            logger.info("✅ Scheduler parado")

    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scheduler: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Setup do Pipeline de Dados para ML'
    )

    parser.add_argument(
        '--create-tables',
        action='store_true',
        help='Criar tabelas do banco de dados'
    )

    parser.add_argument(
        '--configure-leagues',
        action='store_true',
        help='Configurar ligas prioritárias'
    )

    parser.add_argument(
        '--initial-historical',
        action='store_true',
        help='Coletar histórico inicial de todas as ligas'
    )

    parser.add_argument(
        '--max-leagues',
        type=int,
        help='Limite de ligas para coleta histórica'
    )

    parser.add_argument(
        '--start-scheduler',
        action='store_true',
        help='Iniciar scheduler automático'
    )

    parser.add_argument(
        '--full-setup',
        action='store_true',
        help='Executar setup completo (tabelas + ligas + scheduler)'
    )

    args = parser.parse_args()

    # Criar sessão do banco
    db = SessionLocal()

    try:
        # Setup completo
        if args.full_setup:
            logger.info("🚀 INICIANDO SETUP COMPLETO DO PIPELINE")
            logger.info("="*60)

            # 1. Criar tabelas
            create_tables()

            # 2. Configurar ligas
            configure_leagues(db)

            # 3. Perguntar se quer coletar histórico
            print("\n📚 Deseja coletar histórico inicial agora?")
            print("   (Pode ser feito depois com --initial-historical)")
            response = input("Coletar agora? (s/N): ")

            if response.lower() == 's':
                await collect_initial_historical(db)

            # 4. Iniciar scheduler
            print("\n⏰ Deseja iniciar o scheduler automático?")
            response = input("Iniciar scheduler? (s/N): ")

            if response.lower() == 's':
                start_scheduler_daemon(db)

            logger.info("\n✅ Setup completo finalizado!")

        # Comandos individuais
        else:
            if args.create_tables:
                create_tables()

            if args.configure_leagues:
                configure_leagues(db)

            if args.initial_historical:
                await collect_initial_historical(db, args.max_leagues)

            if args.start_scheduler:
                start_scheduler_daemon(db)

            # Se nenhum argumento, mostrar ajuda
            if not any([
                args.create_tables,
                args.configure_leagues,
                args.initial_historical,
                args.start_scheduler
            ]):
                parser.print_help()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
