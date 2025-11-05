"""
🏁 COLLECT FINISHED MATCHES - Coletar jogos finalizados com resultados reais
Busca nas APIs jogos que já terminaram e têm placares definidos
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.getcwd())

from app.services.api_sports_collector import api_sports_collector
from app.services.gradual_population_service import gradual_population_service
from app.core.database import get_db_session
from app.models.match import Match

async def main():
    """Função principal para coletar jogos finalizados"""
    print("🏁 COLETANDO JOGOS FINALIZADOS COM RESULTADOS REAIS")
    print("🎯 Buscando nas principais ligas: Brasileirão, La Liga, Premier League, Serie A")
    print("=" * 70)

    try:
        # 1. Verificar estado atual do banco
        with get_db_session() as session:
            total_matches = session.query(Match).count()
            with_scores = session.query(Match).filter(
                Match.home_score.isnot(None),
                Match.away_score.isnot(None)
            ).count()

            print(f"📊 ESTADO ATUAL:")
            print(f"  ⚽ Total de jogos: {total_matches}")
            print(f"  🎯 Com placares: {with_scores}")
            print(f"  ❌ Sem placares: {total_matches - with_scores}")
            print()

        # 2. Coletar jogos finalizados das APIs
        print("🔄 INICIANDO COLETA DE JOGOS FINALIZADOS...")
        finished_matches = await api_sports_collector.get_finished_matches_with_results()

        if not finished_matches:
            print("❌ NENHUM JOGO FINALIZADO COLETADO")
            print("💡 Possíveis causas:")
            print("  • Rate limit da API atingido")
            print("  • Problemas de conectividade")
            print("  • API key inválida")
            return

        print(f"\n✅ COLETADOS {len(finished_matches)} JOGOS FINALIZADOS")

        # 3. Inserir no banco de dados
        print("\n📦 INSERINDO JOGOS NO BANCO...")
        inserted_count = 0
        updated_count = 0

        with get_db_session() as session:
            for match_data in finished_matches:
                try:
                    # Verificar se o jogo já existe
                    external_id = f"api_sports_{match_data['match_id']}"
                    existing_match = session.query(Match).filter(
                        Match.external_id == external_id
                    ).first()

                    if existing_match:
                        # Atualizar com resultado se não tinha
                        if (existing_match.home_score is None and
                            'home_score' in match_data):
                            existing_match.home_score = match_data['home_score']
                            existing_match.away_score = match_data['away_score']
                            existing_match.status = 'FINISHED'
                            updated_count += 1

                            print(f"  🔄 Atualizado: {match_data['home_team']['name']} {match_data['home_score']}-{match_data['away_score']} {match_data['away_team']['name']}")
                    else:
                        # Inserir novo jogo
                        result = await gradual_population_service._insert_match_safely(session, match_data)
                        if result:
                            inserted_count += 1
                            print(f"  ✅ Inserido: {match_data['home_team']['name']} {match_data['home_score']}-{match_data['away_score']} {match_data['away_team']['name']}")

                except Exception as e:
                    print(f"  ❌ Erro inserindo {match_data.get('home_team', {}).get('name', 'Unknown')}: {e}")
                    continue

            session.commit()

        # 4. Verificar resultado final
        with get_db_session() as session:
            final_total = session.query(Match).count()
            final_with_scores = session.query(Match).filter(
                Match.home_score.isnot(None),
                Match.away_score.isnot(None)
            ).count()

            print(f"\n📊 RESULTADO FINAL:")
            print(f"  ✅ Jogos inseridos: {inserted_count}")
            print(f"  🔄 Jogos atualizados: {updated_count}")
            print(f"  ⚽ Total final de jogos: {final_total}")
            print(f"  🎯 Com placares reais: {final_with_scores}")

            if final_with_scores >= 10:
                print(f"\n🎉 SUCESSO! Agora temos {final_with_scores} jogos com resultados reais")
                print("🤖 Próximo passo: Executar 'python3 train_ml_models.py'")
            else:
                print(f"\n⚠️ AINDA INSUFICIENTE: Precisamos de pelo menos 10 jogos para ML")
                print("🔄 Execute este script novamente ou ajuste as datas na API")

    except Exception as e:
        print(f"❌ Erro no script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())