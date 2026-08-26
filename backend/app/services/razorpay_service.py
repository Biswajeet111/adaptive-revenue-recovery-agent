import razorpay

from backend.app.config import settings


class RazorpayService:
    def __init__(self) -> None:
        self.client = razorpay.Client(
            auth=(
                settings.razorpay_key_id,
                settings.razorpay_key_secret,
            )
        )

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: str | None = None,
    ) -> dict:
        order_data = {
            "amount": amount,
            "currency": currency,
        }

        if receipt:
            order_data["receipt"] = receipt

        return self.client.order.create(order_data)

    def fetch_payment(self, payment_id: str) -> dict:
        return self.client.payment.fetch(payment_id)

    def fetch_order(self, order_id: str) -> dict:
        return self.client.order.fetch(order_id)