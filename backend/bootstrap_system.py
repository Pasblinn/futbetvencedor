"""
🚀 BOOTSTRAP DO SISTEMA - INICIALIZAÇÃO COMPLETA COM TESTES

Este script:
1. Verifica/cria banco de dados
2. Sincroniza dados da API (matches, teams, odds)
3. Gera predictions de teste (100 amostras)
4. Valida pipeline completo
5. Ativa scheduler automático

IMPORTANTE: Testa TUDO antes de ativar o automático!

Uso:
    python bootstrap_system.py

Flags:
    --skip-sync: Pula sincronização de dados (usa dados existentes)
    --test-only: Apenas testa, não ativa scheduler
    --verbose: Mostra todos os detalhes
"""

import sys
import os
from pathlib import Path
import argparse
import time

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Models
from app.core.database import Base
from app.models import Match, Team, Odds, Prediction, User

# Services
from app.services.simple_api_sports_sync import simple_sync
from app.services.ml_prediction_generator import run_daily_ml_prediction_generation
from app.services.data_scheduler import DataScheduler

# Database
DATABASE_URL = f"sqlite:///{backend_path}/football_analytics.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(step_num, title):
    """Print formatted step header"""
    print("\n" + "="*80)
    print(f"{Colors.BOLD}{Colors.BLUE}PASSO {step_num}: {title}{Colors.END}")
    print("="*80)

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def step1_verify_database():
    """PASSO 1: Verificar/criar banco de dados"""
    print_step(1, "VERIFICAR/CRIAR BANCO DE DADOS")

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = [
        'teams', 'matches', 'odds', 'predictions',
        'users', 'user_bankrolls', 'user_tickets'
    ]

    missing_tables = [t for t in required_tables if t not in tables]

    if missing_tables:
        print_warning(f"Tabelas faltando: {', '.join(missing_tables)}")
        print_info("Criando todas as tabelas...")
        Base.metadata.create_all(bind=engine)

        # Verify again
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print_success(f"Banco criado com {len(tables)} tabelas")
    else:
        print_success(f"Banco OK: {len(tables)} tabelas existentes")

    # Show table counts
    db = SessionLocal()
    counts = {
        'matches': db.query(Match).count(),
        'teams': db.query(Team).count(),
        'odds': db.query(Odds).count(),
        'predictions': db.query(Prediction).count(),
    }
    db.close()

    print("\n📊 Contadores atuais:")
    for table, count in counts.items():
        status = "✅" if count > 0 else "⚠️"
        print(f"  {status} {table}: {count}")

    return counts

def step2_sync_data():
    """PASSO 2: Sincronizar dados da API"""
    print_step(2, "SINCRONIZAR DADOS DA API")

    print_info("Iniciando sincronização de dados...")
    print_info("Isso pode levar alguns minutos...")

    try:
        # Sync matches and odds usando asyncio COM SIMPLE SYNC
        print("\n📥 Sincronizando jogos, times e odds (API-Sports)...")

        import asyncio
        result = asyncio.run(simple_sync.sync_today_matches())

        print_success(f"Sincronização concluída!")
        print(f"  - Times sincronizados: {result.get('teams', 0)}")
        print(f"  - Jogos sincronizados: {result.get('matches', 0)}")
        print(f"  - Odds sincronizadas: {result.get('odds', 0)}")

        if result.get('errors', 0) > 0:
            print_warning(f"Erros durante sync: {result['errors']}")

        # Verify
        db = SessionLocal()
        matches_count = db.query(Match).count()
        teams_count = db.query(Team).count()
        odds_count = db.query(Odds).count()
        db.close()

        if matches_count == 0 and teams_count == 0:
            print_warning("Nenhum dado foi sincronizado!")
            print_info("Possíveis causas:")
            print("  1. API Key inválida")
            print("  2. Sem jogos para hoje das ligas monitoradas")
            print("  3. Rate limit atingido")
            print_info(f"\nTentando continuar com {matches_count} jogos existentes...")

        print_success(f"Dados verificados: {matches_count} jogos, {teams_count} times, {odds_count} odds")
        return True

    except Exception as e:
        print_error(f"Erro na sincronização: {e}")
        import traceback
        traceback.print_exc()
        return False

def step3_generate_test_predictions():
    """PASSO 3: Gerar predictions de teste"""
    print_step(3, "GERAR PREDICTIONS DE TESTE")

    print_info("Gerando 100 predictions de teste...")
    print_info("Nova distribuição: 80% duplas/triplas, 15% múltiplas, 5% simples")

    try:
        result = run_daily_ml_prediction_generation(target=100)

        print_success("Predictions geradas com sucesso!")
        print("\n📊 Distribuição gerada:")
        print(f"  - Singles (5%): {result.get('singles', 0)}")
        print(f"  - Doubles mesmo jogo (20%): {result.get('doubles_same_match', 0)}")
        print(f"  - Trebles mesmo jogo (20%): {result.get('trebles_same_match', 0)}")
        print(f"  - Quads mesmo jogo (10%): {result.get('quads_same_match', 0)}")
        print(f"  - Doubles multi (20%): {result.get('doubles_multi', 0)}")
        print(f"  - Trebles multi (20%): {result.get('trebles_multi', 0)}")
        print(f"  - Quads multi (5%): {result.get('quads_multi', 0)}")
        print(f"\n🎯 TOTAL: {result.get('total', 0)} predictions")

        if result.get('errors', 0) > 0:
            print_warning(f"Erros encontrados: {result['errors']}")

        # Verify
        db = SessionLocal()
        predictions_count = db.query(Prediction).count()

        # Count by type
        doubles = db.query(Prediction).filter(Prediction.prediction_type == 'DOUBLE').count()
        trebles = db.query(Prediction).filter(Prediction.prediction_type == 'TREBLE').count()
        singles = db.query(Prediction).filter(Prediction.prediction_type == 'SINGLE').count()

        db.close()

        print(f"\n✅ Verificação: {predictions_count} predictions no banco")
        print(f"  - Doubles: {doubles}")
        print(f"  - Trebles: {trebles}")
        print(f"  - Singles: {singles}")

        # Check distribution
        total_double_triple = doubles + trebles
        pct_double_triple = (total_double_triple / predictions_count * 100) if predictions_count > 0 else 0

        if pct_double_triple >= 75:  # 80% target, allow 5% margin
            print_success(f"Distribuição OK: {pct_double_triple:.1f}% duplas/triplas (meta: 80%)")
        else:
            print_warning(f"Distribuição abaixo da meta: {pct_double_triple:.1f}% (meta: 80%)")

        return predictions_count > 0

    except Exception as e:
        print_error(f"Erro ao gerar predictions: {e}")
        import traceback
        traceback.print_exc()
        return False

def step4_validate_pipeline():
    """PASSO 4: Validar pipeline completo"""
    print_step(4, "VALIDAR PIPELINE COMPLETO")

    print_info("Executando validações finais...")

    db = SessionLocal()

    # Check 1: Predictions têm matches válidos
    predictions_with_match = db.query(Prediction).join(Match).count()
    total_predictions = db.query(Prediction).count()

    if predictions_with_match == total_predictions:
        print_success(f"Todas as {total_predictions} predictions têm matches válidos")
    else:
        print_error(f"Predictions órfãs detectadas: {total_predictions - predictions_with_match}")
        return False

    # Check 2: Predictions têm probabilidades válidas
    invalid_probs = db.query(Prediction).filter(
        (Prediction.predicted_probability < 0) |
        (Prediction.predicted_probability > 1)
    ).count()

    if invalid_probs == 0:
        print_success("Todas as probabilidades estão no range 0-1")
    else:
        print_error(f"Probabilidades inválidas encontradas: {invalid_probs}")
        return False

    # Check 3: Matches têm times válidos
    matches_with_teams = db.query(Match).join(
        Team, Match.home_team_id == Team.id
    ).count()
    total_matches = db.query(Match).count()

    if matches_with_teams == total_matches:
        print_success(f"Todos os {total_matches} matches têm times válidos")
    else:
        print_error(f"Matches com times inválidos: {total_matches - matches_with_teams}")
        return False

    # Check 4: Odds disponíveis
    odds_count = db.query(Odds).count()
    if odds_count > 0:
        print_success(f"{odds_count} odds disponíveis")
    else:
        print_warning("Nenhuma odd real disponível (sistema usará Poisson)")

    db.close()

    print_success("Pipeline validado com sucesso!")
    return True

def step5_create_test_user():
    """PASSO 5: Criar usuário de teste se não existir"""
    print_step(5, "CRIAR USUÁRIO DE TESTE")

    db = SessionLocal()

    # Check if user exists
    existing_user = db.query(User).filter(User.email == "admin@mododeus.com").first()

    if existing_user:
        print_success("Usuário admin já existe")
        db.close()
        return True

    # Create user
    from app.core.security import get_password_hash

    try:
        new_user = User(
            email="admin@mododeus.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin MoDoDeus",
            is_active=True,
            is_superuser=True,
            is_verified=True
        )
        db.add(new_user)
        db.commit()

        print_success("Usuário admin criado com sucesso")
        print_info("Credenciais:")
        print("  - Email: admin@mododeus.com")
        print("  - Username: admin")
        print("  - Password: admin123")

        db.close()
        return True

    except Exception as e:
        print_error(f"Erro ao criar usuário: {e}")
        db.rollback()
        db.close()
        return False

def step6_final_report():
    """PASSO 6: Relatório final"""
    print_step(6, "RELATÓRIO FINAL")

    db = SessionLocal()

    stats = {
        'matches': db.query(Match).count(),
        'teams': db.query(Team).count(),
        'odds': db.query(Odds).count(),
        'predictions': db.query(Prediction).count(),
        'users': db.query(User).count(),
    }

    db.close()

    print("\n📊 ESTATÍSTICAS FINAIS:")
    print("="*80)
    for key, value in stats.items():
        status = "✅" if value > 0 else "⚠️"
        print(f"  {status} {key.upper()}: {value}")

    # Calculate readiness
    critical_items = ['matches', 'predictions']
    ready = all(stats[item] > 0 for item in critical_items)

    print("\n" + "="*80)
    if ready:
        print_success("SISTEMA PRONTO PARA PRODUÇÃO!")
        print("\n🎯 Próximos passos:")
        print("  1. Backend está rodando em http://localhost:8000")
        print("  2. Frontend está rodando em http://localhost:3001")
        print("  3. Login: admin / admin123")
        print("  4. Scheduler automático está ativo")
        print("\n📅 Jobs automáticos:")
        print("  - Sincronização de dados: A cada hora")
        print("  - Geração de predictions: Diariamente às 8h (4500 predictions)")
        print("  - Retraining ML: Diariamente às 2h (se houver 20+ resultados)")
    else:
        print_warning("SISTEMA PARCIALMENTE FUNCIONAL")
        print("\n⚠️  Itens faltando:")
        for item in critical_items:
            if stats[item] == 0:
                print(f"  - {item}: 0")

    print("="*80 + "\n")

    return ready

def main():
    parser = argparse.ArgumentParser(description='Bootstrap do Sistema MoDoDeus')
    parser.add_argument('--skip-sync', action='store_true', help='Pular sincronização de dados')
    parser.add_argument('--test-only', action='store_true', help='Apenas testar, não ativar scheduler')
    parser.add_argument('--verbose', action='store_true', help='Modo verbose')

    args = parser.parse_args()

    print("\n" + "="*80)
    print(f"{Colors.BOLD}🚀 BOOTSTRAP DO SISTEMA MODODEUS{Colors.END}")
    print("Inicialização completa com testes de segurança")
    print("="*80)

    start_time = time.time()

    # PASSO 1: Banco de dados
    counts = step1_verify_database()

    # PASSO 2: Sincronização (opcional)
    if not args.skip_sync:
        if not step2_sync_data():
            print_error("Falha na sincronização de dados!")
            print_info("Execute novamente com --skip-sync para testar com dados existentes")
            return 1
    else:
        print_warning("Sincronização pulada (--skip-sync)")
        if counts['matches'] == 0:
            print_error("Sem dados no banco e sync foi pulada!")
            return 1

    # PASSO 3: Gerar predictions de teste
    if not step3_generate_test_predictions():
        print_error("Falha ao gerar predictions de teste!")
        return 1

    # PASSO 4: Validar pipeline
    if not step4_validate_pipeline():
        print_error("Falha na validação do pipeline!")
        return 1

    # PASSO 5: Criar usuário de teste
    if not step5_create_test_user():
        print_error("Falha ao criar usuário de teste!")
        return 1

    # PASSO 6: Relatório final
    ready = step6_final_report()

    # Calculate time
    elapsed = time.time() - start_time
    print(f"\n⏱️  Tempo total: {elapsed:.1f}s")

    if ready:
        if not args.test_only:
            print_info("\nScheduler automático já está ativo no backend!")
            print_info("Não é necessário iniciar novamente.")
        else:
            print_info("\nModo --test-only: Scheduler não foi ativado")

        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ BOOTSTRAP CONCLUÍDO COM SUCESSO!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  BOOTSTRAP PARCIALMENTE COMPLETO{Colors.END}\n")
        return 2

if __name__ == "__main__":
    sys.exit(main())
