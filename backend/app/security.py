import secrets

from fastapi import Header, HTTPException

from backend.app.config import settings


def require_operations_api_key(
    x_operations_api_key: str | None = Header(
        default=None,
        alias="X-Operations-API-Key",
    ),
) -> None:
    """
    Protect internal operations endpoints with a shared API key.

    The application fails closed when the key is not configured.
    """
    if not settings.operations_api_key:
        raise HTTPException(
            status_code=503,
            detail="Operations API authentication is not configured.",
        )

    if not x_operations_api_key:
        raise HTTPException(
            status_code=401,
            detail="Operations API key is required.",
        )

    if not secrets.compare_digest(
        x_operations_api_key,
        settings.operations_api_key,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Operations API key.",
        )