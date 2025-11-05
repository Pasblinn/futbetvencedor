#!/usr/bin/env python3
"""
🧹 Limpar Jogos Antigos das Predictions

Remove jogos antes de 06/10/2025 das predictions
(mantém no banco para histórico e análise)
"""
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Match

# Database
engine = create_engine("sqlite:///./football_analytics_dev.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def clean_old_matches():
    """
    Marca jogos antes de 06/10/2025 como finalizados
    se ainda estiverem com status de agendado
    """
    # Data limite: 06/10/2025 00:00
    cutoff_date = datetime(2025, 10, 6, 0, 0, 0)

    print(f"🔍 Buscando jogos antes de {cutoff_date.strftime('%d/%m/%Y')}...")

    # Buscar jogos antigos ainda com status de agendado
    old_matches = db.query(Match).filter(
        Match.match_date < cutoff_date,
        Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
    ).all()

    print(f"📋 Encontrados {len(old_matches)} jogos antigos ainda marcados como agendados")

    updated_count = 0
    for match in old_matches:
        # Marcar como finalizado (sem resultado se não tiver)
        match.status = 'FT'  # Finished
        updated_count += 1
        print(f"  ✓ {match.home_team} vs {match.away_team} - {match.match_date.strftime('%d/%m/%Y')} → FT")

    db.commit()

    print(f"\n✅ {updated_count} jogos marcados como finalizados")
    print("⚠️  Esses jogos agora NÃO aparecerão em Predictions")
    print("✓  Eles permanecem no banco para histórico e análise")

    # Verificar quantos jogos válidos restam
    valid_matches = db.query(Match).filter(
        Match.status.in_(['NS', 'TBD', 'SCHEDULED', 'LIVE', 'HT', '1H', '2H'])
    ).count()

    print(f"\n📊 Jogos válidos restantes em Predictions: {valid_matches}")

    db.close()

if __name__ == "__main__":
    clean_old_matches()
