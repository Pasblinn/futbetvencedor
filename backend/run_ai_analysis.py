#!/usr/bin/env python3
"""
🧠 Script para executar análise AI Agent nas predictions
"""
import sys
from app.services.automated_pipeline import run_ai_batch_analysis

if __name__ == "__main__":
    print("=" * 70)
    print("🧠 EXECUTANDO ANÁLISE AI AGENT EM LOTE")
    print("=" * 70)

    result = run_ai_batch_analysis()

    print("\n" + "=" * 70)
    print("✅ RESULTADO DA ANÁLISE AI:")
    print("=" * 70)

    for key, value in result.items():
        print(f"  {key}: {value}")

    print("=" * 70)
