"""
⚡ Rate Limiting - Proteção contra abuso de API
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Configurar rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # 100 requests por minuto por IP
    storage_uri="memory://"  # Use Redis em produção: "redis://localhost:6379"
)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Handler customizado para erro de rate limit

    Args:
        request: FastAPI request
        exc: RateLimitExceeded exception

    Returns:
        JSON response com erro 429
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Rate limit exceeded. Please try again later.",
            "detail": str(exc.detail)
        }
    )
