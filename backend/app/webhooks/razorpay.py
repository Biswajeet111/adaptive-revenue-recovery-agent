import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services.signature_service import (
    verify_razorpay_signature,
)
from backend.app.services.webhook_service import WebhookService


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"],
)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(
        default=None,
        alias="X-Razorpay-Signature",
    ),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()

    if not raw_body:
        raise HTTPException(
            status_code=400,
            detail="Empty webhook body",
        )

    if not x_razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay webhook signature",
        )

    if not verify_razorpay_signature(
        raw_body,
        x_razorpay_signature,
        settings.razorpay_webhook_secret,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay webhook signature",
        )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

    event_type = payload.get("event")

    if not event_type:
        raise HTTPException(
            status_code=400,
            detail="Missing event type",
        )

    event_id = request.headers.get("X-Razorpay-Event-Id")

    if not event_id:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay event ID",
        )

    webhook_service = WebhookService(db)

    if webhook_service.event_exists(event_id):
        return {
            "success": True,
            "status": "duplicate_ignored",
            "event_id": event_id,
        }

    try:
        event = webhook_service.store_event(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            signature=x_razorpay_signature,
        )

        if event_type in {
            "payment.failed",
            "payment.authorized",
            "payment.captured",
        }:
            webhook_service.process_payment_event(event)

        db.commit()

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing failed: {exc}",
        )

    return {
        "success": True,
        "status": "processed",
        "event_id": event_id,
        "event": event_type,
    }