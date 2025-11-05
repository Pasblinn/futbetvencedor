#!/bin/bash

# 🚀 START BACKEND - Sistema Automatizado MoDoDeus

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 INICIANDO BACKEND - MoDoDeus Football Analytics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ativar venv
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Verificar se Ollama está rodando
echo "🧠 Verificando Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama está rodando"
else
    echo "⚠️  Ollama não detectado em http://localhost:11434"
    echo "   Para iniciar: ollama serve"
fi

# Criar diretório de logs se não existir
mkdir -p logs

# Limpar log de erros se estiver muito grande (>100MB)
if [ -f "logs/scheduler_error.log" ]; then
    size=$(du -m logs/scheduler_error.log | cut -f1)
    if [ $size -gt 100 ]; then
        echo "🧹 Log de erros muito grande (${size}MB), truncando..."
        tail -1000 logs/scheduler_error.log > logs/scheduler_error.log.tmp
        mv logs/scheduler_error.log.tmp logs/scheduler_error.log
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 SISTEMA AUTOMATIZADO ATIVO (12 JOBS):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📥 Importar Jogos (próximos 7 dias)  → 4x/dia (00h, 06h, 12h, 18h)"
echo "🔴 Atualizar Jogos AO VIVO           → A cada 2 minutos"
echo "🧠 Gerar Predictions ML              → A cada 6 horas"
echo "🧠 Análise AI Agent (TOP 100)        → A cada 2 horas ⚡"
echo "🤖 ML Retraining                     → Diário às 02:00 🎉"
echo "🧹 Limpar Jogos Finalizados          → A cada 1 hora"
echo "🏆 Normalizar Nomes de Ligas         → Diário às 03:00"
echo "🔄 Atualizar Resultados [LEGACY]     → A cada 1 hora"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 DICAS:"
echo "   - Para monitorar jobs: ./monitor_scheduler.sh"
echo "   - Logs em: logs/scheduler.log e logs/scheduler_error.log"
echo "   - Para parar: Ctrl+C"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Iniciando servidor FastAPI..."
echo ""

# Iniciar backend com uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
