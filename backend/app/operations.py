from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.security import require_operations_api_key
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.operations_service import (
    OperationsService,
)


router = APIRouter(
    prefix="/api/v1/operations",
    tags=["Operations"],
    dependencies=[Depends(require_operations_api_key)],
)


def get_operations_service(
    db: Session = Depends(get_db),
) -> OperationsService:

    return OperationsService(db)


# =========================================================
# PHASE 12 — SYSTEM MONITORING
# =========================================================

@router.get("/metrics")
def operations_metrics(
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    """
    System-level revenue recovery metrics.

    Read-only endpoint. No AI, payment, webhook,
    reconciliation, or communication execution occurs.
    """

    return service.metrics()


# =========================================================
# EXISTING SUMMARY
# =========================================================

@router.get("/summary")
def operations_summary(
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    return service.summary()


# =========================================================
# RECOVERY CASES
# =========================================================

@router.get("/recovery-cases")
def recovery_cases(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    return service.list_recovery_cases(
        limit=limit,
        offset=offset,
    )


@router.get("/recovery-cases/{case_id}")
def recovery_case(
    case_id: int,
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    result = service.get_recovery_case(
        case_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recovery case not found.",
        )

    return result


# =========================================================
# RECOVERY ACTIONS
# =========================================================

@router.get("/recovery-actions/{action_id}")
def recovery_action(
    action_id: int,
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    result = service.get_recovery_action(
        action_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recovery action not found.",
        )

    return result


# =========================================================
# WEBHOOKS
# =========================================================

@router.get("/webhooks")
def webhooks(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    return service.list_webhooks(
        limit=limit,
        offset=offset,
    )


# =========================================================
# AUDIT LOGS
# =========================================================

@router.get("/audit-logs")
def audit_logs(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    return service.list_audit_logs(
        limit=limit,
        offset=offset,
    )


# =========================================================
# COMMUNICATIONS
# =========================================================

@router.get("/communications")
def communications(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    return service.list_communications(
        limit=limit,
        offset=offset,
    )