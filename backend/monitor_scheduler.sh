#!/bin/bash

# 🔍 MONITOR DE SCHEDULER - Sistema de Automação MoDoDeus
# Monitora execução dos 12 jobs automáticos

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 MONITOR DE SCHEDULER - MoDoDeus Football Analytics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ativar venv
source venv/bin/activate

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função principal
show_menu() {
    echo "Escolha uma opção:"
    echo ""
    echo "  1) 📊 Status do Scheduler (jobs ativos)"
    echo "  2) 📝 Últimos logs (tail -50)"
    echo "  3) 🔴 Erros recentes (últimas 20 linhas)"
    echo "  4) 🧠 Logs do AI Agent"
    echo "  5) 🤖 Logs do ML Retraining"
    echo "  6) 📥 Logs de Importação"
    echo "  7) 🔄 Logs de Predictions"
    echo "  8) 📈 Estatísticas do Banco (predictions, matches)"
    echo "  9) 🧹 Limpar logs antigos (>100MB)"
    echo "  0) ❌ Sair"
    echo ""
}

# 1. Status do Scheduler
show_scheduler_status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 STATUS DO SCHEDULER${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    python -c "
from app.core.scheduler import scheduler

if scheduler.running:
    print('\n✅ Scheduler ATIVO\n')
    print('📋 Jobs Registrados:\n')

    for job in scheduler.get_jobs():
        print(f'  🔹 {job.id}')
        print(f'     Nome: {job.name}')
        print(f'     Trigger: {job.trigger}')
        if job.next_run_time:
            print(f'     Próxima execução: {job.next_run_time}')
        print()
else:
    print('\n❌ Scheduler INATIVO\n')
"
}

# 2. Últimos logs
show_recent_logs() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📝 ÚLTIMOS 50 LOGS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [ -f "logs/scheduler.log" ]; then
        tail -50 logs/scheduler.log | grep -E "(INFO|ERROR|WARNING)" | tail -20
    else
        echo "❌ Arquivo logs/scheduler.log não encontrado"
    fi
}

# 3. Erros recentes
show_errors() {
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}🔴 ERROS RECENTES${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [ -f "logs/scheduler_error.log" ]; then
        tail -100 logs/scheduler_error.log | grep -E "ERROR|Exception|Traceback" | tail -20
    else
        echo "✅ Nenhum erro encontrado"
    fi
}

# 4. AI Agent logs
show_ai_logs() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🧠 LOGS DO AI AGENT${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    tail -200 logs/scheduler.log 2>/dev/null | grep -E "(AI Agent|ai_batch_analysis|🧠)" | tail -15
}

# 5. ML Retraining logs
show_ml_logs() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🤖 LOGS DO ML RETRAINING${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    tail -200 logs/scheduler.log 2>/dev/null | grep -E "(ML Retraining|ml_retraining|🤖)" | tail -15
}

# 6. Importação logs
show_import_logs() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📥 LOGS DE IMPORTAÇÃO${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    tail -200 logs/scheduler.log 2>/dev/null | grep -E "(Importar|import_upcoming|📥)" | tail -15
}

# 7. Predictions logs
show_predictions_logs() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🔄 LOGS DE PREDICTIONS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    tail -200 logs/scheduler.log 2>/dev/null | grep -E "(Predictions|generate_predictions|🔄)" | tail -15
}

# 8. Estatísticas do banco
show_database_stats() {
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📈 ESTATÍSTICAS DO BANCO${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    python -c "
from app.core.database import get_db_session
from app.models import Match, Prediction
from sqlalchemy import func
from datetime import datetime

db = get_db_session()

try:
    # Matches
    total_matches = db.query(Match).count()
    upcoming_matches = db.query(Match).filter(Match.match_date >= datetime.now()).count()

    # Predictions
    total_predictions = db.query(Prediction).count()
    ai_analyzed = db.query(Prediction).filter(Prediction.ai_analyzed == True).count()

    # Results
    greens = db.query(Prediction).filter(Prediction.is_winner == True).count()
    reds = db.query(Prediction).filter(Prediction.is_winner == False).count()
    pending = total_predictions - greens - reds

    accuracy = (greens / (greens + reds) * 100) if (greens + reds) > 0 else 0

    print(f'\n📊 MATCHES:')
    print(f'  Total: {total_matches}')
    print(f'  Próximos: {upcoming_matches}')
    print(f'\n🧠 PREDICTIONS:')
    print(f'  Total: {total_predictions}')
    print(f'  Analisadas por AI: {ai_analyzed}')
    print(f'\n📈 RESULTADOS:')
    print(f'  🟢 GREENS: {greens}')
    print(f'  🔴 REDS: {reds}')
    print(f'  ⏳ Pendentes: {pending}')
    print(f'  📊 Accuracy: {accuracy:.1f}%')
    print()

finally:
    db.close()
"
}

# 9. Limpar logs
clean_logs() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🧹 LIMPANDO LOGS GRANDES (>100MB)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    find logs/ -type f -size +100M -exec sh -c '
        for file; do
            echo "🗑️  Truncando: $file"
            tail -1000 "$file" > "$file.tmp" && mv "$file.tmp" "$file"
        done
    ' sh {} +

    echo "✅ Limpeza concluída"
}

# Loop do menu
while true; do
    echo ""
    show_menu
    read -p "Opção: " choice
    echo ""

    case $choice in
        1) show_scheduler_status ;;
        2) show_recent_logs ;;
        3) show_errors ;;
        4) show_ai_logs ;;
        5) show_ml_logs ;;
        6) show_import_logs ;;
        7) show_predictions_logs ;;
        8) show_database_stats ;;
        9) clean_logs ;;
        0) echo "👋 Até logo!"; exit 0 ;;
        *) echo "❌ Opção inválida" ;;
    esac

    echo ""
    read -p "Pressione Enter para continuar..."
done
