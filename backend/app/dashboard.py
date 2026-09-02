from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.operations_service import OperationsService


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)


def get_operations_service(
    db: Session = Depends(get_db),
) -> OperationsService:
    return OperationsService(db)


@router.get("/overview")
def dashboard_overview(
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    """
    Read-only dashboard overview.

    Uses the existing OperationsService so dashboard
    metrics remain consistent with the internal operations API.
    """
    return service.metrics()


@router.get("/summary")
def dashboard_summary(
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    """
    Read-only operational summary for the dashboard.
    """
    return service.summary()


@router.get("/cases")
def dashboard_cases(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    """
    Return recovery cases for the dashboard.
    """
    return service.list_recovery_cases(
        limit=limit,
        offset=offset,
    )


@router.get("/cases/{case_id}")
def dashboard_case(
    case_id: int,
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    """
    Return one recovery case with its actions
    and communications.
    """
    result = service.get_recovery_case(case_id)

    if result is None:
        return {
            "error": "Recovery case not found.",
        }

    return result


@router.get("/webhooks")
def dashboard_webhooks(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    """
    Return recent Razorpay webhook activity.
    """
    return service.list_webhooks(
        limit=limit,
        offset=offset,
    )


@router.get("/communications")
def dashboard_communications(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: OperationsService = Depends(
        get_operations_service
    ),
):
    """
    Return recent recovery communications.
    """
    return service.list_communications(
        limit=limit,
        offset=offset,
    )