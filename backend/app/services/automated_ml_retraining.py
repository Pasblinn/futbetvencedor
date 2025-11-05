"""
🤖 SISTEMA DE RETREINO AUTOMÁTICO DE ML
Sistema inteligente para retreinar modelos baseado em performance e dados novos
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import joblib
import os
from pathlib import Path
import schedule
import time
from threading import Thread
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetrainingTrigger:
    trigger_type: str  # 'performance', 'data_volume', 'schedule', 'manual'
    threshold_value: float
    current_value: float
    triggered_at: datetime
    reason: str

@dataclass
class ModelPerformance:
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    samples_count: int
    last_evaluation: datetime
    trend: str  # 'improving', 'stable', 'degrading'

@dataclass
class RetrainingResult:
    success: bool
    model_name: str
    old_accuracy: float
    new_accuracy: float
    improvement: float
    training_samples: int
    training_duration: float
    model_path: str
    validation_report: Dict[str, Any]
    timestamp: datetime

class AutomatedMLRetraining:
    def __init__(self):
        self.models_dir = Path("models/automated")
        self.retraining_data_dir = Path("retraining_data")
        self.performance_log_dir = Path("logs")

        # Criar diretórios necessários
        for dir_path in [self.models_dir, self.retraining_data_dir, self.performance_log_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Configurações de retreino
        self.config = {
            "min_accuracy_threshold": 0.55,  # Retreinar se accuracy < 55%
            "min_data_samples": 20,          # 🔧 AJUSTADO: 100→20 (mais realista para volume atual)
            "performance_window_days": 7,    # Avaliar performance dos últimos 7 dias
            "auto_retrain_schedule": "daily", # daily, weekly, disabled
            "max_retrain_frequency": 1,      # Máximo 1 retreino por dia
            "validation_split": 0.2,         # 20% para validação
            "backup_models": True            # Manter backup dos modelos antigos
        }

        # Performance tracking
        self.performance_history = []
        self.last_retraining = {}

        # Modelos suportados
        self.supported_models = {
            "1x2_classifier": {
                "target_column": "result",
                "features": ["home_form", "away_form", "head_to_head", "home_goals_avg", "away_goals_avg"],
                "model_class": RandomForestClassifier,
                "params": {"n_estimators": 100, "random_state": 42}
            },
            "over_under_classifier": {
                "target_column": "total_goals_category",
                "features": ["avg_goals_home", "avg_goals_away", "league_avg_goals", "form_goals"],
                "model_class": GradientBoostingClassifier,
                "params": {"n_estimators": 100, "random_state": 42}
            },
            "btts_classifier": {
                "target_column": "both_teams_scored",
                "features": ["home_scoring_rate", "away_scoring_rate", "home_conceding_rate", "away_conceding_rate"],
                "model_class": RandomForestClassifier,
                "params": {"n_estimators": 100, "random_state": 42}
            }
        }

        # Inicializar agendamento
        self._setup_scheduled_retraining()

    def _setup_scheduled_retraining(self):
        """Configura o agendamento automático de retreino"""
        if self.config["auto_retrain_schedule"] == "daily":
            schedule.every().day.at("02:00").do(self._run_scheduled_retraining)
        elif self.config["auto_retrain_schedule"] == "weekly":
            schedule.every().sunday.at("02:00").do(self._run_scheduled_retraining)

        # Iniciar thread do scheduler
        scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()

    def _run_scheduler(self):
        """Executa o scheduler em background"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto

    async def evaluate_retraining_triggers(self) -> List[RetrainingTrigger]:
        """
        Avalia se algum modelo precisa ser retreinado
        """
        triggers = []

        for model_name in self.supported_models.keys():
            # 1. Verificar performance
            performance = await self._evaluate_model_performance(model_name)
            if performance and performance.accuracy < self.config["min_accuracy_threshold"]:
                triggers.append(RetrainingTrigger(
                    trigger_type="performance",
                    threshold_value=self.config["min_accuracy_threshold"],
                    current_value=performance.accuracy,
                    triggered_at=datetime.now(),
                    reason=f"Accuracy {performance.accuracy:.2%} abaixo do threshold {self.config['min_accuracy_threshold']:.2%}"
                ))

            # 2. Verificar volume de dados novos
            data_count = await self._count_new_training_data(model_name)
            if data_count >= self.config["min_data_samples"]:
                triggers.append(RetrainingTrigger(
                    trigger_type="data_volume",
                    threshold_value=self.config["min_data_samples"],
                    current_value=data_count,
                    triggered_at=datetime.now(),
                    reason=f"Novos dados disponíveis: {data_count} amostras"
                ))

        return triggers

    async def _evaluate_model_performance(self, model_name: str) -> Optional[ModelPerformance]:
        """
        Avalia a performance atual de um modelo
        """
        try:
            # Carregar dados de teste recentes
            test_data = await self._load_recent_test_data(model_name)
            if test_data.empty:
                return None

            # Carregar modelo
            model_path = self.models_dir / f"{model_name}.joblib"
            if not model_path.exists():
                logger.warning(f"Modelo {model_name} não encontrado em {model_path}")
                return None

            model = joblib.load(model_path)
            model_config = self.supported_models[model_name]

            # Preparar features
            X = test_data[model_config["features"]]
            y_true = test_data[model_config["target_column"]]

            # Fazer previsões
            y_pred = model.predict(X)

            # Calcular métricas
            accuracy = accuracy_score(y_true, y_pred)
            report = classification_report(y_true, y_pred, output_dict=True)

            # Determinar trend
            trend = self._calculate_performance_trend(model_name, accuracy)

            return ModelPerformance(
                model_name=model_name,
                accuracy=accuracy,
                precision=report['weighted avg']['precision'],
                recall=report['weighted avg']['recall'],
                f1_score=report['weighted avg']['f1-score'],
                samples_count=len(test_data),
                last_evaluation=datetime.now(),
                trend=trend
            )

        except Exception as e:
            logger.error(f"Erro ao avaliar performance do modelo {model_name}: {str(e)}")
            return None

    async def _load_recent_test_data(self, model_name: str) -> pd.DataFrame:
        """
        Carrega dados de teste recentes para avaliação
        """
        try:
            # Buscar dados dos últimos N dias
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.config["performance_window_days"])

            # Simular carregamento de dados (em produção, viria do banco)
            # Por agora, gerar dados simulados para teste
            np.random.seed(42)
            n_samples = 50

            data = {
                "home_form": np.random.uniform(0, 1, n_samples),
                "away_form": np.random.uniform(0, 1, n_samples),
                "head_to_head": np.random.uniform(0, 1, n_samples),
                "home_goals_avg": np.random.uniform(0.5, 3.0, n_samples),
                "away_goals_avg": np.random.uniform(0.5, 3.0, n_samples),
                "avg_goals_home": np.random.uniform(1.0, 3.0, n_samples),
                "avg_goals_away": np.random.uniform(1.0, 3.0, n_samples),
                "league_avg_goals": np.random.uniform(2.0, 3.5, n_samples),
                "form_goals": np.random.uniform(1.0, 4.0, n_samples),
                "home_scoring_rate": np.random.uniform(0.3, 0.9, n_samples),
                "away_scoring_rate": np.random.uniform(0.3, 0.9, n_samples),
                "home_conceding_rate": np.random.uniform(0.1, 0.7, n_samples),
                "away_conceding_rate": np.random.uniform(0.1, 0.7, n_samples)
            }

            # Gerar targets baseados nas features (simulação)
            if model_name == "1x2_classifier":
                data["result"] = np.random.choice([0, 1, 2], n_samples)  # 0: Away, 1: Draw, 2: Home
            elif model_name == "over_under_classifier":
                data["total_goals_category"] = np.random.choice([0, 1], n_samples)  # 0: Under, 1: Over
            elif model_name == "btts_classifier":
                data["both_teams_scored"] = np.random.choice([0, 1], n_samples)  # 0: No, 1: Yes

            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Erro ao carregar dados de teste para {model_name}: {str(e)}")
            return pd.DataFrame()

    async def _count_new_training_data(self, model_name: str) -> int:
        """
        Conta quantos novos dados de treino estão disponíveis
        """
        try:
            # Verificar quando foi o último retreino
            last_retrain_file = self.retraining_data_dir / f"{model_name}_last_retrain.json"

            if last_retrain_file.exists():
                with open(last_retrain_file, 'r') as f:
                    last_retrain_data = json.load(f)
                    last_retrain_date = datetime.fromisoformat(last_retrain_data['timestamp'])
            else:
                last_retrain_date = datetime.now() - timedelta(days=30)  # 30 dias atrás por padrão

            # Simular contagem de novos dados
            # Em produção, isso seria uma query no banco de dados
            days_since_retrain = (datetime.now() - last_retrain_date).days
            new_data_count = min(days_since_retrain * 10, 500)  # Máximo 500 amostras

            return new_data_count

        except Exception as e:
            logger.error(f"Erro ao contar novos dados para {model_name}: {str(e)}")
            return 0

    def _calculate_performance_trend(self, model_name: str, current_accuracy: float) -> str:
        """
        Calcula a tendência de performance do modelo
        """
        # Buscar histórico de performance
        history_file = self.performance_log_dir / f"{model_name}_performance_history.json"

        if not history_file.exists():
            return "stable"

        try:
            with open(history_file, 'r') as f:
                history = json.load(f)

            if len(history) < 2:
                return "stable"

            # Comparar com as últimas 3 avaliações
            recent_accuracies = [entry['accuracy'] for entry in history[-3:]]
            recent_accuracies.append(current_accuracy)

            # Calcular tendência
            if len(recent_accuracies) >= 3:
                avg_change = np.mean(np.diff(recent_accuracies))
                if avg_change > 0.01:  # Melhorando > 1%
                    return "improving"
                elif avg_change < -0.01:  # Piorando > 1%
                    return "degrading"

            return "stable"

        except Exception as e:
            logger.error(f"Erro ao calcular tendência para {model_name}: {str(e)}")
            return "stable"

    async def retrain_model(self, model_name: str, trigger: RetrainingTrigger) -> RetrainingResult:
        """
        Executa o retreino de um modelo específico
        """
        start_time = time.time()
        logger.info(f"Iniciando retreino do modelo {model_name}. Razão: {trigger.reason}")

        try:
            # 1. Verificar se já foi retreinado recentemente
            if not self._can_retrain_now(model_name):
                return RetrainingResult(
                    success=False,
                    model_name=model_name,
                    old_accuracy=0,
                    new_accuracy=0,
                    improvement=0,
                    training_samples=0,
                    training_duration=0,
                    model_path="",
                    validation_report={},
                    timestamp=datetime.now()
                )

            # 2. Carregar dados de treino
            training_data = await self._load_training_data(model_name)
            if training_data.empty:
                raise Exception("Nenhum dado de treino disponível")

            # 3. Preparar dados
            model_config = self.supported_models[model_name]
            X = training_data[model_config["features"]]
            y = training_data[model_config["target_column"]]

            # 4. Split treino/validação
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=self.config["validation_split"], random_state=42
            )

            # 5. Backup do modelo atual (se existir)
            old_accuracy = 0
            old_model_path = self.models_dir / f"{model_name}.joblib"
            if old_model_path.exists():
                old_accuracy = await self._get_model_accuracy(model_name)
                if self.config["backup_models"]:
                    backup_path = self.models_dir / f"{model_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
                    joblib.dump(joblib.load(old_model_path), backup_path)

            # 6. Treinar novo modelo
            new_model = model_config["model_class"](**model_config["params"])
            new_model.fit(X_train, y_train)

            # 7. Validar
            y_pred = new_model.predict(X_val)
            new_accuracy = accuracy_score(y_val, y_pred)
            validation_report = classification_report(y_val, y_pred, output_dict=True)

            # 8. Decidir se aceitar o novo modelo
            improvement = new_accuracy - old_accuracy
            if improvement >= -0.02:  # Aceitar se não piorar mais que 2%
                # Salvar novo modelo
                new_model_path = self.models_dir / f"{model_name}.joblib"
                joblib.dump(new_model, new_model_path)

                # Atualizar log de retreino
                await self._update_retraining_log(model_name, trigger, new_accuracy)

                # Atualizar histórico de performance
                await self._update_performance_history(model_name, new_accuracy, validation_report)

                training_duration = time.time() - start_time

                logger.info(f"Retreino do modelo {model_name} concluído com sucesso. "
                           f"Accuracy: {old_accuracy:.2%} → {new_accuracy:.2%} "
                           f"(+{improvement:.2%})")

                return RetrainingResult(
                    success=True,
                    model_name=model_name,
                    old_accuracy=old_accuracy,
                    new_accuracy=new_accuracy,
                    improvement=improvement,
                    training_samples=len(training_data),
                    training_duration=training_duration,
                    model_path=str(new_model_path),
                    validation_report=validation_report,
                    timestamp=datetime.now()
                )
            else:
                logger.warning(f"Novo modelo para {model_name} rejeitado. "
                              f"Performance piorou significativamente: {improvement:.2%}")

                return RetrainingResult(
                    success=False,
                    model_name=model_name,
                    old_accuracy=old_accuracy,
                    new_accuracy=new_accuracy,
                    improvement=improvement,
                    training_samples=len(training_data),
                    training_duration=time.time() - start_time,
                    model_path="",
                    validation_report=validation_report,
                    timestamp=datetime.now()
                )

        except Exception as e:
            logger.error(f"Erro durante retreino do modelo {model_name}: {str(e)}")
            return RetrainingResult(
                success=False,
                model_name=model_name,
                old_accuracy=0,
                new_accuracy=0,
                improvement=0,
                training_samples=0,
                training_duration=time.time() - start_time,
                model_path="",
                validation_report={},
                timestamp=datetime.now()
            )

    async def _load_training_data(self, model_name: str) -> pd.DataFrame:
        """
        Carrega dados de treino REAIS para o modelo (do banco de dados)
        """
        try:
            from app.core.database import SessionLocal
            from app.models import Prediction, Match, TeamStatistics
            from sqlalchemy.orm import joinedload

            db = SessionLocal()

            # 🔥 BUSCAR PREDICTIONS COM RESULTADOS REAIS (is_winner != None)
            predictions = db.query(Prediction).join(Match).filter(
                Prediction.is_winner.isnot(None)  # Apenas predictions com resultado
            ).options(
                joinedload(Prediction.match)
            ).all()

            db.close()

            logger.info(f"📊 Encontradas {len(predictions)} predictions com resultados reais")

            if len(predictions) < self.config["min_data_samples"]:
                logger.warning(f"⚠️ Apenas {len(predictions)} amostras (mínimo: {self.config['min_data_samples']})")
                return pd.DataFrame()  # Retorna vazio se não tiver dados suficientes

            # Construir dataset a partir das predictions reais
            data_rows = []

            for pred in predictions:
                try:
                    match = pred.match

                    # Extrair features do key_factors (JSON)
                    key_factors = pred.key_factors if pred.key_factors else {}

                    # Features básicas (com fallback para valores default)
                    row = {
                        # Features genéricas
                        "home_form": key_factors.get('home_form', 0.5),
                        "away_form": key_factors.get('away_form', 0.5),
                        "head_to_head": key_factors.get('h2h_factor', 0.5),
                        "home_goals_avg": key_factors.get('lambda_home', 1.5),
                        "away_goals_avg": key_factors.get('lambda_away', 1.3),

                        # Features para Over/Under
                        "avg_goals_home": key_factors.get('lambda_home', 1.5),
                        "avg_goals_away": key_factors.get('lambda_away', 1.3),
                        "league_avg_goals": 2.7,
                        "form_goals": (key_factors.get('lambda_home', 1.5) + key_factors.get('lambda_away', 1.3)),

                        # Features para BTTS
                        "home_scoring_rate": min(key_factors.get('lambda_home', 1.5) / 3.0, 0.9),
                        "away_scoring_rate": min(key_factors.get('lambda_away', 1.3) / 3.0, 0.9),
                        "home_conceding_rate": 0.5,
                        "away_conceding_rate": 0.5,
                    }

                    # Target baseado no tipo de modelo
                    if model_name == "1x2_classifier":
                        # Target: 0=Away, 1=Draw, 2=Home
                        if pred.market_type == "1X2" or pred.market_type.startswith("HOME_") or pred.market_type.startswith("AWAY_") or pred.market_type == "DRAW":
                            if "HOME" in pred.predicted_outcome or pred.predicted_outcome == "1":
                                row["result"] = 2 if pred.is_winner else (1 if "DRAW" in str(match.status) else 0)
                            elif "AWAY" in pred.predicted_outcome or pred.predicted_outcome == "2":
                                row["result"] = 0 if pred.is_winner else (1 if "DRAW" in str(match.status) else 2)
                            elif "DRAW" in pred.predicted_outcome or pred.predicted_outcome == "X":
                                row["result"] = 1 if pred.is_winner else (2 if match.home_score > match.away_score else 0)
                            else:
                                continue  # Skip se não conseguir determinar
                        else:
                            continue  # Skip se não for mercado 1X2

                    elif model_name == "over_under_classifier":
                        # Target: 0=Under, 1=Over
                        if "OVER" in pred.market_type or "UNDER" in pred.market_type:
                            is_over = "OVER" in pred.predicted_outcome
                            row["total_goals_category"] = 1 if (is_over and pred.is_winner) else 0
                        else:
                            continue  # Skip se não for mercado O/U

                    elif model_name == "btts_classifier":
                        # Target: 0=No, 1=Yes
                        if "BTTS" in pred.market_type:
                            is_yes = "YES" in pred.predicted_outcome
                            row["both_teams_scored"] = 1 if (is_yes and pred.is_winner) else 0
                        else:
                            continue  # Skip se não for mercado BTTS

                    data_rows.append(row)

                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar prediction {pred.id}: {str(e)}")
                    continue

            if not data_rows:
                logger.warning(f"⚠️ Nenhuma row válida após processamento")
                return pd.DataFrame()

            df = pd.DataFrame(data_rows)
            logger.info(f"✅ Dataset criado: {len(df)} amostras de dados REAIS")

            return df

        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados de treino para {model_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _can_retrain_now(self, model_name: str) -> bool:
        """
        Verifica se o modelo pode ser retreinado agora
        """
        try:
            last_retrain_file = self.retraining_data_dir / f"{model_name}_last_retrain.json"

            if not last_retrain_file.exists():
                return True

            with open(last_retrain_file, 'r') as f:
                last_retrain_data = json.load(f)
                last_retrain_date = datetime.fromisoformat(last_retrain_data['timestamp'])

            # Verificar se passou o tempo mínimo entre retreinos
            time_since_last = datetime.now() - last_retrain_date
            min_interval = timedelta(days=1 / self.config["max_retrain_frequency"])

            return time_since_last >= min_interval

        except Exception as e:
            logger.error(f"Erro ao verificar se pode retreinar {model_name}: {str(e)}")
            return True

    async def _get_model_accuracy(self, model_name: str) -> float:
        """
        Obtém a accuracy atual do modelo
        """
        try:
            performance = await self._evaluate_model_performance(model_name)
            return performance.accuracy if performance else 0
        except:
            return 0

    async def _update_retraining_log(self, model_name: str, trigger: RetrainingTrigger, new_accuracy: float):
        """
        Atualiza o log de retreino
        """
        try:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "trigger_type": trigger.trigger_type,
                "trigger_reason": trigger.reason,
                "new_accuracy": new_accuracy
            }

            log_file = self.retraining_data_dir / f"{model_name}_last_retrain.json"
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)

        except Exception as e:
            logger.error(f"Erro ao atualizar log de retreino para {model_name}: {str(e)}")

    async def _update_performance_history(self, model_name: str, accuracy: float, report: Dict[str, Any]):
        """
        Atualiza o histórico de performance
        """
        try:
            history_file = self.performance_log_dir / f"{model_name}_performance_history.json"

            # Carregar histórico existente
            history = []
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)

            # Adicionar nova entrada
            new_entry = {
                "timestamp": datetime.now().isoformat(),
                "accuracy": accuracy,
                "precision": report['weighted avg']['precision'],
                "recall": report['weighted avg']['recall'],
                "f1_score": report['weighted avg']['f1-score']
            }

            history.append(new_entry)

            # Manter apenas os últimos 100 registros
            if len(history) > 100:
                history = history[-100:]

            # Salvar
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logger.error(f"Erro ao atualizar histórico de performance para {model_name}: {str(e)}")

    def _run_scheduled_retraining(self):
        """
        Executa retreino agendado (chamado pelo scheduler)
        """
        logger.info("Executando retreino agendado...")

        # Executar em thread separada para não bloquear
        async def run_async_retraining():
            triggers = await self.evaluate_retraining_triggers()
            if triggers:
                results = await self.run_bulk_retraining()
                logger.info(f"Retreino agendado concluído. {len(results)} modelos processados.")
            else:
                logger.info("Nenhum modelo precisa de retreino no momento.")

        # Executar de forma assíncrona
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_async_retraining())
        loop.close()

    async def run_bulk_retraining(self) -> List[RetrainingResult]:
        """
        Executa retreino em massa para todos os modelos que precisam
        """
        triggers = await self.evaluate_retraining_triggers()
        results = []

        # Agrupar triggers por modelo
        model_triggers = {}
        for trigger in triggers:
            # Assumir que todos os triggers se aplicam a todos os modelos por simplicidade
            for model_name in self.supported_models.keys():
                if model_name not in model_triggers:
                    model_triggers[model_name] = []
                model_triggers[model_name].append(trigger)

        # Executar retreino para cada modelo
        for model_name, model_trigger_list in model_triggers.items():
            # Usar o primeiro trigger (mais crítico)
            primary_trigger = model_trigger_list[0]
            result = await self.retrain_model(model_name, primary_trigger)
            results.append(result)

        return results

    async def get_retraining_status(self) -> Dict[str, Any]:
        """
        Retorna status atual do sistema de retreino
        """
        try:
            status = {
                "system_active": True,
                "config": self.config,
                "models": {},
                "pending_triggers": [],
                "last_retraining": {},
                "next_scheduled": None
            }

            # Status de cada modelo
            for model_name in self.supported_models.keys():
                performance = await self._evaluate_model_performance(model_name)
                new_data_count = await self._count_new_training_data(model_name)

                status["models"][model_name] = {
                    "current_performance": performance.__dict__ if performance else None,
                    "new_data_samples": new_data_count,
                    "needs_retraining": (
                        (performance and performance.accuracy < self.config["min_accuracy_threshold"]) or
                        new_data_count >= self.config["min_data_samples"]
                    )
                }

            # Triggers pendentes
            triggers = await self.evaluate_retraining_triggers()
            status["pending_triggers"] = [
                {
                    "type": t.trigger_type,
                    "reason": t.reason,
                    "current_value": t.current_value,
                    "threshold": t.threshold_value
                }
                for t in triggers
            ]

            # Próximo agendamento
            if self.config["auto_retrain_schedule"] != "disabled":
                # Simular próximo agendamento
                next_run = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0)
                if next_run <= datetime.now():
                    next_run += timedelta(days=1)
                status["next_scheduled"] = next_run.isoformat()

            return status

        except Exception as e:
            logger.error(f"Erro ao obter status de retreino: {str(e)}")
            return {"error": str(e)}

# Instância global do serviço
automated_ml_retraining = AutomatedMLRetraining()