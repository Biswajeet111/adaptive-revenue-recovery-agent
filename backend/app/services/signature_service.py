import hashlib
import hmac


def verify_razorpay_signature(
    payload: bytes,
    received_signature: str,
    webhook_secret: str,
) -> bool:
    expected_signature = hmac.new(
        webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        received_signature,
    )