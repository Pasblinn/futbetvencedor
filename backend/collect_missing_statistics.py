#!/usr/bin/env python3
"""
📊 COLETAR ESTATÍSTICAS FALTANTES
Coleta estatísticas dos fixtures que ainda não têm
Respeita quota e prioriza ligas importantes
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.services.api_football_service import APIFootballService
from app.services.api_quota_manager import APIQuotaManager
from app.models.api_tracking import FixtureCache

async def main():
    print("📊 COLETA DE ESTATÍSTICAS FALTANTES")
    print("="*60)

    db = SessionLocal()
    api_service = APIFootballService()
    quota_manager = APIQuotaManager(db)

    # Verificar quota disponível
    health = quota_manager.check_health()
    print(f"\n💊 Quota disponível: {health['available_requests']} requests")
    print(f"   Status: {health['status']}")

    if health['available_requests'] < 100:
        print("\n❌ Quota insuficiente (mínimo 100 requests)")
        db.close()
        return

    # Buscar fixtures sem estatísticas (priorizando ligas brasileiras)
    fixtures_to_collect = db.query(FixtureCache).filter(
        FixtureCache.status == 'FT',
        FixtureCache.has_statistics == False
    ).order_by(
        # Priorizar: 71=Brasileirão A, 72=Série B, 13=Libertadores, 11=Sul-Americana
        FixtureCache.league_id.in_([71, 72, 13, 11]).desc(),
        FixtureCache.fixture_date.desc()
    ).all()

    print(f"\n🎯 Fixtures sem estatísticas: {len(fixtures_to_collect)}")

    # Calcular quantos podemos coletar
    available_requests = health['available_requests']
    safe_limit = int(available_requests * 0.8)  # Usar apenas 80% para segurança
    max_to_collect = min(safe_limit, len(fixtures_to_collect))

    print(f"   Podemos coletar: {max_to_collect} (limite seguro: {safe_limit})")

    if max_to_collect == 0:
        print("\n⚠️ Nenhuma estatística pode ser coletada agora")
        db.close()
        return

    # Confirmação
    print(f"\n⚠️  Isso vai usar ~{max_to_collect} requests")
    response = input("Continuar? (s/N): ")

    if response.lower() != 's':
        print("❌ Cancelado pelo usuário")
        db.close()
        return

    # Coletar estatísticas
    print(f"\n🚀 Iniciando coleta de {max_to_collect} fixtures...")
    print("="*60)

    collected = 0
    errors = 0
    delay = quota_manager.get_recommended_delay()

    for idx, cache in enumerate(fixtures_to_collect[:max_to_collect], 1):
        try:
            # Verificar quota antes de cada request
            if not quota_manager.can_make_request(1):
                print(f"\n⚠️ Quota esgotada em {idx-1}/{max_to_collect}")
                break

            # Coletar estatísticas
            stats = await api_service.get_fixture_statistics(cache.fixture_id)

            # Registrar request
            quota_manager.record_request(
                endpoint='fixture_statistics',
                success=True,
                results_count=len(stats) if stats else 0,
                params={'fixture': cache.fixture_id}
            )

            # Salvar no cache
            if stats and len(stats) > 0:
                cache.raw_statistics_data = stats
                cache.has_statistics = True
                cache.needs_update = True
                db.commit()
                collected += 1

                # Log a cada 50
                if idx % 50 == 0:
                    remaining = quota_manager.get_available_requests()
                    print(f"   [{idx}/{max_to_collect}] ✅ {collected} coletados | Quota: {remaining} restantes")

            # Delay adaptativo
            await asyncio.sleep(delay)

        except Exception as e:
            errors += 1
            print(f"   ❌ Erro fixture {cache.fixture_id}: {e}")

            if errors > 10:
                print(f"\n⚠️ Muitos erros ({errors}). Parando...")
                break

    # Resumo final
    print(f"\n{'='*60}")
    print("🎉 COLETA DE ESTATÍSTICAS CONCLUÍDA!")
    print(f"{'='*60}")
    print(f"📊 Coletados: {collected}/{max_to_collect}")
    print(f"❌ Erros: {errors}")

    final_health = quota_manager.check_health()
    print(f"\n💊 Quota final:")
    print(f"   Usados: {final_health['available_requests']}")
    print(f"   Status: {final_health['status']}")

    # Estatísticas atualizadas
    total_with_stats = db.query(FixtureCache).filter(
        FixtureCache.status == 'FT',
        FixtureCache.has_statistics == True
    ).count()

    total_ft = db.query(FixtureCache).filter(FixtureCache.status == 'FT').count()

    coverage = (total_with_stats / total_ft * 100) if total_ft > 0 else 0

    print(f"\n📈 Cobertura atualizada:")
    print(f"   Com stats: {total_with_stats}/{total_ft} ({coverage:.1f}%)")

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
