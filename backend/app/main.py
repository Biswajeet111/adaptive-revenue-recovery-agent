from decimal import Decimal
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.dashboard import router as dashboard_router
from backend.app.database import get_db
from backend.app.models.transaction import Transaction
from backend.app.operations import router as operations_router
from backend.app.services.razorpay_service import RazorpayService
from backend.app.webhooks.razorpay import router as razorpay_webhook_router


app = FastAPI(
    title="Adaptive Revenue Recovery Agent",
    description="AI-powered autonomous revenue recovery platform",
    version="0.1.0",
)


allowed_origins = [
    origin.strip()
    for origin in settings.cors_allowed_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(razorpay_webhook_router)
app.include_router(operations_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {
        "name": "Adaptive Revenue Recovery Agent",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/checkout", response_class=HTMLResponse)
def checkout_page():
    checkout_file = Path(__file__).parent / "templates" / "checkout.html"
    return checkout_file.read_text(encoding="utf-8")


@app.post("/api/v1/checkout/order")
def create_checkout_order(db: Session = Depends(get_db)):
    amount_paise = 10000

    razorpay_service = RazorpayService()

    order = razorpay_service.create_order(
        amount=amount_paise,
        currency="INR",
        receipt=f"rr-test-{amount_paise}",
    )

    transaction = Transaction(
        razorpay_order_id=order["id"],
        amount=Decimal(amount_paise) / Decimal(100),
        currency=order["currency"],
        status=order["status"],
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {
        "key_id": settings.razorpay_key_id,
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "transaction_id": transaction.id,
    }