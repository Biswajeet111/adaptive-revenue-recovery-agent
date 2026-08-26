from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models.transaction import Transaction
from backend.app.services.recovery_service import RecoveryService


def main():
    db = SessionLocal()

    try:
        transactions = db.scalars(
            select(Transaction).where(
                Transaction.status == "failed"
            )
        ).all()

        print(
            f"Found {len(transactions)} failed transactions."
        )

        service = RecoveryService(db)

        for transaction in transactions:
            print(
                f"Creating recovery case for "
                f"transaction {transaction.id}"
            )

            case = service.create_case_for_transaction(
                transaction
            )

            print(
                f"Recovery case {case.id}: "
                f"{case.classification} / "
                f"{case.recoverability} / "
                f"{case.recommended_action}"
            )

        db.commit()

        print(
            "Recovery case creation completed."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()