from typing import Literal

from pydantic import BaseModel, Field


RecoveryActionType = Literal[
    "delayed_retry",
    "request_payment_method_update",
    "alternative_payment_method",
    "manual_review",
]


class RecoveryDecision(BaseModel):
    classification: str

    recoverability: Literal[
        "low",
        "medium",
        "high",
    ]

    recommended_action: RecoveryActionType

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reason: str

    policy_references: list[str]