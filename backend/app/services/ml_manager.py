"""
🎯 ML MANAGER - Gerenciador Principal do Sistema de Machine Learning
Coordena treinamento, predições e integração com o motor matemático
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

from app.services.ml_prediction_engine import MLPredictionEngine
from app.services.ml_training_service import MLTrainingService
from app.services.real_prediction_engine import RealPredictionEngine
from app.core.config import settings

class MLManager:
    """
    🎯 Gerenciador central do sistema de ML
    Coordena todas as operações de machine learning
    """

    def __init__(self):
        self.ml_engine = MLPredictionEngine()
        self.training_service = MLTrainingService()
        self.real_engine = RealPredictionEngine()

        # Status do sistema
        self.system_status = {
            'models_trained': False,
            'last_training_date': None,
            'models_available': [],
            'training_in_progress': False
        }

        # Configurações
        self.config = {
            'auto_retrain_days': 30,  # Retreinar a cada 30 dias
            'min_prediction_confidence': 0.6,
            'ensemble_weights': {
                'ml_weight': 0.6,
                'mathematical_weight': 0.4
            }
        }

    async def initialize_ml_system(self) -> Dict:
        """
        🚀 Inicializar sistema de ML completo
        """
        print("🚀 INICIALIZANDO SISTEMA DE MACHINE LEARNING")
        print("=" * 50)

        initialization_result = {
            'status': 'INITIALIZING',
            'steps': [],
            'errors': [],
            'start_time': datetime.now().isoformat()
        }

        try:
            # 1. Verificar se modelos existem
            print("🔍 Verificando modelos existentes...")
            models_check = await self._check_existing_models()
            initialization_result['steps'].append({
                'step': 'check_models',
                'result': models_check,
                'timestamp': datetime.now().isoformat()
            })

            # 2. Se não existem modelos, fazer treinamento inicial
            if not models_check['models_exist']:
                print("🎓 Modelos não encontrados. Iniciando treinamento inicial...")
                training_result = await self.training_service.run_full_training_pipeline()
                initialization_result['steps'].append({
                    'step': 'initial_training',
                    'result': training_result,
                    'timestamp': datetime.now().isoformat()
                })

                if training_result.get('status') != 'SUCCESS':
                    initialization_result['errors'].extend(training_result.get('errors', []))
                    initialization_result['status'] = 'FAILED'
                    return initialization_result

            # 3. Carregar modelos
            print("📥 Carregando modelos...")
            load_result = await self._load_models()
            initialization_result['steps'].append({
                'step': 'load_models',
                'result': load_result,
                'timestamp': datetime.now().isoformat()
            })

            # 4. Teste de funcionamento
            print("🧪 Testando sistema...")
            test_result = await self._test_ml_system()
            initialization_result['steps'].append({
                'step': 'system_test',
                'result': test_result,
                'timestamp': datetime.now().isoformat()
            })

            # 5. Atualizar status
            await self._update_system_status()

            initialization_result['status'] = 'SUCCESS'
            initialization_result['end_time'] = datetime.now().isoformat()

            print("✅ Sistema de ML inicializado com sucesso!")
            return initialization_result

        except Exception as e:
            initialization_result['errors'].append(str(e))
            initialization_result['status'] = 'FAILED'
            initialization_result['end_time'] = datetime.now().isoformat()
            print(f"❌ Erro na inicialização: {e}")
            return initialization_result

    async def generate_enhanced_prediction(self, home_team_id: str, away_team_id: str, match_date: datetime = None) -> Dict:
        """
        🔮 Gerar predição avançada combinando ML + Matemática
        """
        if match_date is None:
            match_date = datetime.now()

        prediction_result = {
            'match_info': {
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'match_date': match_date.isoformat(),
                'prediction_timestamp': datetime.now().isoformat()
            },
            'predictions': {},
            'confidence': {},
            'recommendations': [],
            'system_status': self.system_status.copy()
        }

        try:
            print(f"🔮 Gerando predição avançada: {home_team_id} vs {away_team_id}")

            # 1. Verificar se modelos estão disponíveis
            if not self.system_status['models_trained']:
                print("⚠️ Modelos ML não disponíveis, usando apenas motor matemático...")
                math_only = await self.real_engine.generate_real_prediction(
                    f"{home_team_id}_vs_{away_team_id}",
                    home_team_id,
                    away_team_id,
                    match_date
                )
                prediction_result['predictions']['mathematical_only'] = math_only
                prediction_result['confidence']['overall'] = 'MEDIUM'
                prediction_result['recommendations'].append("Considere treinar modelos ML para predições mais precisas")
                return prediction_result

            # 2. Predição ML
            print("🤖 Gerando predição ML...")
            ml_prediction = await self.ml_engine.predict_with_ml(home_team_id, away_team_id, match_date)

            # 3. Predição Matemática
            print("📊 Gerando predição matemática...")
            math_prediction = await self.real_engine.generate_real_prediction(
                f"{home_team_id}_vs_{away_team_id}",
                home_team_id,
                away_team_id,
                match_date
            )

            # 4. Ensemble Inteligente
            print("🎯 Combinando predições em ensemble...")
            ensemble_prediction = await self._create_intelligent_ensemble(ml_prediction, math_prediction)

            # 5. Análise de Confiança
            confidence_analysis = await self._analyze_prediction_confidence(ml_prediction, math_prediction, ensemble_prediction)

            # 6. Recomendações
            recommendations = await self._generate_prediction_recommendations(ensemble_prediction, confidence_analysis)

            # Estruturar resultado final
            prediction_result.update({
                'predictions': {
                    'ml_prediction': ml_prediction,
                    'mathematical_prediction': math_prediction,
                    'ensemble_prediction': ensemble_prediction
                },
                'confidence': confidence_analysis,
                'recommendations': recommendations,
                'system_info': {
                    'ml_models_used': len(self.system_status.get('models_available', [])),
                    'ensemble_weights': self.config['ensemble_weights'],
                    'prediction_engine_version': '2.0_ML_Enhanced'
                }
            })

            print("✅ Predição avançada gerada com sucesso!")
            return prediction_result

        except Exception as e:
            prediction_result['error'] = str(e)
            prediction_result['recommendations'].append(f"Erro na predição: {str(e)}")
            print(f"❌ Erro na predição avançada: {e}")
            return prediction_result

    async def _create_intelligent_ensemble(self, ml_pred: Dict, math_pred: Dict) -> Dict:
        """
        🧠 Criar ensemble inteligente baseado na confiança de cada método
        """
        try:
            # Analisar qualidade das predições
            ml_confidence = self._extract_ml_confidence(ml_pred)
            math_confidence = self._extract_math_confidence(math_pred)

            # Ajustar pesos dinamicamente
            if ml_confidence > 0.7 and math_confidence < 0.6:
                ml_weight = 0.75
                math_weight = 0.25
            elif math_confidence > 0.7 and ml_confidence < 0.6:
                ml_weight = 0.4
                math_weight = 0.6
            else:
                ml_weight = self.config['ensemble_weights']['ml_weight']
                math_weight = self.config['ensemble_weights']['mathematical_weight']

            # Combinar predições
            ensemble = {}

            # Resultado 1X2
            if 'ml_predictions' in ml_pred and 'match_outcome' in math_pred:
                ml_result = ml_pred.get('ml_predictions', {}).get('result', {})
                math_result = math_pred.get('match_outcome', {})

                ensemble['match_outcome'] = {
                    'home_win_probability': (
                        ml_result.get('probabilities', {}).get('H', 0.33) * ml_weight +
                        math_result.get('home_win_probability', 0.33) * math_weight
                    ),
                    'draw_probability': (
                        ml_result.get('probabilities', {}).get('D', 0.33) * ml_weight +
                        math_result.get('draw_probability', 0.33) * math_weight
                    ),
                    'away_win_probability': (
                        ml_result.get('probabilities', {}).get('A', 0.33) * ml_weight +
                        math_result.get('away_win_probability', 0.33) * math_weight
                    )
                }

                # Determinar resultado mais provável
                probs = ensemble['match_outcome']
                max_prob = max(probs.values())
                if probs['home_win_probability'] == max_prob:
                    ensemble['match_outcome']['predicted_result'] = '1'
                elif probs['away_win_probability'] == max_prob:
                    ensemble['match_outcome']['predicted_result'] = '2'
                else:
                    ensemble['match_outcome']['predicted_result'] = 'X'

                ensemble['match_outcome']['confidence'] = max_prob

            # Gols
            if 'ml_predictions' in ml_pred and 'goals_prediction' in math_pred:
                ml_goals = ml_pred.get('ml_predictions', {}).get('goals', {}).get('predicted_total_goals', 2.5)
                math_goals = math_pred.get('goals_prediction', {}).get('expected_total_goals', 2.5)

                ensemble_goals = ml_goals * ml_weight + math_goals * math_weight

                ensemble['goals_prediction'] = {
                    'expected_total_goals': round(ensemble_goals, 2),
                    'over_2_5_probability': self._calculate_over_probability(ensemble_goals, 2.5),
                    'over_1_5_probability': self._calculate_over_probability(ensemble_goals, 1.5),
                    'over_3_5_probability': self._calculate_over_probability(ensemble_goals, 3.5)
                }

            # BTTS
            if 'btts_prediction' in math_pred:
                ensemble['btts_prediction'] = math_pred['btts_prediction']

            # Metadados do ensemble
            ensemble['ensemble_info'] = {
                'ml_weight_used': ml_weight,
                'math_weight_used': math_weight,
                'ml_confidence': ml_confidence,
                'math_confidence': math_confidence,
                'dynamic_weighting': True
            }

            return ensemble

        except Exception as e:
            print(f"❌ Erro no ensemble: {e}")
            return math_pred  # Fallback para predição matemática

    def _extract_ml_confidence(self, ml_pred: Dict) -> float:
        """Extrair nível de confiança da predição ML"""
        try:
            if 'ml_predictions' in ml_pred:
                result_probs = ml_pred['ml_predictions'].get('result', {}).get('probabilities', {})
                if result_probs:
                    return max(result_probs.values())
            return 0.5
        except:
            return 0.5

    def _extract_math_confidence(self, math_pred: Dict) -> float:
        """Extrair nível de confiança da predição matemática"""
        try:
            confidence_system = math_pred.get('confidence_system', {})
            return confidence_system.get('overall_confidence', 0.5)
        except:
            return 0.5

    def _calculate_over_probability(self, expected_goals: float, threshold: float) -> float:
        """Calcular probabilidade Over usando distribuição de Poisson"""
        try:
            from scipy.stats import poisson
            return 1 - poisson.cdf(threshold, expected_goals)
        except:
            # Fallback simples
            return max(0, min(1, (expected_goals - threshold) / 2))

    async def _analyze_prediction_confidence(self, ml_pred: Dict, math_pred: Dict, ensemble_pred: Dict) -> Dict:
        """
        📊 Analisar confiança das predições
        """
        try:
            ml_conf = self._extract_ml_confidence(ml_pred)
            math_conf = self._extract_math_confidence(math_pred)
            ensemble_conf = max(ensemble_pred.get('match_outcome', {}).get('confidence', 0.5), 0.5)

            # Classificar confiança
            def classify_confidence(conf):
                if conf >= 0.7:
                    return 'HIGH'
                elif conf >= 0.55:
                    return 'MEDIUM'
                else:
                    return 'LOW'

            return {
                'ml_confidence': {
                    'score': round(ml_conf, 3),
                    'level': classify_confidence(ml_conf)
                },
                'mathematical_confidence': {
                    'score': round(math_conf, 3),
                    'level': classify_confidence(math_conf)
                },
                'ensemble_confidence': {
                    'score': round(ensemble_conf, 3),
                    'level': classify_confidence(ensemble_conf)
                },
                'overall': classify_confidence(max(ml_conf, math_conf, ensemble_conf)),
                'agreement': abs(ml_conf - math_conf) < 0.2  # Se diferença < 20%
            }

        except Exception as e:
            return {
                'error': str(e),
                'overall': 'MEDIUM'
            }

    async def _generate_prediction_recommendations(self, ensemble_pred: Dict, confidence_analysis: Dict) -> List[str]:
        """
        💡 Gerar recomendações baseadas na predição
        """
        recommendations = []

        try:
            # Confiança geral
            overall_confidence = confidence_analysis.get('overall', 'MEDIUM')

            if overall_confidence == 'HIGH':
                recommendations.append("✅ Alta confiança - Predição muito confiável")
            elif overall_confidence == 'MEDIUM':
                recommendations.append("⚠️ Confiança moderada - Considere fatores adicionais")
            else:
                recommendations.append("❌ Baixa confiança - Use com cautela")

            # Análise do resultado
            match_outcome = ensemble_pred.get('match_outcome', {})
            predicted_result = match_outcome.get('predicted_result', '')
            confidence = match_outcome.get('confidence', 0)

            if confidence > 0.6:
                result_map = {'1': 'Vitória da Casa', 'X': 'Empate', '2': 'Vitória Visitante'}
                recommendations.append(f"🎯 Resultado mais provável: {result_map.get(predicted_result, 'Indefinido')}")

            # Análise de gols
            goals_pred = ensemble_pred.get('goals_prediction', {})
            expected_goals = goals_pred.get('expected_total_goals', 0)

            if expected_goals > 3.0:
                recommendations.append("⚽ Jogo com tendência a muitos gols (Over 2.5)")
            elif expected_goals < 2.0:
                recommendations.append("🔒 Jogo com tendência a poucos gols (Under 2.5)")

            # Acordância entre métodos
            if confidence_analysis.get('agreement', False):
                recommendations.append("🤝 ML e Análise Matemática concordam - Maior confiabilidade")
            else:
                recommendations.append("⚖️ Divergência entre métodos - Análise adicional recomendada")

        except Exception as e:
            recommendations.append(f"⚠️ Erro na análise: {str(e)}")

        return recommendations

    async def _check_existing_models(self) -> Dict:
        """Verificar se modelos já existem"""
        try:
            models_file = Path("app/ml/models/trained_models.joblib")
            return {
                'models_exist': models_file.exists(),
                'models_path': str(models_file),
                'file_size': models_file.stat().st_size if models_file.exists() else 0
            }
        except Exception as e:
            return {'models_exist': False, 'error': str(e)}

    async def _load_models(self) -> Dict:
        """Carregar modelos existentes"""
        try:
            models_data = await self.ml_engine._load_models()
            if models_data:
                self.system_status['models_trained'] = True
                self.system_status['models_available'] = list(models_data.get('result_models', {}).keys())
                return {'status': 'SUCCESS', 'models_loaded': len(self.system_status['models_available'])}
            return {'status': 'FAILED', 'error': 'No models found'}
        except Exception as e:
            return {'status': 'FAILED', 'error': str(e)}

    async def _test_ml_system(self) -> Dict:
        """Testar funcionamento do sistema ML"""
        try:
            # Teste simples com IDs fictícios
            test_result = await self.ml_engine.predict_with_ml("1", "2", datetime.now())
            return {
                'test_passed': 'error' not in test_result,
                'test_result': 'SUCCESS' if 'error' not in test_result else test_result.get('error')
            }
        except Exception as e:
            return {'test_passed': False, 'error': str(e)}

    async def _update_system_status(self):
        """Atualizar status do sistema"""
        self.system_status['last_training_date'] = datetime.now().isoformat()

    async def check_retrain_needed(self) -> bool:
        """Verificar se é necessário retreinar"""
        if not self.system_status['last_training_date']:
            return True

        last_train = datetime.fromisoformat(self.system_status['last_training_date'])
        days_since_train = (datetime.now() - last_train).days

        return days_since_train >= self.config['auto_retrain_days']

    async def auto_retrain_if_needed(self) -> Dict:
        """Retreinar automaticamente se necessário"""
        if await self.check_retrain_needed():
            print("🔄 Retreinamento automático iniciado...")
            return await self.training_service.quick_retrain()
        else:
            return {'status': 'NO_RETRAIN_NEEDED'}

# Instância global do manager
ml_manager = MLManager()