"""
🎓 ML TRAINING SERVICE - Serviço de Treinamento Automatizado
Coleta dados históricos e treina modelos de ML periodicamente
Inclui validação, backtesting e otimização de hiperparâmetros
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
import joblib

from app.services.ml_prediction_engine import MLPredictionEngine
from app.services.football_data_service import FootballDataService
from app.core.config import settings

class MLTrainingService:
    """
    🔄 Serviço automatizado para treinamento e validação de modelos ML
    """

    def __init__(self):
        self.ml_engine = MLPredictionEngine()
        self.football_service = FootballDataService()

        # Configurações de treinamento
        self.training_config = {
            'min_historical_days': 90,  # Mínimo 3 meses de dados (mais realista para API gratuita)
            'max_historical_days': 180,  # Máximo 6 meses (limite API gratuita)
            'min_matches_per_team': 10,  # Reduzido para compensar período menor
            'validation_split': 0.2,
            'major_leagues': ['PL', 'PD'],  # Apenas Premier League e La Liga para início (respeitar rate limits)
            'chunk_days': 30,  # Coletar dados em chunks de 30 dias para evitar timeout
            'rate_limit_delay': 2.0  # Aumentar pausa entre requests para respeitar API limits
        }

        # Diretórios
        self.models_dir = Path("app/ml/models")
        self.data_dir = Path("app/ml/data")
        self.reports_dir = Path("app/ml/reports")

        for dir_path in [self.models_dir, self.data_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    async def run_full_training_pipeline(self) -> Dict:
        """
        🚀 Pipeline completo de treinamento de ML
        """
        print("🚀 INICIANDO PIPELINE COMPLETO DE TREINAMENTO ML")
        print("=" * 60)

        pipeline_results = {
            'start_time': datetime.now().isoformat(),
            'steps': {},
            'final_metrics': {},
            'errors': []
        }

        try:
            # 1. Coleta de dados históricos
            print("\n📊 ETAPA 1: Coletando dados históricos...")
            data_result = await self._collect_historical_data()
            pipeline_results['steps']['data_collection'] = data_result

            if data_result.get('error'):
                pipeline_results['errors'].append(f"Data collection: {data_result['error']}")
                return pipeline_results

            # 2. Preparação e limpeza dos dados
            print("\n🧹 ETAPA 2: Preparando e limpando dados...")
            prep_result = await self._prepare_training_data(data_result['matches'])
            pipeline_results['steps']['data_preparation'] = prep_result

            # 3. Feature engineering
            print("\n🔧 ETAPA 3: Criando features avançadas...")
            features_df = await self.ml_engine.create_advanced_features(prep_result['cleaned_matches'])
            pipeline_results['steps']['feature_engineering'] = {
                'total_features': len(features_df.columns) if not features_df.empty else 0,
                'total_samples': len(features_df) if not features_df.empty else 0
            }

            if features_df.empty:
                pipeline_results['errors'].append("Feature engineering failed - empty dataset")
                return pipeline_results

            # 4. Divisão treino/validação
            print("\n📊 ETAPA 4: Dividindo dados para treinamento e validação...")
            train_test_result = await self._split_train_validation(features_df)
            pipeline_results['steps']['train_test_split'] = train_test_result

            # 5. Treinamento dos modelos
            print("\n🎓 ETAPA 5: Treinando modelos de ML...")
            training_result = await self.ml_engine.train_models(train_test_result['train_df'])
            pipeline_results['steps']['model_training'] = {
                'result_models_trained': len(training_result.get('result_models', {})),
                'goals_models_trained': len(training_result.get('goals_models', {})),
                'training_samples': training_result.get('training_samples', 0)
            }

            # 6. Validação e backtesting
            print("\n✅ ETAPA 6: Validando modelos...")
            validation_result = await self._validate_models(train_test_result['validation_df'], training_result)
            pipeline_results['steps']['validation'] = validation_result

            # 7. Relatório final
            print("\n📋 ETAPA 7: Gerando relatório...")
            report_result = await self._generate_training_report(pipeline_results, validation_result)
            pipeline_results['steps']['report_generation'] = report_result

            pipeline_results['end_time'] = datetime.now().isoformat()
            pipeline_results['status'] = 'SUCCESS'

            print(f"\n✅ PIPELINE CONCLUÍDO COM SUCESSO!")
            print(f"📊 {pipeline_results['steps']['feature_engineering']['total_samples']} amostras processadas")
            print(f"🎓 {pipeline_results['steps']['model_training']['result_models_trained']} modelos de resultado treinados")
            print(f"⚽ {pipeline_results['steps']['model_training']['goals_models_trained']} modelos de gols treinados")

            return pipeline_results

        except Exception as e:
            pipeline_results['errors'].append(f"Pipeline error: {str(e)}")
            pipeline_results['status'] = 'FAILED'
            pipeline_results['end_time'] = datetime.now().isoformat()
            print(f"❌ Erro no pipeline: {e}")
            return pipeline_results

    async def _collect_historical_data(self) -> Dict:
        """📚 Coletar dados históricos de múltiplas ligas em chunks menores"""
        try:
            all_matches = []
            league_stats = {}

            # Data de corte para dados históricos
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.training_config['max_historical_days'])
            chunk_days = self.training_config['chunk_days']

            print(f"📅 Coletando dados de {start_date.strftime('%Y-%m-%d')} até {end_date.strftime('%Y-%m-%d')}")
            print(f"📦 Usando chunks de {chunk_days} dias para otimizar API calls")

            for league in self.training_config['major_leagues']:
                try:
                    print(f"   🏆 Processando {league}...")
                    league_matches = []

                    # Coletar dados em chunks para evitar timeout/limite da API
                    current_date = start_date
                    chunk_count = 0

                    while current_date < end_date:
                        chunk_end = min(current_date + timedelta(days=chunk_days), end_date)
                        chunk_count += 1

                        try:
                            print(f"      📦 Chunk {chunk_count}: {current_date.strftime('%Y-%m-%d')} até {chunk_end.strftime('%Y-%m-%d')}")

                            chunk_matches = await self.football_service.get_matches_by_competition(
                                league,
                                current_date.strftime('%Y-%m-%d'),
                                chunk_end.strftime('%Y-%m-%d')
                            )

                            league_matches.extend(chunk_matches)
                            print(f"         ✅ {len(chunk_matches)} jogos no chunk")

                            # Pausa entre chunks para respeitar rate limits da API
                            await asyncio.sleep(self.training_config['rate_limit_delay'])

                        except Exception as chunk_error:
                            print(f"         ❌ Erro no chunk: {chunk_error}")
                            continue

                        current_date = chunk_end

                    # Filtrar apenas jogos finalizados
                    finished_matches = [m for m in league_matches if m.get('status') == 'FINISHED']

                    league_stats[league] = {
                        'total_matches': len(league_matches),
                        'finished_matches': len(finished_matches),
                        'chunks_processed': chunk_count
                    }

                    all_matches.extend(finished_matches)
                    print(f"      ✅ {len(finished_matches)} jogos finalizados coletados no total")

                except Exception as e:
                    print(f"      ❌ Erro na liga {league}: {e}")
                    league_stats[league] = {'error': str(e)}

            print(f"\n📊 Total de jogos coletados: {len(all_matches)}")

            # Salvar dados brutos
            data_file = self.data_dir / f"historical_matches_{datetime.now().strftime('%Y%m%d')}.json"
            with open(data_file, 'w') as f:
                json.dump(all_matches, f, indent=2, default=str)

            return {
                'matches': all_matches,
                'total_matches': len(all_matches),
                'league_stats': league_stats,
                'data_file': str(data_file),
                'collection_date': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': str(e)}

    async def _prepare_training_data(self, matches: List[Dict]) -> Dict:
        """🧹 Preparar e limpar dados para treinamento"""
        try:
            print(f"🧹 Preparando {len(matches)} jogos...")

            # Filtros de qualidade
            cleaned_matches = []
            team_match_counts = {}

            for match in matches:
                # Verificar se tem dados essenciais
                if not all([
                    match.get('homeTeam', {}).get('id'),
                    match.get('awayTeam', {}).get('id'),
                    match.get('score', {}).get('fullTime', {}).get('home') is not None,
                    match.get('score', {}).get('fullTime', {}).get('away') is not None,
                    match.get('utcDate')
                ]):
                    continue

                home_id = str(match['homeTeam']['id'])
                away_id = str(match['awayTeam']['id'])

                # Contar jogos por time
                team_match_counts[home_id] = team_match_counts.get(home_id, 0) + 1
                team_match_counts[away_id] = team_match_counts.get(away_id, 0) + 1

                cleaned_matches.append(match)

            # Filtrar times com poucos jogos
            teams_with_enough_matches = {
                team_id for team_id, count in team_match_counts.items()
                if count >= self.training_config['min_matches_per_team']
            }

            final_matches = []
            for match in cleaned_matches:
                home_id = str(match['homeTeam']['id'])
                away_id = str(match['awayTeam']['id'])

                if home_id in teams_with_enough_matches and away_id in teams_with_enough_matches:
                    final_matches.append(match)

            print(f"✅ {len(final_matches)} jogos limpos e válidos")
            print(f"📊 {len(teams_with_enough_matches)} times com dados suficientes")

            return {
                'cleaned_matches': final_matches,
                'original_count': len(matches),
                'cleaned_count': len(final_matches),
                'teams_count': len(teams_with_enough_matches),
                'min_matches_per_team': self.training_config['min_matches_per_team']
            }

        except Exception as e:
            return {'error': str(e)}

    async def _split_train_validation(self, df: pd.DataFrame) -> Dict:
        """📊 Dividir dados em treino e validação (temporal)"""
        try:
            # Ordenar por data para split temporal
            if 'utcDate' in df.columns:
                df = df.sort_values('utcDate')

            total_samples = len(df)
            validation_size = int(total_samples * self.training_config['validation_split'])
            train_size = total_samples - validation_size

            # Split temporal (mais recentes para validação)
            train_df = df.iloc[:train_size].copy()
            validation_df = df.iloc[train_size:].copy()

            print(f"📊 Treino: {len(train_df)} amostras")
            print(f"✅ Validação: {len(validation_df)} amostras")

            return {
                'train_df': train_df,
                'validation_df': validation_df,
                'train_size': len(train_df),
                'validation_size': len(validation_df),
                'split_ratio': self.training_config['validation_split']
            }

        except Exception as e:
            return {'error': str(e)}

    async def _validate_models(self, validation_df: pd.DataFrame, trained_models: Dict) -> Dict:
        """✅ Validar modelos treinados"""
        try:
            print(f"✅ Validando modelos com {len(validation_df)} amostras...")

            validation_results = {
                'result_models_performance': {},
                'goals_models_performance': {},
                'overall_metrics': {}
            }

            # Preparar features de validação
            feature_columns = trained_models.get('feature_columns', [])
            if not feature_columns:
                return {'error': 'Feature columns not found in trained models'}

            # Selecionar apenas features disponíveis
            available_features = [col for col in feature_columns if col in validation_df.columns]
            X_val = validation_df[available_features]

            # Preencher valores faltando
            X_val = X_val.fillna(X_val.mean())

            # Targets
            y_result = validation_df['result'] if 'result' in validation_df.columns else None
            y_goals = validation_df['total_goals'] if 'total_goals' in validation_df.columns else None

            # Validar modelos de resultado
            if y_result is not None and 'result_models' in trained_models:
                print("🎯 Validando modelos de resultado...")

                X_result_scaled = self.ml_engine.result_scaler.transform(X_val)

                for model_name, model_data in trained_models['result_models'].items():
                    try:
                        model = model_data['model']
                        y_pred = model.predict(X_result_scaled)

                        accuracy = accuracy_score(y_result, y_pred)

                        validation_results['result_models_performance'][model_name] = {
                            'accuracy': accuracy,
                            'cv_score': model_data.get('cv_mean', 0),
                            'samples_validated': len(y_result)
                        }

                        print(f"   ✅ {model_name}: {accuracy:.3f} accuracy")

                    except Exception as e:
                        print(f"   ❌ Erro validando {model_name}: {e}")

            # Validar modelos de gols
            if y_goals is not None and 'goals_models' in trained_models:
                print("⚽ Validando modelos de gols...")

                X_goals_scaled = self.ml_engine.goals_scaler.transform(X_val)

                for model_name, model_data in trained_models['goals_models'].items():
                    try:
                        model = model_data['model']

                        if model_name == 'gradient_boosting':
                            # Para modelos de classificação de bins
                            y_goals_binned = pd.cut(y_goals, bins=[0, 1.5, 2.5, 3.5, 10], labels=['Low', 'Medium', 'High', 'Very High'])
                            y_pred = model.predict(X_goals_scaled)
                            accuracy = accuracy_score(y_goals_binned, y_pred)

                            validation_results['goals_models_performance'][model_name] = {
                                'accuracy': accuracy,
                                'cv_score': model_data.get('cv_mean', 0),
                                'type': 'classification'
                            }
                        else:
                            # Para modelos de regressão
                            y_pred = model.predict(X_goals_scaled)
                            mse = mean_squared_error(y_goals, y_pred)

                            validation_results['goals_models_performance'][model_name] = {
                                'mse': mse,
                                'rmse': np.sqrt(mse),
                                'cv_score': model_data.get('cv_mean', 0),
                                'type': 'regression'
                            }

                        print(f"   ✅ {model_name}: validado")

                    except Exception as e:
                        print(f"   ❌ Erro validando {model_name}: {e}")

            # Métricas gerais
            validation_results['overall_metrics'] = {
                'validation_samples': len(validation_df),
                'features_used': len(available_features),
                'validation_date': datetime.now().isoformat()
            }

            return validation_results

        except Exception as e:
            return {'error': str(e)}

    async def _generate_training_report(self, pipeline_results: Dict, validation_results: Dict) -> Dict:
        """📋 Gerar relatório detalhado do treinamento"""
        try:
            report = {
                'training_summary': {
                    'pipeline_status': pipeline_results.get('status', 'UNKNOWN'),
                    'start_time': pipeline_results.get('start_time'),
                    'end_time': pipeline_results.get('end_time'),
                    'total_errors': len(pipeline_results.get('errors', []))
                },
                'data_summary': pipeline_results.get('steps', {}).get('data_collection', {}),
                'model_performance': validation_results,
                'recommendations': []
            }

            # Gerar recomendações
            if validation_results.get('result_models_performance'):
                best_result_model = max(
                    validation_results['result_models_performance'].items(),
                    key=lambda x: x[1].get('accuracy', 0)
                )
                report['recommendations'].append(
                    f"Melhor modelo para resultados: {best_result_model[0]} "
                    f"(accuracy: {best_result_model[1].get('accuracy', 0):.3f})"
                )

            # Salvar relatório
            report_file = self.reports_dir / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"📋 Relatório salvo em: {report_file}")

            return {
                'report_file': str(report_file),
                'report_summary': report['training_summary']
            }

        except Exception as e:
            return {'error': str(e)}

    async def quick_retrain(self) -> Dict:
        """🔄 Retreinamento rápido com dados mais recentes"""
        print("🔄 Iniciando retreinamento rápido...")

        try:
            # Usar apenas dados dos últimos 6 meses para retreino rápido
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)

            # Coletar dados recentes
            recent_matches = []
            for league in ['PL', 'PD', 'SA', 'BL1']:  # Apenas top 4 ligas
                try:
                    matches = await self.football_service.get_matches_by_competition(
                        league,
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    finished = [m for m in matches if m.get('status') == 'FINISHED']
                    recent_matches.extend(finished)
                except:
                    continue

            if len(recent_matches) < 100:
                return {'error': 'Dados insuficientes para retreinamento rápido'}

            # Feature engineering
            features_df = await self.ml_engine.create_advanced_features(recent_matches)

            if features_df.empty:
                return {'error': 'Falha no feature engineering'}

            # Treinar apenas modelos principais
            training_result = await self.ml_engine.train_models(features_df)

            return {
                'status': 'SUCCESS',
                'samples_used': len(features_df),
                'models_trained': len(training_result.get('result_models', {})),
                'retrain_date': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': str(e)}