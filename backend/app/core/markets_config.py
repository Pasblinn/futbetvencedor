"""
🎯 CONFIGURAÇÃO COMPLETA DE MERCADOS DE APOSTAS
Mapeamento de todos os mercados disponíveis para football analytics
Baseado em API-Football odds markets e principais bookmakers
"""

# Mapeamento de IDs de mercados da API-Football
# Ref: https://www.api-football.com/documentation-v3#tag/Odds/operation/get-odds
MARKET_IDS = {
    # ============= MERCADOS PRINCIPAIS =============
    "1X2": 1,                           # Resultado Final (Home/Draw/Away)
    "DOUBLE_CHANCE": 2,                 # Dupla Hipótese (1X, 12, X2)
    "OVER_UNDER": 5,                    # Total de Gols (Over/Under 2.5, 1.5, 3.5, etc)
    "BTTS": 8,                          # Both Teams To Score (Sim/Não)
    "CORRECT_SCORE": 9,                 # Placar Exato

    # ============= PRIMEIRO/SEGUNDO TEMPO =============
    "HALFTIME_RESULT": 10,              # Resultado 1º Tempo
    "HALFTIME_OVER_UNDER": 11,          # Over/Under 1º Tempo
    "HALFTIME_BTTS": 12,                # BTTS 1º Tempo
    "SECOND_HALF_RESULT": 13,           # Resultado 2º Tempo
    "SECOND_HALF_OVER_UNDER": 14,       # Over/Under 2º Tempo

    # ============= HANDICAP =============
    "ASIAN_HANDICAP": 3,                # Handicap Asiático (-1.5, -0.5, +1.5, etc)
    "EUROPEAN_HANDICAP": 4,             # Handicap Europeu (0:1, 1:0, etc)

    # ============= GOLS =============
    "FIRST_GOAL": 15,                   # Primeiro a Marcar
    "LAST_GOAL": 16,                    # Último a Marcar
    "ANYTIME_GOALSCORER": 17,           # Marcará a Qualquer Momento
    "EXACT_GOALS": 18,                  # Número Exato de Gols (0, 1, 2, 3+)
    "ODD_EVEN": 19,                     # Gols Par/Ímpar
    "GOALS_RANGE": 20,                  # Intervalo de Gols (0-1, 2-3, 4-6, 7+)
    "HOME_OVER_UNDER": 21,              # Over/Under Gols Casa
    "AWAY_OVER_UNDER": 22,              # Over/Under Gols Visitante
    "HOME_EXACT_GOALS": 23,             # Gols Exatos Casa
    "AWAY_EXACT_GOALS": 24,             # Gols Exatos Visitante

    # ============= ESCANTEIOS =============
    "CORNERS_OVER_UNDER": 25,           # Total de Escanteios Over/Under
    "CORNERS_1X2": 26,                  # Escanteios 1X2 (qual time terá mais)
    "CORNERS_ASIAN_HANDICAP": 27,       # Handicap Asiático Escanteios
    "CORNERS_EXACT": 28,                # Número Exato de Escanteios
    "FIRST_CORNER": 29,                 # Primeiro Escanteio
    "LAST_CORNER": 30,                  # Último Escanteio
    "HOME_CORNERS": 31,                 # Total Escanteios Casa
    "AWAY_CORNERS": 32,                 # Total Escanteios Visitante
    "CORNERS_HALFTIME": 33,             # Escanteios 1º Tempo

    # ============= CARTÕES =============
    "CARDS_OVER_UNDER": 35,             # Total de Cartões Over/Under
    "CARDS_1X2": 36,                    # Cartões 1X2 (qual time terá mais)
    "CARDS_ASIAN_HANDICAP": 37,         # Handicap Asiático Cartões
    "CARDS_EXACT": 38,                  # Número Exato de Cartões
    "FIRST_CARD": 39,                   # Primeiro Cartão
    "RED_CARD": 40,                     # Haverá Cartão Vermelho (Sim/Não)
    "HOME_CARDS": 41,                   # Total Cartões Casa
    "AWAY_CARDS": 42,                   # Total Cartões Visitante

    # ============= COMBINAÇÕES =============
    "RESULT_BTTS": 50,                  # Resultado + BTTS (ex: Home Win + BTTS Yes)
    "RESULT_OVER_UNDER": 51,            # Resultado + Over/Under
    "HALFTIME_FULLTIME": 52,            # Resultado 1º Tempo / Tempo Final
    "WIN_TO_NIL": 53,                   # Vencer Sem Sofrer Gols
    "WIN_BOTH_HALVES": 54,              # Vencer Ambos os Tempos
    "SCORE_BOTH_HALVES": 55,            # Marcar em Ambos os Tempos

    # ============= ESPECIAIS =============
    "PENALTY": 60,                      # Haverá Pênalti (Sim/Não)
    "PENALTY_SCORED": 61,               # Pênalti Convertido
    "OWN_GOAL": 62,                     # Haverá Gol Contra
    "HAT_TRICK": 63,                    # Haverá Hat-trick
    "CLEAN_SHEET": 64,                  # Clean Sheet (Casa/Visitante/Nenhum/Ambos)
    "COMEBACK": 65,                     # Haverá Virada

    # ============= ALTERNATIVOS =============
    "ALT_OVER_UNDER_15": 70,            # Over/Under 1.5 alternativo
    "ALT_OVER_UNDER_35": 71,            # Over/Under 3.5 alternativo
    "ALT_OVER_UNDER_45": 72,            # Over/Under 4.5 alternativo
    "ALT_ASIAN_HANDICAP": 73,           # Handicaps Asiáticos Alternativos
    "ALT_CORNERS": 74,                  # Escanteios Alternativos
    "ALT_CARDS": 75,                    # Cartões Alternativos
}

# Nomes amigáveis dos mercados (para display no frontend)
MARKET_NAMES = {
    # Principais
    "1X2": "Resultado Final",
    "DOUBLE_CHANCE": "Dupla Hipótese",
    "OVER_UNDER": "Total de Gols",
    "BTTS": "Ambas Marcam",
    "CORRECT_SCORE": "Placar Exato",

    # Tempo
    "HALFTIME_RESULT": "Resultado 1º Tempo",
    "HALFTIME_OVER_UNDER": "Gols 1º Tempo",
    "HALFTIME_BTTS": "Ambas Marcam 1º Tempo",
    "SECOND_HALF_RESULT": "Resultado 2º Tempo",
    "SECOND_HALF_OVER_UNDER": "Gols 2º Tempo",

    # Handicap
    "ASIAN_HANDICAP": "Handicap Asiático",
    "EUROPEAN_HANDICAP": "Handicap Europeu",

    # Gols
    "FIRST_GOAL": "Primeiro Gol",
    "LAST_GOAL": "Último Gol",
    "ANYTIME_GOALSCORER": "Marcará a Qualquer Momento",
    "EXACT_GOALS": "Número Exato de Gols",
    "ODD_EVEN": "Gols Par/Ímpar",
    "GOALS_RANGE": "Intervalo de Gols",
    "HOME_OVER_UNDER": "Total Gols Casa",
    "AWAY_OVER_UNDER": "Total Gols Visitante",
    "HOME_EXACT_GOALS": "Gols Exatos Casa",
    "AWAY_EXACT_GOALS": "Gols Exatos Visitante",

    # Escanteios
    "CORNERS_OVER_UNDER": "Total de Escanteios",
    "CORNERS_1X2": "Mais Escanteios",
    "CORNERS_ASIAN_HANDICAP": "Handicap Escanteios",
    "CORNERS_EXACT": "Escanteios Exatos",
    "FIRST_CORNER": "Primeiro Escanteio",
    "LAST_CORNER": "Último Escanteio",
    "HOME_CORNERS": "Escanteios Casa",
    "AWAY_CORNERS": "Escanteios Visitante",
    "CORNERS_HALFTIME": "Escanteios 1º Tempo",

    # Cartões
    "CARDS_OVER_UNDER": "Total de Cartões",
    "CARDS_1X2": "Mais Cartões",
    "CARDS_ASIAN_HANDICAP": "Handicap Cartões",
    "CARDS_EXACT": "Cartões Exatos",
    "FIRST_CARD": "Primeiro Cartão",
    "RED_CARD": "Cartão Vermelho",
    "HOME_CARDS": "Cartões Casa",
    "AWAY_CARDS": "Cartões Visitante",

    # Combinações
    "RESULT_BTTS": "Resultado + Ambas Marcam",
    "RESULT_OVER_UNDER": "Resultado + Total Gols",
    "HALFTIME_FULLTIME": "HT/FT",
    "WIN_TO_NIL": "Vencer Sem Sofrer",
    "WIN_BOTH_HALVES": "Vencer Ambos Tempos",
    "SCORE_BOTH_HALVES": "Marcar Ambos Tempos",

    # Especiais
    "PENALTY": "Haverá Pênalti",
    "PENALTY_SCORED": "Pênalti Convertido",
    "OWN_GOAL": "Gol Contra",
    "HAT_TRICK": "Hat-trick",
    "CLEAN_SHEET": "Clean Sheet",
    "COMEBACK": "Virada",

    # Alternativos
    "ALT_OVER_UNDER_15": "Total Gols (Alt 1.5)",
    "ALT_OVER_UNDER_35": "Total Gols (Alt 3.5)",
    "ALT_OVER_UNDER_45": "Total Gols (Alt 4.5)",
    "ALT_ASIAN_HANDICAP": "Handicap Asiático (Alt)",
    "ALT_CORNERS": "Escanteios (Alt)",
    "ALT_CARDS": "Cartões (Alt)",
}

# Categorias de mercados (para organização no frontend)
MARKET_CATEGORIES = {
    "main": {
        "name": "Mercados Principais",
        "icon": "⚽",
        "markets": ["1X2", "DOUBLE_CHANCE", "OVER_UNDER", "BTTS", "CORRECT_SCORE"]
    },
    "halftime": {
        "name": "Primeiro/Segundo Tempo",
        "icon": "⏱️",
        "markets": ["HALFTIME_RESULT", "HALFTIME_OVER_UNDER", "HALFTIME_BTTS",
                   "SECOND_HALF_RESULT", "SECOND_HALF_OVER_UNDER"]
    },
    "handicap": {
        "name": "Handicaps",
        "icon": "⚖️",
        "markets": ["ASIAN_HANDICAP", "EUROPEAN_HANDICAP"]
    },
    "goals": {
        "name": "Mercados de Gols",
        "icon": "🥅",
        "markets": ["FIRST_GOAL", "LAST_GOAL", "ANYTIME_GOALSCORER", "EXACT_GOALS",
                   "ODD_EVEN", "GOALS_RANGE", "HOME_OVER_UNDER", "AWAY_OVER_UNDER",
                   "HOME_EXACT_GOALS", "AWAY_EXACT_GOALS"]
    },
    "corners": {
        "name": "Escanteios",
        "icon": "🚩",
        "markets": ["CORNERS_OVER_UNDER", "CORNERS_1X2", "CORNERS_ASIAN_HANDICAP",
                   "CORNERS_EXACT", "FIRST_CORNER", "LAST_CORNER", "HOME_CORNERS",
                   "AWAY_CORNERS", "CORNERS_HALFTIME"]
    },
    "cards": {
        "name": "Cartões",
        "icon": "🟨",
        "markets": ["CARDS_OVER_UNDER", "CARDS_1X2", "CARDS_ASIAN_HANDICAP",
                   "CARDS_EXACT", "FIRST_CARD", "RED_CARD", "HOME_CARDS", "AWAY_CARDS"]
    },
    "combos": {
        "name": "Combinações",
        "icon": "🔀",
        "markets": ["RESULT_BTTS", "RESULT_OVER_UNDER", "HALFTIME_FULLTIME",
                   "WIN_TO_NIL", "WIN_BOTH_HALVES", "SCORE_BOTH_HALVES"]
    },
    "specials": {
        "name": "Mercados Especiais",
        "icon": "✨",
        "markets": ["PENALTY", "PENALTY_SCORED", "OWN_GOAL", "HAT_TRICK",
                   "CLEAN_SHEET", "COMEBACK"]
    },
    "alternatives": {
        "name": "Linhas Alternativas",
        "icon": "📊",
        "markets": ["ALT_OVER_UNDER_15", "ALT_OVER_UNDER_35", "ALT_OVER_UNDER_45",
                   "ALT_ASIAN_HANDICAP", "ALT_CORNERS", "ALT_CARDS"]
    }
}

# Prioridade dos mercados (ordem de exibição)
MARKET_PRIORITY = [
    "1X2",
    "DOUBLE_CHANCE",
    "OVER_UNDER",
    "BTTS",
    "ASIAN_HANDICAP",
    "CORRECT_SCORE",
    "HALFTIME_RESULT",
    "CORNERS_OVER_UNDER",
    "CARDS_OVER_UNDER",
    # ... resto em ordem alfabética
]

def get_market_id(market_name: str) -> int:
    """Retorna o ID do mercado na API-Football"""
    return MARKET_IDS.get(market_name)

def get_market_name(market_key: str) -> str:
    """Retorna o nome amigável do mercado"""
    return MARKET_NAMES.get(market_key, market_key)

def get_market_category(market_key: str) -> str:
    """Retorna a categoria do mercado"""
    for cat_key, cat_data in MARKET_CATEGORIES.items():
        if market_key in cat_data["markets"]:
            return cat_key
    return "other"

def get_all_markets() -> list:
    """Retorna lista de todos os mercados disponíveis"""
    return list(MARKET_IDS.keys())

def get_priority_markets(limit: int = 10) -> list:
    """Retorna os mercados prioritários para exibição"""
    return MARKET_PRIORITY[:limit]
