#!/usr/bin/env python3
"""
🔧 Corrigir Status de Jogos "Ao Vivo" Antigos

Marca jogos com status LIVE/HT/1H/2H que já finalizaram como FT
"""
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Match

# Database
engine = create_engine("sqlite:///./football_analytics_dev.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def fix_stale_live_matches():
    """
    Marca jogos com status LIVE mas que já deveriam ter terminado
    (mais de 2 horas desde o início) como FT
    """
    # Data limite: jogos que começaram há mais de 2 horas
    cutoff_time = datetime.now() - timedelta(hours=2)

    print(f"🔍 Buscando jogos 'ao vivo' que começaram antes de {cutoff_time.strftime('%d/%m/%Y %H:%M')}...")

    # Buscar jogos "ao vivo" antigos
    stale_live_matches = db.query(Match).filter(
        Match.match_date < cutoff_time,
        Match.status.in_(['LIVE', 'HT', '1H', '2H', 'BT', 'ET', 'P', 'SUSP', 'INT'])
    ).all()

    print(f"📋 Encontrados {len(stale_live_matches)} jogos com status 'ao vivo' desatualizados")

    if len(stale_live_matches) == 0:
        print("✅ Nenhum jogo para corrigir!")
        return

    updated_count = 0
    for match in stale_live_matches:
        # Marcar como finalizado
        old_status = match.status
        match.status = 'FT'
        updated_count += 1

        print(f"  ✓ {match.home_team.name} vs {match.away_team.name}")
        print(f"    {match.match_date.strftime('%d/%m/%Y %H:%M')} - {old_status} → FT")

    db.commit()

    print(f"\n✅ {updated_count} jogos marcados como finalizados")
    print(f"⚠️  Agora o scheduler deve rodar mais rápido")

    # Verificar quantos jogos ao vivo restam
    remaining_live = db.query(Match).filter(
        Match.status.in_(['LIVE', 'HT', '1H', '2H'])
    ).count()

    print(f"\n📊 Jogos realmente ao vivo restantes: {remaining_live}")

    db.close()

if __name__ == "__main__":
    fix_stale_live_matches()
