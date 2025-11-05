#!/usr/bin/env python3
"""
🎯 SINCRONIZAÇÃO MANUAL DE ODDS - BUSCAR ODDS REAIS AGORA!
Executa a sincronização de odds da API-Football para os jogos de hoje
"""
import asyncio
from app.services.data_synchronizer import DataSynchronizer

async def main():
    print("=" * 80)
    print("💰 SINCRONIZANDO ODDS REAIS DA API-FOOTBALL")
    print("=" * 80)

    synchronizer = DataSynchronizer()

    # Executar sincronização de odds
    result = await synchronizer._sync_odds()

    print(f"\n✅ Sincronização concluída!")
    print(f"   📊 {result} odds processadas")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
