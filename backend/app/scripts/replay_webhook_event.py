from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.webhook_event import WebhookEvent
from backend.app.services.webhook_service import WebhookService


EVENT_ID = "TVFCDVc3LQ3HLz"


def main():
    db = SessionLocal()

    try:
        event = db.scalar(
            select(WebhookEvent).where(
                WebhookEvent.event_id == EVENT_ID
            )
        )

        if event is None:
            raise ValueError(
                f"Webhook event {EVENT_ID} not found."
            )

        print(
            f"Replaying webhook event: "
            f"{event.event_id}"
        )
        print(
            f"Event type: {event.event_type}"
        )

        service = WebhookService(db)

        # Replay only the payment-link event.
        # No AI decision is generated.
        # No new Razorpay payment is created.

        service.process_payment_link_event(
            event
        )

        db.commit()

        print()
        print("WEBHOOK REPLAY COMPLETED.")
        print(
            f"Event processed: "
            f"{event.processed}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()