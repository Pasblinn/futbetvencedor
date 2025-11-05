#!/usr/bin/env python3
"""
🔧 Atualiza o Spider Principal com Sites Funcionais
Integra apenas os sites que foram testados e funcionaram
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_spider_configs():
    """Atualiza configurações do spider com sites funcionais"""

    # Configurações baseadas nos testes reais
    working_sites = {
        'pt.wikipedia.org': {
            'strategy': ['requests', 'scrapy'],
            'delay': 2,
            'use_proxy': False,  # Wikipedia não precisa
            'table_selectors': ['table.wikitable', 'table'],
            'success_rate': 1.0,
            'last_tested': '2024-09-24',
            'status': 'WORKING'
        },
        'en.wikipedia.org': {
            'strategy': ['requests', 'scrapy'],
            'delay': 2,
            'use_proxy': False,
            'table_selectors': ['table.wikitable', 'table'],
            'success_rate': 1.0,
            'last_tested': '2024-09-24',
            'status': 'WORKING'
        },
        'ge.globo.com': {
            'strategy': ['requests', 'requests_html'],
            'delay': 3,
            'use_proxy': False,
            'table_selectors': ['.tabela', '.classificacao', '.fixture'],
            'custom_parser': 'globo_parser',
            'success_rate': 0.7,
            'last_tested': '2024-09-24',
            'status': 'CONTENT_AVAILABLE'
        },
        'terra.com.br': {
            'strategy': ['requests', 'requests_html'],
            'delay': 3,
            'use_proxy': False,
            'table_selectors': ['.tabela', '.classificacao'],
            'custom_parser': 'terra_parser',
            'success_rate': 0.7,
            'last_tested': '2024-09-24',
            'status': 'CONTENT_AVAILABLE'
        }
    }

    # Sites problemáticos (para referência)
    problematic_sites = {
        'fbref.com': {
            'strategy': ['undetected_chrome', 'proxy_requests'],
            'delay': 5,
            'use_proxy': True,
            'issue': 'HTTP 403 - Strong anti-bot',
            'success_rate': 0.0,
            'last_tested': '2024-09-24',
            'status': 'BLOCKED'
        },
        'sofascore.com': {
            'strategy': ['undetected_chrome', 'proxy_requests'],
            'delay': 10,
            'use_proxy': True,
            'issue': 'HTTP 403 - Cloudflare',
            'success_rate': 0.0,
            'last_tested': '2024-09-24',
            'status': 'BLOCKED'
        },
        'oddspedia.com': {
            'strategy': ['selenium', 'proxy_requests'],
            'delay': 8,
            'use_proxy': True,
            'issue': 'HTTP 403 - Anti-bot',
            'success_rate': 0.0,
            'last_tested': '2024-09-24',
            'status': 'BLOCKED'
        }
    }

    # URLs de competições funcionais
    working_urls = {
        'brasileirao_2024': [
            'https://pt.wikipedia.org/wiki/Campeonato_Brasileiro_de_Futebol_de_2024_-_S%C3%A9rie_A',
            'https://en.wikipedia.org/wiki/2024_Campeonato_Brasileiro_S%C3%A9rie_A',
            'https://ge.globo.com/futebol/brasileirao-serie-a/',
            'https://www.terra.com.br/esportes/futebol/brasileiro-serie-a/'
        ],
        'github_data': [
            'https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/en.1.json'
        ]
    }

    logger.info("🔧 CONFIGURAÇÕES ATUALIZADAS DO SPIDER")
    logger.info("=" * 50)

    logger.info("✅ SITES FUNCIONAIS:")
    for site, config in working_sites.items():
        logger.info(f"   • {site}: {config['status']} (Taxa: {config['success_rate']*100:.0f}%)")

    logger.info("\n❌ SITES PROBLEMÁTICOS:")
    for site, config in problematic_sites.items():
        logger.info(f"   • {site}: {config['issue']}")

    logger.info(f"\n🎯 URLs TESTADAS E FUNCIONAIS: {len(sum(working_urls.values(), []))}")

    return {
        'working_sites': working_sites,
        'problematic_sites': problematic_sites,
        'working_urls': working_urls
    }

def create_production_spider_config():
    """Cria arquivo de configuração para produção"""
    config = update_spider_configs()

    spider_config = {
        'SITE_CONFIGS': config['working_sites'],
        'BLOCKED_SITES': config['problematic_sites'],
        'COMPETITION_URLS': {
            'brasileirao': {
                '2024': config['working_urls']['brasileirao_2024']
            }
        },
        'DEFAULT_SETTINGS': {
            'DOWNLOAD_DELAY': 3,
            'CONCURRENT_REQUESTS': 2,
            'RESPECT_ROBOTS_TXT': True,
            'USER_AGENT_ROTATION': True,
            'RETRY_ENABLED': True,
            'RETRY_TIMES': 3
        }
    }

    # Salva configuração
    import json
    with open('/home/pablintadini/mododeus/football-analytics/backend/working_spider_config.json', 'w') as f:
        json.dump(spider_config, f, indent=2, ensure_ascii=False)

    logger.info("💾 Configuração salva em: working_spider_config.json")

    return spider_config

def recommend_next_steps():
    """Recomendações baseadas nos testes"""
    logger.info("\n" + "=" * 60)
    logger.info("💡 RECOMENDAÇÕES PARA PRODUÇÃO")
    logger.info("=" * 60)

    logger.info("🚀 IMPLEMENTAÇÃO IMEDIATA (Prioridade 1):")
    logger.info("   1. Atualizar football_spider.py com sites funcionais")
    logger.info("   2. Implementar parsers customizados para Globo/Terra")
    logger.info("   3. Configurar pipeline automático com Wikipedia")
    logger.info("   4. Testar integração completa com ML")

    logger.info("\n🔧 MELHORIAS FUTURAS (Prioridade 2):")
    logger.info("   1. Implementar proxies premium para sites bloqueados")
    logger.info("   2. Desenvolver sistema de CAPTCHA solving")
    logger.info("   3. Buscar APIs oficiais (CBF, clubes)")
    logger.info("   4. Implementar cache inteligente")

    logger.info("\n📊 ESTRATÉGIA DE DADOS:")
    logger.info("   • Fonte primária: Wikipedia (100% confiável)")
    logger.info("   • Fonte secundária: Sites brasileiros acessíveis")
    logger.info("   • Backup: GitHub OpenFootball API")
    logger.info("   • Fallback: Dados históricos em cache")

    logger.info("\n⚡ IMPLEMENTAÇÃO RÁPIDA - PRÓXIMOS 30 MINUTOS:")
    logger.info("   1. Modificar football_spider.py")
    logger.info("   2. Testar scraping da Wikipedia")
    logger.info("   3. Executar pipeline ML com dados reais")
    logger.info("   4. Validar integração frontend")

def main():
    logger.info("🔄 ATUALIZANDO CONFIGURAÇÕES DO SPIDER...")

    # Atualiza configurações baseadas nos testes
    config = update_spider_configs()

    # Cria configuração de produção
    prod_config = create_production_spider_config()

    # Mostra recomendações
    recommend_next_steps()

    logger.info(f"\n🎉 CONFIGURAÇÃO COMPLETA!")
    logger.info("🚀 Pronto para implementar spider de produção com dados reais!")

if __name__ == '__main__':
    main()