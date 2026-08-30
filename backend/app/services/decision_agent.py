import json
from pathlib import Path

from groq import Groq

from backend.app.config import settings
from backend.app.schemas.recovery_decision import (
    RecoveryDecision,
)
from backend.app.services.policy_retrieval_service import (
    PolicyEvidence,
)


class RecoveryDecisionAgent:

    ALLOWED_ACTIONS = {
        "delayed_retry",
        "request_payment_method_update",
        "alternative_payment_method",
        "manual_review",
    }

    CACHE_DIR = (
        Path(__file__).resolve().parents[1]
        / "cache"
    )

    CACHE_FILE = (
        CACHE_DIR
        / "last_recovery_decision.json"
    )

    def __init__(self):
        self.client = Groq(
            api_key=settings.groq_api_key
        )

        self.model = settings.groq_decision_model

    def decide(
        self,
        *,
        transaction_context: dict,
        policy_evidence: list[PolicyEvidence],
        use_cache: bool = True,
    ) -> RecoveryDecision:

        if use_cache and self.CACHE_FILE.exists():
            return self._load_cached_decision()

        if not policy_evidence:
            raise ValueError(
                "Cannot make a policy-grounded decision "
                "without policy evidence."
            )

        evidence_text = self._format_evidence(
            policy_evidence
        )

        system_prompt = """
You are the Recovery Decision Agent for an
automated revenue recovery system.

Your job is to recommend ONE recovery action
based only on the transaction context and the
provided policy evidence.

Rules:

1. Do not invent policies.
2. Do not invent transaction facts.
3. Do not recommend an unsupported action.
4. Prefer the least disruptive viable strategy.
5. High-risk or insufficiently supported cases
   should use manual_review.
6. A payment link being created does NOT mean
   revenue has been recovered.
7. Return ONLY valid JSON.
8. Confidence must be between 0 and 1.
9. Include policy document name and version
   in policy_references.

Allowed actions:

- delayed_retry
- request_payment_method_update
- alternative_payment_method
- manual_review

Return exactly:

{
  "classification": "string",
  "recoverability": "low | medium | high",
  "recommended_action": "delayed_retry | request_payment_method_update | alternative_payment_method | manual_review",
  "confidence": 0.0,
  "reason": "string",
  "policy_references": ["string"]
}
"""

        user_prompt = f"""
TRANSACTION CONTEXT:

{json.dumps(
    transaction_context,
    indent=2,
    default=str,
)}

POLICY EVIDENCE:

{evidence_text}

Determine the most appropriate recovery action
using only the supplied transaction context and
policy evidence.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={
                "type": "json_object",
            },
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "Groq returned an empty decision."
            )

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Groq returned invalid JSON."
            ) from exc

        decision = RecoveryDecision.model_validate(
            data
        )

        if (
            decision.recommended_action
            not in self.ALLOWED_ACTIONS
        ):
            raise ValueError(
                "Groq returned an unsupported "
                "recovery action."
            )

        self._save_cached_decision(
            decision
        )

        return decision

    @staticmethod
    def _format_evidence(
        evidence: list[PolicyEvidence],
    ) -> str:

        sections = []

        for index, item in enumerate(
            evidence,
            start=1,
        ):
            sections.append(
                f"""
[EVIDENCE {index}]
Document: {item.document.name}
Version: {item.document.version}
Similarity: {item.similarity:.4f}

Content:
{item.chunk.content}
"""
            )

        return "\n".join(sections)

    @classmethod
    def _save_cached_decision(
        cls,
        decision: RecoveryDecision,
    ) -> None:

        cls.CACHE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        cls.CACHE_FILE.write_text(
            decision.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )

    @classmethod
    def _load_cached_decision(
        cls,
    ) -> RecoveryDecision:

        data = json.loads(
            cls.CACHE_FILE.read_text(
                encoding="utf-8"
            )
        )

        return RecoveryDecision.model_validate(
            data
        )