import argparse
import time

from backend.app.database import SessionLocal
from backend.app.services.recovery_worker import RecoveryWorker


def main():

    parser = argparse.ArgumentParser(
        description="Run the Adaptive Revenue Recovery Worker."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without external payment execution.",
    )

    parser.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="Number of worker cycles. 0 means continuous.",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Seconds between worker cycles.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Maximum actions processed per cycle.",
    )

    args = parser.parse_args()

    cycle = 0

    print(
        "=== ADAPTIVE REVENUE RECOVERY WORKER ==="
    )

    print(
        f"Mode: "
        f"{'DRY-RUN' if args.dry_run else 'LIVE'}"
    )

    print(
        f"Batch size: {args.batch_size}"
    )

    print(
        f"Interval: {args.interval}s"
    )

    print(
        f"Cycles: "
        f"{'continuous' if args.cycles == 0 else args.cycles}"
    )

    print()

    while True:

        cycle += 1

        db = SessionLocal()

        try:

            print(
                f"--- Worker cycle {cycle} ---"
            )

            worker = RecoveryWorker(
                db=db,
                batch_size=args.batch_size,
                dry_run=args.dry_run,
            )

            result = worker.run_once()

            print(
                f"Found: {result['found']} | "
                f"Stale recovered: "
                f"{result['stale_recovered']} | "
                f"Claimed: {result['claimed']} | "
                f"Processed: {result['processed']} | "
                f"Failed: {result['failed']}"
            )

        except KeyboardInterrupt:

            print()
            print(
                "Worker stopped by user."
            )

            break

        except Exception as exc:

            print(
                f"Worker cycle failed: {exc}"
            )

        finally:

            db.close()

        if args.cycles > 0:

            if cycle >= args.cycles:

                print()
                print(
                    "Worker completed requested cycles."
                )

                break

        time.sleep(
            max(args.interval, 1)
        )


if __name__ == "__main__":
    main()