#!/usr/bin/env python3
"""
🔧 SCRIPT DE CORREÇÃO - Partidas Travadas

Este script corrige partidas que ficaram "travadas" com status LIVE/2H
mas que já deveriam estar finalizadas.

Uso:
    python fix_stuck_matches.py [--dry-run] [--hours 2]

Exemplos:
    python fix_stuck_matches.py --dry-run  # Apenas mostra o que seria feito
    python fix_stuck_matches.py             # Executa a correção
    python fix_stuck_matches.py --hours 3   # Considera travado após 3h
"""

import sys
sys.path.append('/home/pablintadini/mododeus/football-analytics/backend')

from datetime import datetime, timedelta, timezone
from sqlalchemy import and_
import argparse
import logging

from app.core.database import SessionLocal
from app.models import Match

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_stuck_matches(db, hours_threshold=2):
    """
    Encontra partidas travadas com status LIVE mas que começaram há muito tempo

    Args:
        db: Database session
        hours_threshold: Horas após início para considerar travado

    Returns:
        List de Match objects travados
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)

    stuck_matches = db.query(Match).filter(
        and_(
            Match.status.in_(['LIVE', '1H', '2H', 'HT', 'BT', 'ET', 'P']),
            Match.match_date < cutoff_time
        )
    ).all()

    return stuck_matches


def fix_stuck_match(db, match, dry_run=False):
    """
    Corrige uma partida travada mudando status para FT

    Args:
        db: Database session
        match: Match object
        dry_run: Se True, apenas simula a correção

    Returns:
        bool: True se corrigido, False se erro
    """
    try:
        logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Corrigindo match {match.id}:")
        logger.info(f"  Liga: {match.league}")
        logger.info(f"  Data: {match.match_date}")
        logger.info(f"  Status atual: {match.status}")
        logger.info(f"  Placar: {match.home_score}-{match.away_score}")

        if not dry_run:
            match.status = 'FT'
            db.commit()
            logger.info(f"  ✅ Status atualizado para 'FT'")
        else:
            logger.info(f"  → Seria atualizado para 'FT'")

        return True

    except Exception as e:
        logger.error(f"  ❌ Erro ao corrigir match {match.id}: {e}")
        db.rollback()
        return False


def main():
    parser = argparse.ArgumentParser(description='Corrige partidas travadas')
    parser.add_argument('--dry-run', action='store_true', help='Apenas simula, não modifica')
    parser.add_argument('--hours', type=int, default=2, help='Horas após início para considerar travado')

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("🔧 CORREÇÃO DE PARTIDAS TRAVADAS")
    logger.info("=" * 80)

    if args.dry_run:
        logger.info("⚠️ Modo DRY-RUN ativado - nenhuma alteração será feita")

    logger.info(f"⏱️ Threshold: Partidas com +{args.hours}h desde início")
    logger.info("=" * 80)

    # Database session
    db = SessionLocal()

    try:
        # Encontrar partidas travadas
        stuck_matches = find_stuck_matches(db, args.hours)

        if not stuck_matches:
            logger.info("\n✅ Nenhuma partida travada encontrada!")
            return

        logger.info(f"\n🔍 Encontradas {len(stuck_matches)} partidas travadas:\n")

        # Corrigir cada uma
        success_count = 0
        fail_count = 0

        for i, match in enumerate(stuck_matches, 1):
            logger.info(f"[{i}/{len(stuck_matches)}]")

            if fix_stuck_match(db, match, dry_run=args.dry_run):
                success_count += 1
            else:
                fail_count += 1

            logger.info("")  # Linha em branco

        # Resumo
        logger.info("=" * 80)
        logger.info("📊 RESUMO DA CORREÇÃO")
        logger.info("=" * 80)
        logger.info(f"Total processadas: {len(stuck_matches)}")
        logger.info(f"✅ Sucesso: {success_count}")
        logger.info(f"❌ Falhas: {fail_count}")

        if args.dry_run:
            logger.info("\n⚠️ Modo DRY-RUN - Execute sem --dry-run para aplicar as correções")
        else:
            logger.info("\n✅ Correções aplicadas com sucesso!")

        logger.info("=" * 80)

    finally:
        db.close()


if __name__ == '__main__':
    main()
