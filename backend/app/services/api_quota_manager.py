"""
📊 API QUOTA MANAGER
Gerenciador inteligente de quota da API-Football
Controla e otimiza o uso de requests diários
"""

from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional, Dict
import logging

from app.models.api_tracking import DailyAPIQuota, APIRequestLog

logger = logging.getLogger(__name__)

class APIQuotaManager:
    """Gerenciador de quota da API com controle inteligente"""

    def __init__(self, db: Session, daily_limit: int = 7500):
        self.db = db
        self.daily_limit = daily_limit

    def get_today_quota(self) -> DailyAPIQuota:
        """Obter quota do dia atual"""
        today = date.today().isoformat()

        quota = self.db.query(DailyAPIQuota).filter(
            DailyAPIQuota.date == today
        ).first()

        if not quota:
            # Criar quota do dia
            quota = DailyAPIQuota(
                date=today,
                daily_limit=self.daily_limit,
                requests_used=0,
                requests_remaining=self.daily_limit
            )
            self.db.add(quota)
            self.db.commit()
            self.db.refresh(quota)

        return quota

    def can_make_request(self, requests_needed: int = 1) -> bool:
        """
        Verificar se pode fazer N requests

        Args:
            requests_needed: Número de requests necessários

        Returns:
            True se houver quota disponível
        """
        quota = self.get_today_quota()
        return quota.requests_remaining >= requests_needed

    def get_available_requests(self) -> int:
        """Obter número de requests disponíveis hoje"""
        quota = self.get_today_quota()
        return quota.requests_remaining

    def record_request(
        self,
        endpoint: str,
        success: bool = True,
        results_count: int = 0,
        http_status: int = 200,
        response_time_ms: float = 0,
        error_message: Optional[str] = None,
        params: Optional[Dict] = None
    ) -> APIRequestLog:
        """
        Registrar uma requisição à API

        Args:
            endpoint: Nome do endpoint
            success: Se foi bem-sucedida
            results_count: Quantidade de resultados
            http_status: Status HTTP
            response_time_ms: Tempo de resposta
            error_message: Mensagem de erro (se houver)
            params: Parâmetros da requisição

        Returns:
            Log da requisição
        """
        # Criar log
        log = APIRequestLog(
            endpoint=endpoint,
            params=params,
            http_status=http_status,
            success=success,
            results_count=results_count,
            error_message=error_message,
            response_time_ms=response_time_ms
        )

        self.db.add(log)

        # Atualizar quota
        if success and http_status == 200:
            quota = self.get_today_quota()
            quota.requests_used += 1
            quota.requests_remaining = max(0, quota.daily_limit - quota.requests_used)

            # Atualizar contador por tipo de endpoint
            if 'fixtures' in endpoint:
                quota.fixtures_requests += 1
            elif 'statistics' in endpoint:
                quota.statistics_requests += 1
            elif 'standings' in endpoint:
                quota.standings_requests += 1
            else:
                quota.other_requests += 1

            quota.last_updated = datetime.now()

        self.db.commit()
        return log

    def get_usage_stats(self) -> Dict:
        """Obter estatísticas de uso do dia"""
        quota = self.get_today_quota()

        return {
            'date': quota.date,
            'daily_limit': quota.daily_limit,
            'requests_used': quota.requests_used,
            'requests_remaining': quota.requests_remaining,
            'usage_percentage': (quota.requests_used / quota.daily_limit * 100) if quota.daily_limit > 0 else 0,
            'breakdown': {
                'fixtures': quota.fixtures_requests,
                'statistics': quota.statistics_requests,
                'standings': quota.standings_requests,
                'other': quota.other_requests
            }
        }

    def get_optimal_batch_size(self, target_requests: int) -> int:
        """
        Calcular tamanho ótimo de batch baseado na quota disponível

        Args:
            target_requests: Número total de requests desejados

        Returns:
            Tamanho ótimo do batch
        """
        available = self.get_available_requests()

        # Reservar 10% para requests emergenciais
        safe_available = int(available * 0.9)

        # Se temos quota suficiente, retornar o alvo
        if safe_available >= target_requests:
            return target_requests

        # Senão, retornar o máximo disponível
        return safe_available

    def estimate_completion_time(self, requests_needed: int, delay_per_request: float = 0.5) -> float:
        """
        Estimar tempo de conclusão em segundos

        Args:
            requests_needed: Número de requests necessários
            delay_per_request: Delay entre requests (segundos)

        Returns:
            Tempo estimado em segundos
        """
        return requests_needed * delay_per_request

    def should_throttle(self) -> bool:
        """
        Verificar se deve fazer throttling (limitar velocidade)

        Returns:
            True se deve reduzir velocidade
        """
        stats = self.get_usage_stats()
        usage_percentage = stats['usage_percentage']

        # Se usou mais de 80% da quota, fazer throttling
        return usage_percentage > 80

    def get_recommended_delay(self) -> float:
        """
        Obter delay recomendado entre requests baseado no uso

        Returns:
            Delay em segundos
        """
        stats = self.get_usage_stats()
        usage_percentage = stats['usage_percentage']

        if usage_percentage > 90:
            return 2.0  # Muito uso, delay alto
        elif usage_percentage > 80:
            return 1.0  # Uso alto, delay médio
        elif usage_percentage > 60:
            return 0.5  # Uso moderado, delay normal
        else:
            return 0.3  # Uso baixo, delay mínimo

    def check_health(self) -> Dict:
        """
        Verificar saúde do sistema de quota

        Returns:
            Status de saúde
        """
        stats = self.get_usage_stats()
        available = stats['requests_remaining']
        usage_pct = stats['usage_percentage']

        if available < 100:
            status = "CRITICAL"
            message = f"Quota crítica! Apenas {available} requests restantes"
        elif usage_pct > 90:
            status = "WARNING"
            message = f"Alto uso de quota: {usage_pct:.1f}%"
        elif usage_pct > 70:
            status = "CAUTION"
            message = f"Uso moderado: {usage_pct:.1f}%"
        else:
            status = "HEALTHY"
            message = f"Quota saudável: {available} requests disponíveis"

        return {
            'status': status,
            'message': message,
            'available_requests': available,
            'usage_percentage': usage_pct,
            'recommended_action': self._get_recommended_action(status)
        }

    def _get_recommended_action(self, status: str) -> str:
        """Obter ação recomendada baseada no status"""
        actions = {
            'CRITICAL': 'Parar coletas não essenciais. Apenas atualizações de jogos ao vivo.',
            'WARNING': 'Reduzir velocidade de coleta. Priorizar dados críticos.',
            'CAUTION': 'Monitorar uso. Continuar com cautela.',
            'HEALTHY': 'Operação normal. Sem restrições.'
        }
        return actions.get(status, 'Monitorar')
