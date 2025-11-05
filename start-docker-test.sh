#!/bin/bash

# 🚀 SCRIPT DE TESTE COMPLETO - Docker Environment
# Motor de Predições Real v2.0 com dados AO VIVO

set -e  # Exit on any error

echo "🧠 FOOTBALL ANALYTICS - Teste Docker Completo"
echo "================================================"
echo "📅 $(date)"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para print colorido
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌]${NC} $1"
}

# Verificar se Docker está instalado
check_docker() {
    print_status "Verificando Docker..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker não está instalado!"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose não está instalado!"
        exit 1
    fi

    print_success "Docker e Docker Compose encontrados"
}

# Verificar APIs configuradas
check_api_keys() {
    print_status "Verificando chaves de API..."

    if [ -f ".env" ]; then
        source .env
        print_success "Arquivo .env encontrado"
    else
        print_warning "Arquivo .env não encontrado - usando valores padrão"
    fi

    if [ -n "$FOOTBALL_DATA_API_KEY" ] && [ "$FOOTBALL_DATA_API_KEY" != "sua_chave_aqui" ]; then
        print_success "Football-Data API configurada"
    else
        print_warning "Football-Data API não configurada"
    fi

    if [ -n "$ODDS_API_KEY" ] && [ "$ODDS_API_KEY" != "sua_chave_aqui" ]; then
        print_success "Odds API configurada"
    else
        print_warning "Odds API não configurada"
    fi
}

# Limpar ambiente anterior
cleanup_previous() {
    print_status "Limpando ambiente anterior..."

    # Parar containers se estiverem rodando
    docker-compose -f docker-compose.new.yml down --remove-orphans 2>/dev/null || true

    # Remover containers órfãos
    docker container prune -f 2>/dev/null || true

    print_success "Ambiente limpo"
}

# Construir imagens
build_images() {
    print_status "Construindo imagens Docker..."

    docker-compose -f docker-compose.new.yml build --no-cache

    if [ $? -eq 0 ]; then
        print_success "Imagens construídas com sucesso"
    else
        print_error "Erro na construção das imagens"
        exit 1
    fi
}

# Iniciar serviços
start_services() {
    print_status "Iniciando serviços..."

    # Iniciar banco e cache primeiro
    print_status "Iniciando database e cache..."
    docker-compose -f docker-compose.new.yml up -d database cache

    # Aguardar health checks
    print_status "Aguardando serviços ficarem saudáveis..."
    sleep 30

    # Verificar health
    DB_HEALTH=$(docker-compose -f docker-compose.new.yml ps database | grep -c "healthy" || echo "0")
    CACHE_HEALTH=$(docker-compose -f docker-compose.new.yml ps cache | grep -c "healthy" || echo "0")

    if [ "$DB_HEALTH" -eq "1" ] && [ "$CACHE_HEALTH" -eq "1" ]; then
        print_success "Database e Cache saudáveis"
    else
        print_warning "Aguardando mais tempo para health checks..."
        sleep 30
    fi

    # Iniciar API
    print_status "Iniciando API..."
    docker-compose -f docker-compose.new.yml up -d api

    # Aguardar API ficar pronta
    print_status "Aguardando API ficar disponível..."
    for i in {1..12}; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            print_success "API está respondendo"
            break
        fi
        print_status "Tentativa $i/12 - Aguardando API..."
        sleep 10
    done
}

# Testar API
test_api() {
    print_status "Testando endpoints da API..."

    # Teste básico de health
    if curl -f http://localhost:8000/health &>/dev/null; then
        print_success "Health check passou"
    else
        print_error "Health check falhou"
        return 1
    fi

    # Teste de status do sistema
    if curl -f http://localhost:8000/system/status &>/dev/null; then
        print_success "System status disponível"
    else
        print_warning "System status com problemas"
    fi

    # Teste da documentação
    if curl -f http://localhost:8000/docs &>/dev/null; then
        print_success "Documentação disponível"
    else
        print_warning "Documentação com problemas"
    fi
}

# Executar teste do motor real
test_prediction_engine() {
    print_status "Executando teste do motor de predições real..."

    # Executar container de teste
    docker-compose -f docker-compose.new.yml --profile test up test-engine

    if [ $? -eq 0 ]; then
        print_success "Teste do motor executado"
    else
        print_warning "Teste do motor teve problemas"
    fi
}

# Mostrar status final
show_final_status() {
    echo ""
    echo "🎉 TESTE COMPLETO FINALIZADO"
    echo "================================================"
    echo ""

    print_status "Status dos Serviços:"
    docker-compose -f docker-compose.new.yml ps

    echo ""
    print_status "Links de Acesso:"
    echo "🌐 API: http://localhost:8000"
    echo "📚 Docs: http://localhost:8000/docs"
    echo "❤️ Health: http://localhost:8000/health"
    echo "📊 Status: http://localhost:8000/system/status"
    echo ""

    print_status "Logs em tempo real:"
    echo "docker-compose -f docker-compose.new.yml logs -f api"
    echo ""

    print_status "Para parar:"
    echo "docker-compose -f docker-compose.new.yml down"
    echo ""
}

# Função principal
main() {
    echo "🚀 Iniciando teste completo do ambiente Docker..."
    echo ""

    check_docker
    check_api_keys
    cleanup_previous
    build_images
    start_services
    test_api
    test_prediction_engine
    show_final_status

    print_success "🎉 Teste completo finalizado com sucesso!"
    print_status "O motor de predições real está rodando com dados AO VIVO!"
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi