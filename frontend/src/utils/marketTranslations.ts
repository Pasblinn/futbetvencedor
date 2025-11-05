/**
 * 🎯 TRADUÇÕES DE MERCADOS - ESTILO BET365/BETANO
 *
 * Mapeia os IDs dos mercados (backend) para nomes em português
 * no estilo das casas de apostas brasileiras
 */

export interface Market {
  id: string;
  name: string;
  category: string;
}

// 🔥 Mercados traduzidos no estilo bet365/betano
export const MARKET_TRANSLATIONS: Record<string, Market> = {
  // Resultado Final (1X2)
  'HOME_WIN': { id: 'HOME_WIN', name: 'Casa Vence', category: 'Resultado Final (1X2)' },
  'DRAW': { id: 'DRAW', name: 'Empate', category: 'Resultado Final (1X2)' },
  'AWAY_WIN': { id: 'AWAY_WIN', name: 'Fora Vence', category: 'Resultado Final (1X2)' },

  // Ambas Marcam
  'BTTS_YES': { id: 'BTTS_YES', name: 'Ambas Marcam - Sim', category: 'Ambas Marcam' },
  'BTTS_NO': { id: 'BTTS_NO', name: 'Ambas Marcam - Não', category: 'Ambas Marcam' },

  // Total de Gols
  'OVER_0_5': { id: 'OVER_0_5', name: 'Mais de 0.5 Gols', category: 'Total de Gols' },
  'UNDER_0_5': { id: 'UNDER_0_5', name: 'Menos de 0.5 Gols', category: 'Total de Gols' },
  'OVER_1_5': { id: 'OVER_1_5', name: 'Mais de 1.5 Gols', category: 'Total de Gols' },
  'UNDER_1_5': { id: 'UNDER_1_5', name: 'Menos de 1.5 Gols', category: 'Total de Gols' },
  'OVER_2_5': { id: 'OVER_2_5', name: 'Mais de 2.5 Gols', category: 'Total de Gols' },
  'UNDER_2_5': { id: 'UNDER_2_5', name: 'Menos de 2.5 Gols', category: 'Total de Gols' },
  'OVER_3_5': { id: 'OVER_3_5', name: 'Mais de 3.5 Gols', category: 'Total de Gols' },
  'UNDER_3_5': { id: 'UNDER_3_5', name: 'Menos de 3.5 Gols', category: 'Total de Gols' },
  'OVER_4_5': { id: 'OVER_4_5', name: 'Mais de 4.5 Gols', category: 'Total de Gols' },
  'UNDER_4_5': { id: 'UNDER_4_5', name: 'Menos de 4.5 Gols', category: 'Total de Gols' },
  'OVER_5_5': { id: 'OVER_5_5', name: 'Mais de 5.5 Gols', category: 'Total de Gols' },
  'UNDER_5_5': { id: 'UNDER_5_5', name: 'Menos de 5.5 Gols', category: 'Total de Gols' },

  // Dupla Chance
  'DOUBLE_CHANCE_1X': { id: 'DOUBLE_CHANCE_1X', name: 'Casa ou Empate (1X)', category: 'Dupla Chance' },
  'DOUBLE_CHANCE_12': { id: 'DOUBLE_CHANCE_12', name: 'Casa ou Fora (12)', category: 'Dupla Chance' },
  'DOUBLE_CHANCE_X2': { id: 'DOUBLE_CHANCE_X2', name: 'Empate ou Fora (X2)', category: 'Dupla Chance' },

  // Total Exato de Gols
  'EXACT_GOALS_0': { id: 'EXACT_GOALS_0', name: 'Exatamente 0 Gols', category: 'Total Exato de Gols' },
  'EXACT_GOALS_1': { id: 'EXACT_GOALS_1', name: 'Exatamente 1 Gol', category: 'Total Exato de Gols' },
  'EXACT_GOALS_2': { id: 'EXACT_GOALS_2', name: 'Exatamente 2 Gols', category: 'Total Exato de Gols' },
  'EXACT_GOALS_3': { id: 'EXACT_GOALS_3', name: 'Exatamente 3 Gols', category: 'Total Exato de Gols' },
  'EXACT_GOALS_4_PLUS': { id: 'EXACT_GOALS_4_PLUS', name: '4 ou Mais Gols', category: 'Total Exato de Gols' },

  // Primeiro a Marcar
  'FIRST_GOAL_HOME': { id: 'FIRST_GOAL_HOME', name: 'Casa Marca Primeiro', category: 'Primeiro a Marcar' },
  'FIRST_GOAL_AWAY': { id: 'FIRST_GOAL_AWAY', name: 'Fora Marca Primeiro', category: 'Primeiro a Marcar' },
  'FIRST_GOAL_NONE': { id: 'FIRST_GOAL_NONE', name: 'Nenhum Time Marca', category: 'Primeiro a Marcar' },

  // Não Toma Gol (Clean Sheet)
  'CLEAN_SHEET_HOME': { id: 'CLEAN_SHEET_HOME', name: 'Casa Não Toma Gol', category: 'Não Toma Gol' },
  'CLEAN_SHEET_AWAY': { id: 'CLEAN_SHEET_AWAY', name: 'Fora Não Toma Gol', category: 'Não Toma Gol' },

  // Par/Ímpar
  'ODD_EVEN_ODD': { id: 'ODD_EVEN_ODD', name: 'Total de Gols Ímpar', category: 'Par/Ímpar' },
  'ODD_EVEN_EVEN': { id: 'ODD_EVEN_EVEN', name: 'Total de Gols Par', category: 'Par/Ímpar' },
};

// Lista de todos os mercados (para uso em listas/dropdowns)
export const ALL_MARKETS: Market[] = Object.values(MARKET_TRANSLATIONS);

// Categorias únicas
export const MARKET_CATEGORIES = Array.from(
  new Set(ALL_MARKETS.map(m => m.category))
);

/**
 * Traduz um ID de mercado para português
 * @param marketId - ID do mercado (ex: "OVER_2_5")
 * @returns Nome traduzido (ex: "Mais de 2.5 Gols")
 */
export function translateMarket(marketId: string): string {
  const market = MARKET_TRANSLATIONS[marketId];
  return market ? market.name : marketId;
}

/**
 * Obtém a categoria de um mercado
 * @param marketId - ID do mercado (ex: "OVER_2_5")
 * @returns Categoria (ex: "Total de Gols")
 */
export function getMarketCategory(marketId: string): string {
  const market = MARKET_TRANSLATIONS[marketId];
  return market ? market.category : 'Outros';
}

/**
 * Obtém todos os mercados de uma categoria específica
 * @param category - Nome da categoria
 * @returns Lista de mercados da categoria
 */
export function getMarketsByCategory(category: string): Market[] {
  return ALL_MARKETS.filter(m => m.category === category);
}

/**
 * Formata o nome do mercado para exibição no bilhete
 * Inclui o nome dos times quando relevante
 *
 * @param marketId - ID do mercado
 * @param homeTeam - Nome do time da casa
 * @param awayTeam - Nome do time de fora
 * @returns Nome formatado para o bilhete
 */
export function formatMarketForTicket(
  marketId: string,
  homeTeam: string,
  awayTeam: string
): string {
  const translated = translateMarket(marketId);

  // Substitui "Casa" e "Fora" pelos nomes dos times quando apropriado
  if (marketId.includes('HOME')) {
    return translated.replace('Casa', homeTeam);
  }
  if (marketId.includes('AWAY')) {
    return translated.replace('Fora', awayTeam);
  }

  return translated;
}
