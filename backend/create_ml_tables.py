#!/usr/bin/env python3
"""
🗄️ CRIAÇÃO DE TABELAS ML
Script para criar as tabelas necessárias para o sistema de logging e performance do ML
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine, Base
from app.models import PredictionLog, ModelPerformance

def create_ml_tables():
    """Cria as tabelas necessárias para o sistema ML"""
    print("🗄️ Criando tabelas para sistema ML...")
    
    try:
        # Criar tabelas
        Base.metadata.create_all(bind=engine, tables=[
            PredictionLog.__table__,
            ModelPerformance.__table__
        ])
        
        print("✅ Tabelas criadas com sucesso:")
        print("   - prediction_logs")
        print("   - model_performance")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

if __name__ == "__main__":
    create_ml_tables()
