from backend.app.database import SessionLocal
from backend.app.models.webhook_event import WebhookEvent
from backend.app.services.webhook_service import WebhookService


def main():
    db = SessionLocal()

    try:
        service = WebhookService(db)

        events = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.processed.is_(False))
            .order_by(WebhookEvent.id.asc())
            .all()
        )

        print(f"Found {len(events)} pending webhook events.")

        for event in events:
            print(
                f"Processing event "
                f"{event.event_id} "
                f"({event.event_type})"
            )

            service.process_payment_event(event)

        db.commit()

        print("Pending webhook processing completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()