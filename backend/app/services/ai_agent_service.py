"""
🧠 AI AGENT SERVICE - Análise Contextual Gratuita
Usa Ollama (local) + LangChain para refinar predictions do ML

Stack:
- Ollama (Llama 3.1 8B/70B) - FREE, local
- LangChain - Orchestration
- Zero custo de API
"""
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    AI Agent para análise contextual de predictions
    Usa LLM local (Ollama) sem custos
    """

    def __init__(self, model: str = "llama3.1:8b"):
        """
        Inicializa AI Agent

        Args:
            model: Modelo Ollama (llama3.1:8b, llama3.1:70b, mistral:7b)
        """
        self.model = model
        self.llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Inicializa conexão com Ollama"""
        try:
            from langchain_community.llms import Ollama

            self.llm = Ollama(
                model=self.model,
                temperature=0.3,  # Baixa temperatura = mais consistente
                num_ctx=4096,     # Contexto grande para análises
            )
            logger.info(f"✅ AI Agent inicializado com modelo: {self.model}")

        except ImportError:
            logger.error("❌ langchain_community não instalado. Instale: pip install langchain langchain-community")
            self.llm = None

        except Exception as e:
            logger.error(f"❌ Erro ao conectar Ollama: {e}")
            logger.error("🔧 Certifique-se que Ollama está rodando: ollama serve")
            self.llm = None

    def is_available(self) -> bool:
        """Verifica se AI Agent está disponível"""
        return self.llm is not None

    def analyze_prediction(
        self,
        match_data: Dict,
        ml_prediction: Dict,
        context_data: Dict,
        few_shot_examples: List[Dict] = None
    ) -> Dict:
        """
        Analisa prediction com contexto profundo

        Args:
            match_data: Dados do jogo (times, liga, data)
            ml_prediction: Prediction do ML (probabilidades, confidence)
            context_data: Contexto externo (notícias, clima, tabela)
            few_shot_examples: Exemplos de GREEN/RED para aprendizado

        Returns:
            Análise completa com raciocínio e ajuste de confidence
        """
        if not self.is_available():
            logger.warning("AI Agent não disponível, retornando análise básica")
            return self._fallback_analysis(ml_prediction)

        try:
            # Construir prompt com contexto completo
            prompt = self._build_analysis_prompt(
                match_data,
                ml_prediction,
                context_data,
                few_shot_examples
            )

            # Executar análise com LLM
            logger.info(f"🧠 Analisando: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            response = self.llm.invoke(prompt)

            # Parsear resposta do LLM
            analysis = self._parse_llm_response(response, ml_prediction)

            logger.info(f"✅ Análise concluída - Confidence ajustada: {analysis['adjusted_confidence']:.2%}")
            return analysis

        except Exception as e:
            logger.error(f"❌ Erro na análise AI: {e}")
            return self._fallback_analysis(ml_prediction)

    def _build_analysis_prompt(
        self,
        match_data: Dict,
        ml_prediction: Dict,
        context_data: Dict,
        few_shot_examples: List[Dict] = None
    ) -> str:
        """Constrói prompt otimizado para análise"""

        # Few-shot examples (se disponível)
        examples_text = ""
        if few_shot_examples:
            examples_text = "\n\n📚 EXEMPLOS DE APRENDIZADO:\n"
            for ex in few_shot_examples[:5]:  # Máximo 5 exemplos
                examples_text += f"\n{ex['description']}\nResultado: {ex['outcome']} ({ex['label']})\n"

        # Construir contexto de notícias
        news_text = ""
        if context_data.get('recent_news'):
            news_text = "\n\n📰 NOTÍCIAS RECENTES:\n"
            for news in context_data['recent_news'][:3]:
                news_text += f"• {news}\n"

        prompt = f"""Você é um analista profissional de apostas esportivas. Analise esta previsão de jogo considerando TODOS os fatores contextuais.

🏟️ JOGO:
{match_data['home_team']} vs {match_data['away_team']}
Liga: {match_data.get('league', 'N/A')}
Data: {match_data.get('match_date', 'N/A')}

📊 ANÁLISE MATEMÁTICA (ML):
• Probabilidades:
  - Casa: {ml_prediction.get('probability_home', 0):.1%}
  - Empate: {ml_prediction.get('probability_draw', 0):.1%}
  - Fora: {ml_prediction.get('probability_away', 0):.1%}
• Prediction: {ml_prediction.get('predicted_outcome')}
• Confidence ML: {ml_prediction.get('confidence', 0):.1%}
• Mercados analisados: {', '.join(ml_prediction.get('markets', ['1X2']))}

🌍 CONTEXTO EXTERNO:
• Rivalidade: {context_data.get('rivalry_level', 'baixa')}
• Motivação Casa: {context_data.get('motivation_home', 'normal')}
• Motivação Fora: {context_data.get('motivation_away', 'normal')}
• Clima: {context_data.get('weather', 'bom')}
• Lesões importantes: {', '.join(context_data.get('key_injuries', ['nenhuma']))}
• Posição tabela (Casa): {context_data.get('home_position', 'N/A')}
• Posição tabela (Fora): {context_data.get('away_position', 'N/A')}
{news_text}
{examples_text}

📋 SUA TAREFA:

1. ANALISE os fatores contextuais que o ML não consegue ver
2. IDENTIFIQUE fatores que podem aumentar ou diminuir a confidence
3. AJUSTE a confidence do ML baseado no contexto (pode subir ou descer)
4. EXPLIQUE seu raciocínio de forma clara
5. DÊ uma recomendação final (BET / SKIP / MONITOR)

RESPONDA NO FORMATO JSON:

{{
  "context_analysis": "Análise detalhada dos fatores contextuais",
  "key_factors": ["fator1", "fator2", "fator3"],
  "confidence_adjustment": 0.72,
  "adjustment_reasoning": "Por que ajustou a confidence",
  "recommendation": "BET",
  "risk_level": "MEDIUM",
  "explanation": "Explicação completa para o usuário"
}}

IMPORTANTE:
- Sea confidence ML já é boa E contexto favorável → AUMENTE (até 0.85 max)
- Se contexto desfavorável (chuva, lesões chave) → DIMINUA
- Se muita incerteza → Recomende SKIP
- Seja objetivo e baseado em dados
"""

        return prompt

    def _parse_llm_response(self, response: str, ml_prediction: Dict) -> Dict:
        """
        Parseia resposta do LLM e extrai dados estruturados

        Args:
            response: Resposta em texto do LLM
            ml_prediction: Prediction original do ML

        Returns:
            Análise estruturada
        """
        try:
            # Tentar extrair JSON da resposta
            # LLMs às vezes adicionam texto antes/depois do JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)

                # Validar e normalizar
                return {
                    'context_analysis': parsed.get('context_analysis', ''),
                    'key_factors': parsed.get('key_factors', []),
                    'adjusted_confidence': float(parsed.get('confidence_adjustment', ml_prediction.get('confidence', 0.5))),
                    'adjustment_reasoning': parsed.get('adjustment_reasoning', ''),
                    'recommendation': parsed.get('recommendation', 'MONITOR').upper(),
                    'risk_level': parsed.get('risk_level', 'MEDIUM').upper(),
                    'explanation': parsed.get('explanation', ''),
                    'ml_confidence': ml_prediction.get('confidence', 0.5),
                    'confidence_delta': float(parsed.get('confidence_adjustment', 0.5)) - ml_prediction.get('confidence', 0.5)
                }

            else:
                raise ValueError("JSON não encontrado na resposta")

        except Exception as e:
            logger.error(f"Erro ao parsear resposta LLM: {e}")
            logger.debug(f"Resposta original: {response}")

            # Fallback: extrair informações do texto livre
            return {
                'context_analysis': response[:500],  # Primeiros 500 chars
                'key_factors': [],
                'adjusted_confidence': ml_prediction.get('confidence', 0.5),
                'adjustment_reasoning': 'Análise textual (sem JSON)',
                'recommendation': 'MONITOR',
                'risk_level': 'MEDIUM',
                'explanation': response,
                'ml_confidence': ml_prediction.get('confidence', 0.5),
                'confidence_delta': 0.0
            }

    def _fallback_analysis(self, ml_prediction: Dict) -> Dict:
        """Análise básica quando AI Agent não está disponível"""
        return {
            'context_analysis': 'AI Agent não disponível - usando apenas ML',
            'key_factors': ['Análise matemática pura'],
            'adjusted_confidence': ml_prediction.get('confidence', 0.5),
            'adjustment_reasoning': 'Sem análise contextual',
            'recommendation': 'MONITOR',
            'risk_level': 'MEDIUM',
            'explanation': 'Esta prediction foi gerada apenas com ML. Ative o AI Agent para análise contextual.',
            'ml_confidence': ml_prediction.get('confidence', 0.5),
            'confidence_delta': 0.0,
            'ai_available': False
        }

    def batch_analyze(
        self,
        predictions: List[Dict],
        context_data_list: List[Dict],
        max_concurrent: int = 5
    ) -> List[Dict]:
        """
        Analisa múltiplas predictions em batch

        Args:
            predictions: Lista de predictions com match_data e ml_prediction
            context_data_list: Lista de contextos correspondentes
            max_concurrent: Máximo de análises simultâneas

        Returns:
            Lista de análises
        """
        if not self.is_available():
            logger.warning("AI Agent não disponível para batch analysis")
            return [self._fallback_analysis(p['ml_prediction']) for p in predictions]

        results = []

        # Processar em lotes para não sobrecarregar
        for i in range(0, len(predictions), max_concurrent):
            batch = predictions[i:i + max_concurrent]
            batch_contexts = context_data_list[i:i + max_concurrent]

            for pred, context in zip(batch, batch_contexts):
                analysis = self.analyze_prediction(
                    match_data=pred['match_data'],
                    ml_prediction=pred['ml_prediction'],
                    context_data=context
                )
                results.append(analysis)

        logger.info(f"✅ Batch analysis concluída: {len(results)} predictions analisadas")
        return results
