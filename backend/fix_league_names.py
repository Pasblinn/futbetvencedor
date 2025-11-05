#!/usr/bin/env python3
"""
Script para corrigir nomes de ligas no banco de dados
Converte IDs de ligas (como "71") para nomes legíveis
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.match import Match

# Mapeamento de IDs de ligas para nomes
LEAGUE_NAMES = {
    "71": "Brasileirão Série A",
    "72": "Brasileirão Série B",
    "73": "Brasileirão Série C",
    "74": "Brasileirão Série D",
    "75": "Copa do Brasil",
    "76": "Copa do Nordeste",
    "77": "Copa Verde",
    "13": "Copa Libertadores",
    "11": "Copa Sul-Americana",
    "128": "Liga Profesional Argentina",
    "135": "Campeonato Argentino - Primera División",
    "39": "Premier League",
    "140": "La Liga",
    "78": "Bundesliga",
    "135": "Serie A (Itália)",
    "61": "Ligue 1",
    "94": "Primeira Liga (Portugal)",
    "203": "Süper Lig (Turquia)",
    "88": "Eredivisie (Holanda)",
    "119": "Superliga (Dinamarca)",
    "144": "Jupiler Pro League (Bélgica)",
    "113": "Allsvenskan (Suécia)",
    "103": "Eliteserien (Noruega)",
    "96": "Liga NOS (Portugal)",
    "197": "Super League (Grécia)",
}

def fix_league_names(db: Session):
    """Corrige os nomes das ligas no banco de dados"""
    print("=" * 60)
    print("🔧 CORREÇÃO DE NOMES DE LIGAS")
    print("=" * 60)

    # Buscar todas as ligas distintas
    leagues = db.query(Match.league).distinct().all()
    leagues = [l[0] for l in leagues if l[0]]

    print(f"\n📊 Ligas encontradas no banco: {len(leagues)}")

    for league in sorted(leagues):
        print(f"  - {league}")

    print("\n" + "=" * 60)

    # Contar jogos por liga que precisam de correção
    to_fix = {}
    for league_id, league_name in LEAGUE_NAMES.items():
        count = db.query(Match).filter(Match.league == league_id).count()
        if count > 0:
            to_fix[league_id] = (league_name, count)

    if not to_fix:
        print("✅ Nenhuma liga precisa de correção!")
        return

    print(f"⚠️ Encontradas {len(to_fix)} ligas com IDs numéricos:\n")

    for league_id, (league_name, count) in to_fix.items():
        print(f"  {league_id} → {league_name} ({count} jogos)")

    print("\n" + "=" * 60)

    # Confirmar correção
    print("🔄 Iniciando correção...\n")

    total_updated = 0

    for league_id, (league_name, count) in to_fix.items():
        print(f"  Corrigindo '{league_id}' → '{league_name}'...", end=" ")

        matches = db.query(Match).filter(Match.league == league_id).all()

        for match in matches:
            match.league = league_name

        db.commit()
        total_updated += count

        print(f"✅ {count} jogos atualizados")

    print("\n" + "=" * 60)
    print(f"✅ CORREÇÃO CONCLUÍDA!")
    print(f"📊 Total: {total_updated} jogos atualizados")
    print("=" * 60)

    # Mostrar ligas após correção
    print("\n📋 Ligas no banco após correção:\n")
    leagues_after = db.query(Match.league).distinct().all()
    leagues_after = [l[0] for l in leagues_after if l[0]]

    for league in sorted(leagues_after):
        count = db.query(Match).filter(Match.league == league).count()
        print(f"  - {league} ({count} jogos)")

def main():
    db = SessionLocal()
    try:
        fix_league_names(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
