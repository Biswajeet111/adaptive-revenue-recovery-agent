from typing import Any

from pydantic import BaseModel, ConfigDict


class RazorpayWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    entity: str | None = None
    account_id: str | None = None
    event: str
    contains: list[str] = []
    payload: dict[str, Any]