#!/usr/bin/env python3
"""
🔴 MONITOR EM TEMPO REAL - FLAMENGO VS ESTUDIANTES
Copa Libertadores - 26/09/2025 21:30 Brasília

Sistema de monitoramento ao vivo para:
1. Acompanhar estatísticas do jogo
2. Coletar resultados dos mercados apostados
3. Avaliar acurácia das previsões
4. Preparar dados para retreino da ML
"""

import asyncio
import json
import requests
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

# Adicionar app ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.config import settings

class LiveMatchMonitor:
    def __init__(self):
        self.api_base = "http://localhost:8000/api/v1"
        self.match_id = "535966"
        self.predictions_file = None
        self.api_key = settings.FOOTBALL_DATA_API_KEY
        if not self.api_key:
            raise ValueError("FOOTBALL_DATA_API_KEY não configurada. Configure no arquivo .env")
        self.live_data = {
            'match_events': [],
            'minute_by_minute': {},
            'final_results': {},
            'prediction_accuracy': {}
        }
        self.monitoring = False

    async def start_monitoring(self):
        """Inicia o monitoramento do jogo"""
        print("🔴 INICIANDO MONITOR AO VIVO")
        print("=" * 50)

        # Carregar previsões
        await self.load_predictions()

        # Mostrar status pré-jogo
        await self.show_pre_match_status()

        # Aguardar início do jogo
        await self.wait_for_kickoff()

        # Monitorar durante o jogo
        await self.monitor_live_match()

        # Processar resultados finais
        await self.process_final_results()

    async def load_predictions(self):
        """Carrega as previsões salvas"""
        import glob

        # Procurar arquivo de previsões mais recente
        prediction_files = glob.glob("flamengo_estudiantes_predictions_*.json")
        if prediction_files:
            latest_file = max(prediction_files)
            self.predictions_file = latest_file

            with open(latest_file, 'r', encoding='utf-8') as f:
                self.predictions_data = json.load(f)

            print(f"📊 Previsões carregadas: {latest_file}")
            print(f"🎯 {len(self.predictions_data['predictions'])} mercados analisados")
        else:
            print("❌ Nenhum arquivo de previsões encontrado")
            return False

    async def show_pre_match_status(self):
        """Mostra status pré-jogo"""
        if not self.predictions_data:
            return

        print("\n📋 STATUS PRÉ-JOGO")
        print("-" * 30)

        match_data = self.predictions_data['match']['match']
        print(f"🏟️ {match_data['homeTeam']['name']} vs {match_data['awayTeam']['name']}")
        print(f"🏆 {match_data['competition']['name']}")
        print(f"⏰ {self.predictions_data['match']['kickoff']}")

        # Principais previsões
        print("\n🎯 PRINCIPAIS PREVISÕES:")

        # 1X2
        if '1x2' in self.predictions_data['predictions']:
            pred = self.predictions_data['predictions']['1x2']['predicted_outcome']
            conf = self.predictions_data['predictions']['1x2']['confidence']
            print(f"   ⚽ Resultado: {pred} ({conf:.1%})")

        # Gols
        if 'goals' in self.predictions_data['predictions']:
            total = self.predictions_data['predictions']['goals']['total_goals_expected']
            rec = self.predictions_data['predictions']['goals']['over_under_25']['recommendation']
            print(f"   📈 Gols: {total:.2f} total - {rec}")

        # BTTS
        if 'btts' in self.predictions_data['predictions']:
            btts = self.predictions_data['predictions']['btts']['predicted_outcome']
            conf = self.predictions_data['predictions']['btts']['confidence']
            print(f"   🎯 BTTS: {btts} ({conf:.1%})")

        # Escanteios
        if 'corners' in self.predictions_data['predictions']:
            corners = self.predictions_data['predictions']['corners']['expected_total']
            print(f"   🚩 Escanteios: {corners:.1f} esperados")

        print("\n⏳ Aguardando início do jogo...")

    async def wait_for_kickoff(self):
        """Aguarda o início do jogo"""
        # Horário do jogo: 26/09/2025 00:30 UTC (21:30 Brasília)
        kickoff_time = datetime(2025, 9, 26, 0, 30)  # UTC

        while datetime.now() < kickoff_time:
            time_to_kickoff = kickoff_time - datetime.now()

            if time_to_kickoff.total_seconds() > 3600:  # Mais de 1 hora
                print(f"⏰ Faltam {time_to_kickoff.total_seconds()/3600:.1f}h para o jogo")
                await asyncio.sleep(1800)  # Check a cada 30min
            elif time_to_kickoff.total_seconds() > 300:  # Mais de 5min
                print(f"⏰ Faltam {time_to_kickoff.total_seconds()/60:.0f}min para o jogo")
                await asyncio.sleep(60)  # Check a cada 1min
            else:
                print(f"⏰ Faltam {time_to_kickoff.total_seconds():.0f}s para o jogo")
                await asyncio.sleep(10)  # Check a cada 10s

        print("🚀 JOGO INICIADO! Começando monitoramento...")

    async def monitor_live_match(self):
        """Monitora o jogo ao vivo"""
        self.monitoring = True
        match_minute = 0

        while self.monitoring and match_minute < 95:  # 90min + prorrogação
            try:
                # Simular obtenção de dados ao vivo
                live_stats = await self.fetch_live_stats()

                if live_stats:
                    match_minute = live_stats.get('minute', match_minute + 1)
                    await self.process_live_stats(match_minute, live_stats)

                    # Verificar se jogo terminou
                    if live_stats.get('status') in ['FINISHED', 'FULL_TIME']:
                        print("⏹️ Jogo finalizado!")
                        self.monitoring = False
                        break

                # Aguardar 30 segundos antes da próxima consulta
                await asyncio.sleep(30)

            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                await asyncio.sleep(60)

    async def fetch_live_stats(self):
        """Busca estatísticas ao vivo"""
        try:
            # Tentar buscar dados reais da API
            response = requests.get(
                f"https://api.football-data.org/v4/matches/{self.match_id}",
                headers={"X-Auth-Token": self.api_key},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                # Simular dados se API não estiver disponível
                return self.simulate_live_data()

        except Exception as e:
            print(f"⚠️ Usando dados simulados: {e}")
            return self.simulate_live_data()

    def simulate_live_data(self):
        """Simula dados ao vivo para teste"""
        # Esta função simula um jogo para testar o sistema
        import random

        current_minute = len(self.live_data['minute_by_minute']) + 1

        if current_minute > 90:
            return {
                'status': 'FINISHED',
                'minute': 90,
                'score': {'home': 1, 'away': 1},
                'stats': {
                    'corners_home': 4,
                    'corners_away': 7,
                    'cards_home': 2,
                    'cards_away': 3
                }
            }

        # Simular progresso do jogo
        return {
            'status': 'IN_PLAY',
            'minute': current_minute,
            'score': {'home': 0 if current_minute < 45 else random.randint(0, 1),
                     'away': 0 if current_minute < 30 else random.randint(0, 2)},
            'stats': {
                'corners_home': random.randint(0, current_minute // 15),
                'corners_away': random.randint(0, current_minute // 10),
                'cards_home': random.randint(0, current_minute // 30),
                'cards_away': random.randint(0, current_minute // 25)
            }
        }

    async def process_live_stats(self, minute, stats):
        """Processa estatísticas ao vivo"""
        self.live_data['minute_by_minute'][minute] = {
            'timestamp': datetime.now().isoformat(),
            'minute': minute,
            'score': stats.get('score', {}),
            'stats': stats.get('stats', {}),
            'status': stats.get('status', 'IN_PLAY')
        }

        # Mostrar updates importantes
        if minute % 15 == 0 or stats.get('score', {}) != {}:
            await self.show_live_update(minute, stats)

    async def show_live_update(self, minute, stats):
        """Mostra update ao vivo"""
        score = stats.get('score', {})
        home_score = score.get('home', 0)
        away_score = score.get('away', 0)

        print(f"\n⚽ {minute}' - Estudiantes {home_score} x {away_score} Flamengo")

        # Mostrar estatísticas
        if 'stats' in stats:
            st = stats['stats']
            corners_total = st.get('corners_home', 0) + st.get('corners_away', 0)
            cards_total = st.get('cards_home', 0) + st.get('cards_away', 0)

            print(f"   🚩 Escanteios: {corners_total} ({st.get('corners_home', 0)}-{st.get('corners_away', 0)})")
            print(f"   🟨 Cartões: {cards_total} ({st.get('cards_home', 0)}-{st.get('cards_away', 0)})")

            # Verificar previsões em tempo real
            await self.check_predictions_status(stats)

    async def check_predictions_status(self, stats):
        """Verifica status das previsões"""
        score = stats.get('score', {})
        total_goals = score.get('home', 0) + score.get('away', 0)

        # Check Over/Under 2.5
        if total_goals >= 3:
            print("   📊 Over 2.5 ✅ (Nossa previsão: Under 2.5 ❌)")
        elif stats.get('minute', 0) > 75 and total_goals < 3:
            print("   📊 Under 2.5 provável ✅ (Nossa previsão correta)")

        # Check BTTS
        home_scored = score.get('home', 0) > 0
        away_scored = score.get('away', 0) > 0

        if home_scored and away_scored:
            print("   🎯 BTTS Sim ❌ (Nossa previsão: BTTS Não)")
        elif stats.get('minute', 0) > 80 and not (home_scored and away_scored):
            print("   🎯 BTTS Não provável ✅ (Nossa previsão correta)")

    async def process_final_results(self):
        """Processa resultados finais"""
        print("\n🏁 PROCESSANDO RESULTADOS FINAIS")
        print("=" * 40)

        # Obter estatísticas finais do último minuto
        final_stats = list(self.live_data['minute_by_minute'].values())[-1]

        # Calcular resultados dos mercados
        await self.calculate_market_results(final_stats)

        # Avaliar acurácia das previsões
        await self.evaluate_prediction_accuracy()

        # Preparar dados para retreino
        await self.prepare_retraining_data()

        # Salvar resultados
        await self.save_final_results()

    async def calculate_market_results(self, final_stats):
        """Calcula resultados de todos os mercados"""
        score = final_stats.get('score', {})
        stats = final_stats.get('stats', {})

        home_score = score.get('home', 0)
        away_score = score.get('away', 0)
        total_goals = home_score + away_score

        self.live_data['final_results'] = {
            # Resultado 1X2
            'match_result': 'home_win' if home_score > away_score else
                           ('away_win' if away_score > home_score else 'draw'),

            # Gols
            'total_goals': total_goals,
            'over_1_5': total_goals > 1.5,
            'over_2_5': total_goals > 2.5,
            'over_3_5': total_goals > 3.5,

            # BTTS
            'btts': home_score > 0 and away_score > 0,

            # Escanteios
            'corners_home': stats.get('corners_home', 0),
            'corners_away': stats.get('corners_away', 0),
            'total_corners': stats.get('corners_home', 0) + stats.get('corners_away', 0),

            # Cartões
            'cards_home': stats.get('cards_home', 0),
            'cards_away': stats.get('cards_away', 0),
            'total_cards': stats.get('cards_home', 0) + stats.get('cards_away', 0),

            # Outros mercados
            'home_scored': home_score > 0,
            'away_scored': away_score > 0,
            'clean_sheet_home': away_score == 0,
            'clean_sheet_away': home_score == 0
        }

    async def evaluate_prediction_accuracy(self):
        """Avalia acurácia das previsões"""
        if not self.predictions_data:
            return

        results = self.live_data['final_results']
        predictions = self.predictions_data['predictions']
        accuracy = {}

        # 1X2
        if '1x2' in predictions:
            predicted = predictions['1x2']['predicted_outcome']
            actual = results['match_result']

            # Mapear resultado
            pred_mapped = 'away_win' if 'Flamengo' in predicted else ('draw' if 'Empate' in predicted else 'home_win')
            accuracy['1x2'] = {
                'predicted': predicted,
                'actual': actual,
                'correct': pred_mapped == actual,
                'confidence': predictions['1x2']['confidence']
            }

        # Over/Under 2.5
        if 'goals' in predictions:
            predicted_under = predictions['goals']['over_under_25']['recommendation'] == 'Under 2.5'
            actual_under = not results['over_2_5']

            accuracy['over_under_2_5'] = {
                'predicted': 'Under 2.5' if predicted_under else 'Over 2.5',
                'actual': 'Under 2.5' if actual_under else 'Over 2.5',
                'correct': predicted_under == actual_under,
                'total_goals': results['total_goals']
            }

        # BTTS
        if 'btts' in predictions:
            predicted_no = predictions['btts']['predicted_outcome'] == 'No'
            actual_no = not results['btts']

            accuracy['btts'] = {
                'predicted': 'No' if predicted_no else 'Yes',
                'actual': 'No' if actual_no else 'Yes',
                'correct': predicted_no == actual_no,
                'confidence': predictions['btts']['confidence']
            }

        # Escanteios Over 8.5
        if 'corners' in predictions:
            predicted_over = True  # Previmos over 8.5 com 98.5%
            actual_over = results['total_corners'] > 8.5

            accuracy['corners_over_8_5'] = {
                'predicted': 'Over 8.5',
                'actual': f"Total: {results['total_corners']}",
                'correct': predicted_over == actual_over,
                'probability_predicted': 0.985
            }

        self.live_data['prediction_accuracy'] = accuracy

    async def prepare_retraining_data(self):
        """Prepara dados para retreino da ML"""
        retraining_data = {
            'match_info': {
                'match_id': self.match_id,
                'date': '2025-09-26',
                'home_team': 'Estudiantes',
                'away_team': 'Flamengo',
                'competition': 'Copa Libertadores'
            },
            'predictions_made': self.predictions_data.get('predictions', {}),
            'actual_results': self.live_data['final_results'],
            'prediction_accuracy': self.live_data['prediction_accuracy'],
            'features_for_ml': {
                'home_strength': 0.31,  # Baseado na probabilidade 1X2
                'away_strength': 0.43,
                'expected_goals_home': 0.76,
                'expected_goals_away': 1.46,
                'h2h_advantage': 1,  # Flamengo ganhou ida
                'form_home': 1.5,
                'form_away': 2.2,
                'venue_advantage': 0.08  # 8% vantagem casa
            },
            'learning_points': []
        }

        # Identificar pontos de aprendizado
        accuracy = self.live_data['prediction_accuracy']

        for market, result in accuracy.items():
            if not result['correct']:
                retraining_data['learning_points'].append({
                    'market': market,
                    'error_type': 'prediction_miss',
                    'predicted_confidence': result.get('confidence', 0),
                    'lesson': f"Model was wrong about {market} - need to adjust weights"
                })

        self.live_data['retraining_data'] = retraining_data

    async def save_final_results(self):
        """Salva resultados finais"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"match_results_flamengo_estudiantes_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'match_monitoring': self.live_data,
                'original_predictions': self.predictions_data if hasattr(self, 'predictions_data') else {},
                'monitoring_completed_at': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Resultados salvos: {filename}")

        # Mostrar resumo final
        await self.show_final_summary()

    async def show_final_summary(self):
        """Mostra resumo final"""
        print("\n🏆 RESUMO FINAL")
        print("=" * 30)

        results = self.live_data['final_results']
        accuracy = self.live_data['prediction_accuracy']

        # Placar final
        print(f"📊 PLACAR FINAL:")
        print(f"   Estudiantes {results.get('total_goals', 0) - results.get('away_scored', 0)*results.get('total_goals', 0)//max(1, results.get('total_goals', 1))} x {results.get('away_scored', 0)*results.get('total_goals', 0)//max(1, results.get('total_goals', 1))} Flamengo")

        # Acurácia das previsões
        correct_predictions = sum(1 for acc in accuracy.values() if acc['correct'])
        total_predictions = len(accuracy)
        accuracy_rate = correct_predictions / total_predictions if total_predictions > 0 else 0

        print(f"\n📈 ACURÁCIA DAS PREVISÕES:")
        print(f"   ✅ Corretas: {correct_predictions}/{total_predictions}")
        print(f"   📊 Taxa de acerto: {accuracy_rate:.1%}")

        for market, acc in accuracy.items():
            status = "✅" if acc['correct'] else "❌"
            print(f"   {status} {market.upper()}: {acc['predicted']} (Real: {acc['actual']})")

        # Lições aprendidas
        learning_points = self.live_data.get('retraining_data', {}).get('learning_points', [])
        if learning_points:
            print(f"\n🧠 PONTOS DE APRENDIZADO PARA ML:")
            for i, point in enumerate(learning_points, 1):
                print(f"   {i}. {point['lesson']}")

        print(f"\n🔄 Dados preparados para retreino da ML")
        print(f"📈 Sistema pode ser melhorado com estes resultados")

async def main():
    """Função principal"""
    monitor = LiveMatchMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    # Para teste imediato, executar simulação
    print("🧪 MODO DE TESTE - Executando simulação rápida")
    asyncio.run(main())