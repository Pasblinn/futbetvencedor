"""
🔄 RETRY BACKOFF SYSTEM - Advanced Retry Strategy with Exponential Backoff
Implements intelligent retry logic with jitter, circuit breaker pattern,
and adaptive delay strategies for handling rate limits and temporary failures.
"""

import asyncio
import random
import time
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class RetryReason(Enum):
    """Reasons for retry"""
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"  # 5xx
    RATE_LIMITED = "rate_limited"  # 429
    FORBIDDEN = "forbidden"  # 403
    TIMEOUT = "timeout"
    PROXY_ERROR = "proxy_error"
    UNKNOWN = "unknown"

@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    reason: RetryReason
    delay: float
    timestamp: datetime
    status_code: Optional[int] = None
    error_message: Optional[str] = None

class RetryStats:
    """Statistics for retry attempts"""
    def __init__(self):
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.retry_reasons: Dict[RetryReason, int] = {}
        self.total_delay_time = 0.0
        self.max_attempts_reached = 0

    def add_attempt(self, attempt: RetryAttempt, success: bool = False):
        """Add retry attempt to stats"""
        self.total_attempts += 1
        self.total_delay_time += attempt.delay

        if success:
            self.successful_attempts += 1
        else:
            self.failed_attempts += 1

        self.retry_reasons[attempt.reason] = self.retry_reasons.get(attempt.reason, 0) + 1

    def get_success_rate(self) -> float:
        """Get success rate after retries"""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_attempts / self.total_attempts

class ExponentialBackoff:
    """
    🎯 Exponential Backoff with Jitter
    Implements multiple backoff strategies:
    - Standard exponential backoff
    - Full jitter
    - Equal jitter
    - Decorrelated jitter
    - Linear backoff
    """

    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter_type: str = "full",
        max_attempts: int = 3
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter_type = jitter_type
        self.max_attempts = max_attempts

    def calculate_delay(self, attempt: int, base_delay: Optional[float] = None) -> float:
        """Calculate delay for specific attempt number"""
        if base_delay is None:
            base_delay = self.initial_delay

        # Calculate exponential delay
        exponential_delay = min(base_delay * (self.multiplier ** (attempt - 1)), self.max_delay)

        # Apply jitter strategy
        if self.jitter_type == "none":
            return exponential_delay
        elif self.jitter_type == "full":
            # Full jitter: delay = random(0, exponential_delay)
            return random.uniform(0, exponential_delay)
        elif self.jitter_type == "equal":
            # Equal jitter: delay = exponential_delay/2 + random(0, exponential_delay/2)
            half_delay = exponential_delay / 2
            return half_delay + random.uniform(0, half_delay)
        elif self.jitter_type == "decorrelated":
            # Decorrelated jitter: delay = random(base_delay, delay * 3)
            return random.uniform(base_delay, exponential_delay * 3)
        else:
            # Default to full jitter
            return random.uniform(0, exponential_delay)

class CircuitBreaker:
    """
    🔌 Circuit Breaker Pattern
    Prevents cascading failures by temporarily stopping requests
    when failure rate exceeds threshold
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_duration: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            # Check if timeout has passed
            if (datetime.now() - self.last_failure_time).seconds >= self.timeout_duration:
                self.state = "half_open"
                self.success_count = 0
                return True
            return False
        elif self.state == "half_open":
            return True

        return False

    def record_success(self):
        """Record successful request"""
        if self.state == "half_open":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "closed"
                self.failure_count = 0
        elif self.state == "closed":
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == "closed" and self.failure_count >= self.failure_threshold:
            self.state = "open"
        elif self.state == "half_open":
            self.state = "open"

class RetryBackoffManager:
    """
    🔄 Advanced Retry Manager
    Coordinates retry attempts with multiple strategies and circuit breaking
    """

    def __init__(self):
        self.backoff = ExponentialBackoff()
        self.circuit_breaker = CircuitBreaker()
        self.stats = RetryStats()
        self.domain_stats: Dict[str, RetryStats] = {}

    def configure_backoff(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter_type: str = "full",
        max_attempts: int = 3
    ):
        """Configure backoff parameters"""
        self.backoff = ExponentialBackoff(
            initial_delay=initial_delay,
            max_delay=max_delay,
            multiplier=multiplier,
            jitter_type=jitter_type,
            max_attempts=max_attempts
        )

    def configure_circuit_breaker(
        self,
        failure_threshold: int = 5,
        timeout_duration: int = 60,
        success_threshold: int = 2
    ):
        """Configure circuit breaker parameters"""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout_duration=timeout_duration,
            success_threshold=success_threshold
        )

    def get_retry_reason(self, status_code: int, exception: Exception = None) -> RetryReason:
        """Determine retry reason from status code and exception"""
        if status_code == 429:
            return RetryReason.RATE_LIMITED
        elif status_code == 403:
            return RetryReason.FORBIDDEN
        elif 500 <= status_code < 600:
            return RetryReason.SERVER_ERROR
        elif exception:
            error_msg = str(exception).lower()
            if 'timeout' in error_msg:
                return RetryReason.TIMEOUT
            elif 'proxy' in error_msg:
                return RetryReason.PROXY_ERROR
            elif any(keyword in error_msg for keyword in ['connection', 'network', 'dns']):
                return RetryReason.NETWORK_ERROR

        return RetryReason.UNKNOWN

    def should_retry(self, attempt: int, status_code: int, exception: Exception = None) -> bool:
        """Determine if request should be retried"""
        if attempt >= self.backoff.max_attempts:
            return False

        if not self.circuit_breaker.can_execute():
            return False

        retry_reason = self.get_retry_reason(status_code, exception)

        # Don't retry certain errors
        if status_code in [400, 401, 404, 410]:  # Client errors that won't change
            return False

        # Retry network errors, server errors, rate limits, timeouts
        return retry_reason in [
            RetryReason.NETWORK_ERROR,
            RetryReason.SERVER_ERROR,
            RetryReason.RATE_LIMITED,
            RetryReason.TIMEOUT,
            RetryReason.PROXY_ERROR
        ]

    def calculate_delay(self, attempt: int, status_code: int, exception: Exception = None) -> float:
        """Calculate delay for retry attempt"""
        retry_reason = self.get_retry_reason(status_code, exception)

        # Different base delays for different reasons
        base_delays = {
            RetryReason.RATE_LIMITED: 30.0,  # Longer delay for rate limits
            RetryReason.FORBIDDEN: 60.0,     # Even longer for forbidden
            RetryReason.SERVER_ERROR: 5.0,   # Medium delay for server errors
            RetryReason.NETWORK_ERROR: 2.0,  # Shorter delay for network issues
            RetryReason.TIMEOUT: 10.0,       # Medium delay for timeouts
            RetryReason.PROXY_ERROR: 3.0,    # Short delay for proxy issues
        }

        base_delay = base_delays.get(retry_reason, self.backoff.initial_delay)
        return self.backoff.calculate_delay(attempt, base_delay)

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        domain: str = "default",
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""
        if domain not in self.domain_stats:
            self.domain_stats[domain] = RetryStats()

        domain_stats = self.domain_stats[domain]

        for attempt in range(1, self.backoff.max_attempts + 1):
            try:
                if not self.circuit_breaker.can_execute():
                    raise Exception("Circuit breaker is open")

                result = await func(*args, **kwargs)

                # Success
                self.circuit_breaker.record_success()
                if attempt > 1:
                    logger.info(f"Request succeeded on attempt {attempt} for {domain}")

                return result

            except Exception as e:
                status_code = getattr(e, 'status_code', 500)
                retry_reason = self.get_retry_reason(status_code, e)

                # Record attempt
                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    reason=retry_reason,
                    delay=0.0,
                    timestamp=datetime.now(),
                    status_code=status_code,
                    error_message=str(e)
                )

                should_retry = self.should_retry(attempt, status_code, e)

                if should_retry and attempt < self.backoff.max_attempts:
                    delay = self.calculate_delay(attempt, status_code, e)
                    attempt_info.delay = delay

                    logger.warning(
                        f"Request failed on attempt {attempt} for {domain}. "
                        f"Retrying in {delay:.2f}s. Reason: {retry_reason.value}"
                    )

                    # Record failure for circuit breaker
                    self.circuit_breaker.record_failure()

                    # Wait before retry
                    await asyncio.sleep(delay)

                    # Update stats
                    domain_stats.add_attempt(attempt_info, success=False)
                    self.stats.add_attempt(attempt_info, success=False)

                else:
                    # Final failure
                    logger.error(
                        f"Request failed permanently after {attempt} attempts for {domain}. "
                        f"Final reason: {retry_reason.value}"
                    )

                    domain_stats.add_attempt(attempt_info, success=False)
                    self.stats.add_attempt(attempt_info, success=False)

                    if attempt >= self.backoff.max_attempts:
                        domain_stats.max_attempts_reached += 1
                        self.stats.max_attempts_reached += 1

                    raise e

        # This should not be reached
        raise Exception("Max retry attempts exceeded")

    def get_stats(self, domain: str = None) -> Dict:
        """Get retry statistics"""
        if domain and domain in self.domain_stats:
            stats = self.domain_stats[domain]
        else:
            stats = self.stats

        return {
            'total_attempts': stats.total_attempts,
            'successful_attempts': stats.successful_attempts,
            'failed_attempts': stats.failed_attempts,
            'success_rate': stats.get_success_rate(),
            'retry_reasons': {reason.value: count for reason, count in stats.retry_reasons.items()},
            'total_delay_time': stats.total_delay_time,
            'max_attempts_reached': stats.max_attempts_reached,
            'circuit_breaker_state': self.circuit_breaker.state,
            'circuit_breaker_failures': self.circuit_breaker.failure_count,
            'average_delay': stats.total_delay_time / max(stats.total_attempts, 1)
        }

    def reset_stats(self, domain: str = None):
        """Reset statistics"""
        if domain and domain in self.domain_stats:
            self.domain_stats[domain] = RetryStats()
        else:
            self.stats = RetryStats()
            self.domain_stats.clear()

# Global retry manager instance
retry_manager = RetryBackoffManager()