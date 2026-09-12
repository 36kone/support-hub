from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.shared.dependencies.get_client_ip import get_client_ip

limiter = Limiter(key_func=get_client_ip)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    client_ip = get_client_ip(request)
    response = JSONResponse(
        {"error": f"Rate limit exceeded: {exc.detail} for {client_ip}"},
        status_code=429,
    )
    # Tenta injetar headers se o estado estiver disponível, senão retorna resposta simples
    try:
        if hasattr(request.state, "view_rate_limit"):
            return request.app.state.limiter._inject_headers(
                response, request.state.view_rate_limit
            )
    except Exception:
        pass
    return response
