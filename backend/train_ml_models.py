"""
🤖 TRAIN ML MODELS - Script para treinar modelos ML com dados reais
Usa os jogos finalizados coletados das APIs
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.getcwd())

from app.services.ml_trainer_real_data import ml_trainer_real_data
from app.core.database import get_db_session
from app.models.match import Match

async def show_available_data():
    """Mostrar dados disponíveis para treinamento"""
    print("📊 DADOS DISPONÍVEIS PARA TREINAMENTO ML:")
    print("=" * 60)

    with get_db_session() as session:
        # Jogos finalizados
        finished_matches = session.query(Match).filter(
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).count()

        total_matches = session.query(Match).count()

        print(f"⚽ Total de jogos no banco: {total_matches}")
        print(f"🏁 Jogos finalizados (para ML): {finished_matches}")
        print(f"📅 Jogos sem resultados: {total_matches - finished_matches}")

        if finished_matches > 0:
            # Distribuição por liga
            print(f"\n🏆 Jogos finalizados por liga:")
            finished_by_league = session.query(Match.league, session.query(Match.id).filter(
                Match.league == Match.league,
                Match.home_score.isnot(None)
            ).count().label('count')).filter(
                Match.home_score.isnot(None)
            ).distinct().all()

            leagues = session.query(Match.league).filter(
                Match.home_score.isnot(None)
            ).distinct().all()

            for league in leagues:
                if league[0]:
                    count = session.query(Match).filter(
                        Match.league == league[0],
                        Match.home_score.isnot(None)
                    ).count()
                    print(f"  • {league[0]}: {count} jogos")

    print("=" * 60)

async def main():
    """Função principal"""
    print("🤖 TREINAMENTO DE MODELOS ML COM DADOS REAIS")
    print("🎯 Usando jogos finalizados das APIs")
    print("🔬 Múltiplos algoritmos: RF, GB, LR")
    print("=" * 70)

    try:
        # 1. Mostrar dados disponíveis
        await show_available_data()
        print()

        # 2. Verificar se temos dados suficientes
        with get_db_session() as session:
            finished_count = session.query(Match).filter(
                Match.home_score.isnot(None),
                Match.away_score.isnot(None)
            ).count()

            if finished_count < 10:
                print("❌ DADOS INSUFICIENTES PARA TREINAMENTO")
                print(f"🎯 Necessário: 10+ jogos | Disponível: {finished_count}")
                print("💡 Execute 'python3 collect_finished_matches.py' primeiro")
                return

            print(f"✅ DADOS SUFICIENTES: {finished_count} jogos finalizados")

        # 3. Iniciar treinamento
        print("\n🚀 INICIANDO TREINAMENTO ML...")
        print("⏳ Isso pode levar alguns minutos...")
        print()

        result = await ml_trainer_real_data.train_models_with_real_data()

        # 4. Mostrar resultados do treinamento
        print("📊 RESULTADOS DO TREINAMENTO:")
        print(f"✅ Sucesso: {result['success']}")

        if result['success']:
            print(f"\n📊 Estatísticas dos dados:")
            stats = result['data_stats']
            print(f"  📈 Total de jogos: {stats['total_matches']}")
            print(f"  ⚽ Média gols/jogo: {stats['avg_goals_per_match']:.2f}")
            print(f"  👥 Times únicos: {stats['unique_teams']}")

            print(f"\n🏆 Distribuição de resultados:")
            for result_type, count in stats['results_distribution'].items():
                print(f"  • {result_type}: {count}")

            print(f"\n🏆 Jogos por liga:")
            for league, count in stats['leagues'].items():
                print(f"  • {league}: {count}")

            print(f"\n🤖 Performance dos modelos:")
            for model_name, performance in result['models_trained'].items():
                print(f"  • {model_name}:")
                print(f"    📈 Treino: {performance['train_accuracy']:.3f}")
                print(f"    🎯 Teste: {performance['test_accuracy']:.3f}")

            if 'performance' in result and result['performance']:
                ensemble = result['performance']
                print(f"\n🎯 ENSEMBLE PERFORMANCE:")
                print(f"  🏆 Accuracy: {ensemble['ensemble_accuracy']:.3f}")
                print(f"  🥇 Melhor modelo: {ensemble['best_model']}")

        else:
            print(f"❌ Erro no treinamento: {result.get('error', 'Erro desconhecido')}")

        # 5. Testar predições
        if result['success']:
            print("\n🔮 TESTANDO PREDIÇÕES:")

            test_matches = [
                ("Real Madrid", "Barcelona", "La Liga"),
                ("Liverpool", "Manchester City", "Premier League"),
                ("Flamengo", "Palmeiras", "Brasileirão")
            ]

            for home, away, league in test_matches:
                try:
                    prediction = await ml_trainer_real_data.predict_match_outcome(home, away, league)

                    if 'error' not in prediction:
                        pred = prediction['ensemble_prediction']
                        confidence = prediction['confidence']
                        print(f"  🔮 {home} vs {away}: {pred} (confiança: {confidence:.2f})")
                    else:
                        print(f"  ⚠️ {home} vs {away}: Erro na predição")

                except Exception as e:
                    print(f"  ❌ {home} vs {away}: {e}")

        # 6. Informações finais
        print("\n" + "=" * 70)
        print("🎉 TREINAMENTO ML CONCLUÍDO!")

        if result['success']:
            print("📁 Modelos salvos em: models/real_data/")
            print("🔮 Sistema pronto para fazer predições")
            print("🚀 Próximo: Integrar com endpoints da API")
        else:
            print("❌ Verifique os logs para mais detalhes do erro")

    except Exception as e:
        print(f"❌ Erro no script de treinamento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())