import hashlib
import hmac

from backend.app.services.signature_service import (
    verify_razorpay_signature,
)


def test_valid_signature():
    payload = b'{"event":"payment.failed"}'
    secret = "test_webhook_secret"

    signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    assert verify_razorpay_signature(
        payload,
        signature,
        secret,
    )


def test_invalid_signature():
    payload = b'{"event":"payment.failed"}'
    secret = "test_webhook_secret"

    invalid_signature = "invalid_signature"

    assert not verify_razorpay_signature(
        payload,
        invalid_signature,
        secret,
    )