"""
🏗️ CREATE TRAINING DATASET - Criar dataset para treinar ML
Converte matriz de confrontos da Wikipedia em dataset de jogos individuais
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import re

def extract_matches_from_confrontos():
    """
    Extrair jogos individuais da matriz de confrontos
    """
    print("🏗️ CRIANDO DATASET DE TREINAMENTO ML")
    print("=" * 50)

    # Carregar dados da matriz de confrontos
    confrontos_file = None
    for file in os.listdir('scraped_tables/'):
        if 'Confrontos' in file and file.endswith('.csv'):
            confrontos_file = file
            break

    if not confrontos_file:
        print("❌ Arquivo de confrontos não encontrado!")
        return None

    print(f"📁 Carregando: {confrontos_file}")
    confrontos = pd.read_csv(f'scraped_tables/{confrontos_file}')

    # Extrair jogos
    matches = []
    teams = list(confrontos.columns[1:])  # Pular primeira coluna

    print(f"🏟️ Times encontrados: {len(teams)}")
    print(f"🎯 Processando matriz {confrontos.shape[0]}x{confrontos.shape[1]}")

    for i, home_team_full in enumerate(confrontos.iloc[:, 0]):  # Times mandantes
        # Limpar nome do time (remover códigos especiais)
        home_team = clean_team_name(home_team_full)

        for j, away_team in enumerate(teams):  # Times visitantes
            if i < len(confrontos):  # Verificar se linha existe
                result = confrontos.iloc[i, j + 1]  # +1 para pular primeira coluna

                # Verificar se há resultado válido
                if pd.notna(result) and result != '—' and '–' in str(result):
                    try:
                        # Extrair placar (formato: "2–1", "1–0", etc.)
                        score_match = re.match(r'(\d+)–(\d+)', str(result))
                        if score_match:
                            home_score = int(score_match.group(1))
                            away_score = int(score_match.group(2))

                            # Determinar resultado
                            if home_score > away_score:
                                match_result = 'home_win'
                            elif away_score > home_score:
                                match_result = 'away_win'
                            else:
                                match_result = 'draw'

                            # Criar registro do jogo
                            match = {
                                'home_team': clean_team_name(home_team),
                                'away_team': clean_team_name(away_team),
                                'home_score': home_score,
                                'away_score': away_score,
                                'total_goals': home_score + away_score,
                                'result': match_result,
                                'goal_difference': home_score - away_score,
                                'league': 'Brasileirão 2024',
                                'season': '2024',
                                'source': 'wikipedia_confrontos'
                            }

                            matches.append(match)

                    except Exception as e:
                        print(f"⚠️ Erro processando {home_team} vs {away_team}: {e}")
                        continue

    print(f"⚽ Jogos extraídos: {len(matches)}")
    return matches

def clean_team_name(name):
    """
    Limpar nome do time removendo códigos e caracteres especiais
    """
    if pd.isna(name):
        return "Unknown"

    # Remover códigos entre parênteses e caracteres especiais
    cleaned = re.sub(r'\([^)]*\)', '', str(name))  # Remove (C), (R), etc.
    cleaned = cleaned.strip()
    cleaned = re.sub(r'[^\w\s]', '', cleaned)  # Remove caracteres especiais

    # Mapear nomes conhecidos
    team_mapping = {
        'Athletico Paranaense': 'Athletico-PR',
        'Atlético Goianiense': 'Atlético-GO',
        'Atlético Mineiro': 'Atlético-MG',
        'Vasco da Gama': 'Vasco',
        'Red Bull Bragantino': 'RB Bragantino'
    }

    return team_mapping.get(cleaned, cleaned)

def add_team_features(matches_df):
    """
    Adicionar features dos times baseadas na classificação
    """
    print("📊 Adicionando features dos times...")

    # Carregar classificação
    classificacao_file = None
    for file in os.listdir('scraped_tables/'):
        if 'Classificação' in file and file.endswith('.csv'):
            classificacao_file = file
            break

    if not classificacao_file:
        print("⚠️ Classificação não encontrada, usando features básicas")
        return matches_df

    classificacao = pd.read_csv(f'scraped_tables/{classificacao_file}')

    # Criar dicionário de estatísticas dos times
    team_stats = {}
    for _, row in classificacao.iterrows():
        team_name = clean_team_name(row['Equipevde'])
        team_stats[team_name] = {
            'position': row['Pos'],
            'points': row['Pts'],
            'played': row['J'],
            'wins': row['V'],
            'draws': row['E'],
            'losses': row['D'],
            'goals_for': row['GP'],
            'goals_against': row['GC'],
            'goal_difference': row['SG']
        }

    # Adicionar features ao dataset
    enhanced_matches = []
    for match in matches_df.to_dict('records'):
        home_team = match['home_team']
        away_team = match['away_team']

        # Stats do time da casa
        home_stats = team_stats.get(home_team, {})
        away_stats = team_stats.get(away_team, {})

        match.update({
            'home_position': home_stats.get('position', 10),
            'away_position': away_stats.get('position', 10),
            'home_points': home_stats.get('points', 50),
            'away_points': away_stats.get('points', 50),
            'home_wins': home_stats.get('wins', 15),
            'away_wins': away_stats.get('wins', 15),
            'home_goals_for': home_stats.get('goals_for', 45),
            'away_goals_for': away_stats.get('goals_for', 45),
            'home_goals_against': home_stats.get('goals_against', 45),
            'away_goals_against': away_stats.get('goals_against', 45),
            'position_difference': home_stats.get('position', 10) - away_stats.get('position', 10),
            'points_difference': home_stats.get('points', 50) - away_stats.get('points', 50)
        })

        enhanced_matches.append(match)

    return pd.DataFrame(enhanced_matches)

def main():
    """Função principal"""
    # Extrair jogos da matriz
    matches = extract_matches_from_confrontos()

    if not matches:
        print("❌ Nenhum jogo extraído!")
        return

    # Converter para DataFrame
    matches_df = pd.DataFrame(matches)

    # Adicionar features dos times
    enhanced_df = add_team_features(matches_df)

    # Salvar dataset
    output_file = "brasileirao_2024_training_dataset.csv"
    enhanced_df.to_csv(output_file, index=False)

    print(f"\n📊 DATASET CRIADO:")
    print(f"📁 Arquivo: {output_file}")
    print(f"⚽ Total de jogos: {len(enhanced_df)}")
    print(f"📋 Colunas: {len(enhanced_df.columns)}")

    # Estatísticas do dataset
    print(f"\n📈 ESTATÍSTICAS:")
    print(f"  🏠 Vitórias em casa: {len(enhanced_df[enhanced_df['result'] == 'home_win'])}")
    print(f"  ✈️ Vitórias visitante: {len(enhanced_df[enhanced_df['result'] == 'away_win'])}")
    print(f"  🤝 Empates: {len(enhanced_df[enhanced_df['result'] == 'draw'])}")
    print(f"  ⚽ Média de gols: {enhanced_df['total_goals'].mean():.2f}")
    print(f"  🏟️ Times únicos: {enhanced_df['home_team'].nunique()}")

    # Mostrar sample
    print(f"\n📄 SAMPLE DOS DADOS:")
    print(enhanced_df[['home_team', 'away_team', 'home_score', 'away_score', 'result']].head(10).to_string())

    print(f"\n🎉 DATASET PRONTO PARA ML!")
    print(f"🚀 Próximo: python3 train_ml_models.py")

if __name__ == "__main__":
    main()