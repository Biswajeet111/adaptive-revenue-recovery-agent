import sys

from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.webhook_event import WebhookEvent
from backend.app.services.webhook_service import WebhookService


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: "
            "python -m backend.app.scripts.replay_webhook_event "
            "<event_id>"
        )
        raise SystemExit(1)

    event_id = sys.argv[1]

    db = SessionLocal()

    try:
        event = db.scalar(
            select(WebhookEvent).where(
                WebhookEvent.event_id == event_id
            )
        )

        if event is None:
            raise ValueError(
                f"Webhook event {event_id} not found."
            )

        print(
            "=== WEBHOOK REPLAY ==="
        )
        print(
            f"Event ID: {event.event_id}"
        )
        print(
            f"Event type: {event.event_type}"
        )
        print(
            f"Previously processed: "
            f"{event.processed}"
        )

        service = WebhookService(db)

        if event.event_type in {
            "payment.failed",
            "payment.authorized",
            "payment.captured",
        }:
            service.process_payment_event(event)

        elif event.event_type in {
            "payment_link.paid",
            "payment_link.partially_paid",
            "payment_link.expired",
            "payment_link.cancelled",
        }:
            service.process_payment_link_event(event)

        elif event.event_type == "order.paid":
            event.processed = True

        else:
            raise ValueError(
                f"Unsupported replay event type: "
                f"{event.event_type}"
            )

        db.commit()

        print()
        print(
            "WEBHOOK REPLAY COMPLETED."
        )
        print(
            f"Event processed: {event.processed}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()