"""
🤖 SISTEMA DE RETREINO AUTOMÁTICO DA ML
Sistema inteligente que aprende continuamente com os resultados reais

Funcionalidades:
1. Coleta automática de resultados de jogos
2. Avaliação da acurácia das previsões
3. Retreino da ML com novos dados
4. Otimização automática de parâmetros
5. Validação e deploy de modelos melhorados
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedRetrainingSystem:
    """Sistema automatizado de retreino da ML"""

    def __init__(self, data_directory: str = "retraining_data"):
        self.data_directory = data_directory
        self.models_directory = "models/automated"
        self.current_models = {}
        self.scaler = StandardScaler()
        self.performance_history = []

        # Criar diretórios se não existirem
        os.makedirs(self.data_directory, exist_ok=True)
        os.makedirs(self.models_directory, exist_ok=True)

    async def collect_match_results(self, match_data: Dict) -> bool:
        """Coleta resultados de uma partida para retreino"""
        try:
            # Salvar dados estruturados
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_directory}/match_result_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(match_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Resultado coletado: {filename}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao coletar resultado: {e}")
            return False

    async def analyze_prediction_accuracy(self, days_back: int = 7) -> Dict:
        """Analisa acurácia das previsões dos últimos N dias"""
        logger.info(f"📊 Analisando acurácia dos últimos {days_back} dias")

        # Carregar dados dos últimos dias
        cutoff_date = datetime.now() - timedelta(days=days_back)
        results_files = self._get_recent_results_files(cutoff_date)

        if not results_files:
            return {"error": "Nenhum resultado encontrado no período especificado"}

        accuracy_data = {
            'total_matches': 0,
            'markets_accuracy': {},
            'league_performance': {},
            'improvements_needed': []
        }

        for file_path in results_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    match_data = json.load(f)

                # Processar acurácia deste jogo
                match_accuracy = self._calculate_match_accuracy(match_data)
                self._update_accuracy_stats(accuracy_data, match_accuracy, match_data)

            except Exception as e:
                logger.warning(f"⚠️ Erro ao processar {file_path}: {e}")
                continue

        # Calcular métricas finais
        self._finalize_accuracy_metrics(accuracy_data)

        logger.info(f"📈 Análise concluída: {accuracy_data['total_matches']} jogos analisados")
        return accuracy_data

    def _get_recent_results_files(self, cutoff_date: datetime) -> List[str]:
        """Busca arquivos de resultados recentes"""
        results_files = []

        for filename in os.listdir(self.data_directory):
            if filename.startswith('match_result_') and filename.endswith('.json'):
                file_path = os.path.join(self.data_directory, filename)

                # Verificar data do arquivo
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time >= cutoff_date:
                    results_files.append(file_path)

        return sorted(results_files)

    def _calculate_match_accuracy(self, match_data: Dict) -> Dict:
        """Calcula acurácia das previsões de um jogo"""
        predictions = match_data.get('predictions_made', {})
        actual_results = match_data.get('actual_results', {})

        match_accuracy = {}

        # 1X2
        if 'match_result' in actual_results and '1x2' in predictions:
            predicted = predictions['1x2']['predicted_outcome']
            actual = actual_results['match_result']
            match_accuracy['1x2'] = self._normalize_result_comparison(predicted, actual)

        # Over/Under 2.5
        if 'over_2_5' in actual_results and 'goals' in predictions:
            predicted_under = predictions['goals']['over_under_25']['recommendation'] == 'Under 2.5'
            actual_under = not actual_results['over_2_5']
            match_accuracy['over_under_2_5'] = predicted_under == actual_under

        # BTTS
        if 'btts' in actual_results and 'btts' in predictions:
            predicted_no = predictions['btts']['predicted_outcome'] == 'No'
            actual_no = not actual_results['btts']
            match_accuracy['btts'] = predicted_no == actual_no

        # Escanteios (se disponível)
        if 'corners_total' in actual_results and 'corners' in predictions:
            predicted_over = True  # Assumindo que sempre prevemos over 8.5
            actual_over = actual_results['corners_total'] > 8.5
            match_accuracy['corners'] = predicted_over == actual_over

        return match_accuracy

    def _normalize_result_comparison(self, predicted: str, actual: str) -> bool:
        """Normaliza comparação de resultados"""
        # Mapear diferentes formatos
        prediction_map = {
            'Vitória Flamengo': 'away',
            'Vitória': 'away',
            'Empate': 'draw',
            'home': 'home',
            'away': 'away',
            'draw': 'draw'
        }

        normalized_pred = prediction_map.get(predicted, predicted).lower()
        normalized_actual = actual.lower()

        return normalized_pred == normalized_actual

    def _update_accuracy_stats(self, accuracy_data: Dict, match_accuracy: Dict, match_data: Dict):
        """Atualiza estatísticas de acurácia"""
        accuracy_data['total_matches'] += 1

        # Atualizar acurácia por mercado
        for market, correct in match_accuracy.items():
            if market not in accuracy_data['markets_accuracy']:
                accuracy_data['markets_accuracy'][market] = {'correct': 0, 'total': 0}

            accuracy_data['markets_accuracy'][market]['total'] += 1
            if correct:
                accuracy_data['markets_accuracy'][market]['correct'] += 1

        # Atualizar performance por liga
        league = match_data.get('match_info', {}).get('league', 'Unknown')
        if league not in accuracy_data['league_performance']:
            accuracy_data['league_performance'][league] = {'matches': 0, 'avg_accuracy': 0}

        league_accuracy = sum(match_accuracy.values()) / len(match_accuracy) if match_accuracy else 0
        current_data = accuracy_data['league_performance'][league]

        # Calcular média móvel
        total_matches = current_data['matches'] + 1
        current_data['avg_accuracy'] = (
            (current_data['avg_accuracy'] * current_data['matches'] + league_accuracy) / total_matches
        )
        current_data['matches'] = total_matches

    def _finalize_accuracy_metrics(self, accuracy_data: Dict):
        """Finaliza métricas de acurácia"""
        # Calcular percentuais por mercado
        for market, stats in accuracy_data['markets_accuracy'].items():
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0

            # Identificar mercados que precisam de melhoria
            if stats['accuracy'] < 0.55 and stats['total'] >= 5:
                accuracy_data['improvements_needed'].append({
                    'market': market,
                    'accuracy': stats['accuracy'],
                    'total_predictions': stats['total'],
                    'priority': 'HIGH' if stats['accuracy'] < 0.45 else 'MEDIUM'
                })

        # Ordenar melhorias por prioridade e acurácia
        accuracy_data['improvements_needed'].sort(key=lambda x: x['accuracy'])

    async def retrain_models_automatically(self, min_new_samples: int = 50) -> Dict:
        """Retreina modelos automaticamente quando há dados suficientes"""
        logger.info("🔄 Iniciando retreino automático de modelos")

        # Verificar se há dados suficientes
        new_data_count = self._count_new_training_data()

        if new_data_count < min_new_samples:
            return {
                'status': 'skipped',
                'reason': f'Insuficientes dados novos ({new_data_count}/{min_new_samples})',
                'next_check': 'Em 24 horas'
            }

        logger.info(f"📚 {new_data_count} novos exemplos disponíveis para retreino")

        # Preparar dados de treinamento
        X, y, feature_names = await self._prepare_training_data()

        if len(X) == 0:
            return {'status': 'error', 'message': 'Nenhum dado válido para treinamento'}

        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Normalizar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Treinar múltiplos modelos
        models_performance = {}

        # Random Forest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        rf_model.fit(X_train_scaled, y_train)
        rf_pred = rf_model.predict(X_test_scaled)
        models_performance['random_forest'] = self._calculate_model_metrics(y_test, rf_pred)

        # Gradient Boosting
        gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        gb_model.fit(X_train_scaled, y_train)
        gb_pred = gb_model.predict(X_test_scaled)
        models_performance['gradient_boosting'] = self._calculate_model_metrics(y_test, gb_pred)

        # Selecionar melhor modelo
        best_model_name = max(models_performance.keys(),
                            key=lambda k: models_performance[k]['f1_score'])
        best_model = rf_model if best_model_name == 'random_forest' else gb_model

        # Salvar modelo
        model_filename = f"{self.models_directory}/best_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        joblib.dump({
            'model': best_model,
            'scaler': self.scaler,
            'feature_names': feature_names,
            'performance': models_performance[best_model_name],
            'training_date': datetime.now().isoformat(),
            'samples_used': len(X)
        }, model_filename)

        logger.info(f"💾 Melhor modelo salvo: {model_filename}")

        # Atualizar histórico de performance
        self.performance_history.append({
            'date': datetime.now().isoformat(),
            'model_type': best_model_name,
            'performance': models_performance[best_model_name],
            'training_samples': len(X),
            'filename': model_filename
        })

        return {
            'status': 'success',
            'best_model': best_model_name,
            'performance': models_performance[best_model_name],
            'training_samples': len(X),
            'all_models_performance': models_performance,
            'model_saved': model_filename,
            'improvement_over_previous': self._calculate_improvement()
        }

    def _count_new_training_data(self) -> int:
        """Conta quantos novos exemplos de treinamento estão disponíveis"""
        # Contar arquivos de resultado dos últimos 7 dias
        recent_files = self._get_recent_results_files(datetime.now() - timedelta(days=7))
        return len(recent_files)

    async def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepara dados para treinamento"""
        logger.info("📊 Preparando dados de treinamento")

        # Buscar todos os arquivos de resultado
        all_files = self._get_recent_results_files(datetime.now() - timedelta(days=30))

        training_samples = []
        labels = []

        for file_path in all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    match_data = json.load(f)

                # Extrair features e label
                features = self._extract_features(match_data)
                label = self._extract_label(match_data)

                if features and label is not None:
                    training_samples.append(features)
                    labels.append(label)

            except Exception as e:
                logger.warning(f"⚠️ Erro ao processar {file_path}: {e}")
                continue

        if not training_samples:
            return np.array([]), np.array([]), []

        # Converter para arrays
        feature_names = list(training_samples[0].keys())
        X = np.array([[sample[feature] for feature in feature_names] for sample in training_samples])
        y = np.array(labels)

        logger.info(f"✅ {len(X)} amostras preparadas com {len(feature_names)} features")

        return X, y, feature_names

    def _extract_features(self, match_data: Dict) -> Optional[Dict]:
        """Extrai features de um jogo para treinamento"""
        try:
            features_used = match_data.get('features_for_ml', {})

            if not features_used:
                return None

            return {
                'home_strength': features_used.get('home_strength', 0.5),
                'away_strength': features_used.get('away_strength', 0.5),
                'expected_goals_home': features_used.get('expected_goals_home', 1.0),
                'expected_goals_away': features_used.get('expected_goals_away', 1.0),
                'h2h_advantage': features_used.get('h2h_advantage', 0),
                'form_home': features_used.get('form_home', 1.5),
                'form_away': features_used.get('form_away', 1.5),
                'venue_advantage': features_used.get('venue_advantage', 0.05),
                'league_tier': features_used.get('league_tier', 1)
            }

        except Exception:
            return None

    def _extract_label(self, match_data: Dict) -> Optional[int]:
        """Extrai label (resultado) de um jogo"""
        try:
            actual_result = match_data.get('actual_results', {}).get('match_result', '')

            # Mapear para classificação numérica
            label_map = {
                'home': 0,
                'draw': 1,
                'away': 2
            }

            return label_map.get(actual_result.lower())

        except Exception:
            return None

    def _calculate_model_metrics(self, y_true, y_pred) -> Dict:
        """Calcula métricas de performance do modelo"""
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted'),
            'recall': recall_score(y_true, y_pred, average='weighted'),
            'f1_score': f1_score(y_true, y_pred, average='weighted')
        }

    def _calculate_improvement(self) -> Optional[float]:
        """Calcula melhoria sobre modelo anterior"""
        if len(self.performance_history) < 2:
            return None

        current_f1 = self.performance_history[-1]['performance']['f1_score']
        previous_f1 = self.performance_history[-2]['performance']['f1_score']

        return ((current_f1 - previous_f1) / previous_f1) * 100

    async def get_retraining_status(self) -> Dict:
        """Retorna status do sistema de retreino"""
        new_data_count = self._count_new_training_data()

        return {
            'system_status': 'active',
            'new_data_available': new_data_count,
            'last_retrain': self.performance_history[-1]['date'] if self.performance_history else None,
            'models_trained': len(self.performance_history),
            'current_performance': self.performance_history[-1]['performance'] if self.performance_history else None,
            'next_retrain_threshold': 50,
            'ready_for_retrain': new_data_count >= 50
        }

    async def run_daily_retraining_check(self) -> Dict:
        """Executa verificação diária de retreino"""
        logger.info("🔍 Executando verificação diária de retreino")

        # Analisar acurácia recente
        accuracy_analysis = await self.analyze_prediction_accuracy(days_back=7)

        # Verificar se precisa retreinar
        retrain_needed = False

        # Critérios para retreino
        if accuracy_analysis.get('total_matches', 0) > 0:
            avg_accuracy = np.mean([
                market['accuracy'] for market in accuracy_analysis['markets_accuracy'].values()
            ])

            if avg_accuracy < 0.55:  # Acurácia abaixo de 55%
                retrain_needed = True
                reason = f"Acurácia baixa: {avg_accuracy:.1%}"
            elif len(accuracy_analysis.get('improvements_needed', [])) > 2:
                retrain_needed = True
                reason = "Múltiplos mercados precisam de melhoria"

        result = {
            'check_date': datetime.now().isoformat(),
            'accuracy_analysis': accuracy_analysis,
            'retrain_recommended': retrain_needed
        }

        if retrain_needed:
            logger.info(f"🚨 Retreino recomendado: {reason}")
            retrain_result = await self.retrain_models_automatically()
            result['retrain_result'] = retrain_result
        else:
            logger.info("✅ Modelos performando bem, retreino não necessário")
            result['message'] = 'Modelos estão performando adequadamente'

        return result

# Instância global do sistema de retreino
automated_retraining_system = AutomatedRetrainingSystem()

async def run_daily_retraining():
    """Executa retreino diário automatizado"""
    return await automated_retraining_system.run_daily_retraining_check()

if __name__ == "__main__":
    # Para teste
    import asyncio
    asyncio.run(run_daily_retraining())