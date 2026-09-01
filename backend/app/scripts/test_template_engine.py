from backend.app.services.template_engine import (
    TemplateEngine,
)


def main():

    print(
        "=== PHASE 11.2 TEMPLATE ENGINE TEST ==="
    )

    engine = TemplateEngine()

    # -------------------------------------------------
    # TEST 1 — VALID EMAIL RENDER
    # -------------------------------------------------

    rendered = engine.render(
        name="payment_recovery",
        version="1.0",
        channel="email",
        variables={
            "customer_name": "Test Customer",
            "currency": "INR",
            "amount": "100.00",
            "payment_link": "https://example.test/pay",
            "expiry": "31 Aug 2026",
        },
    )

    assert (
        rendered.name
        == "payment_recovery"
    )

    assert (
        rendered.version
        == "1.0"
    )

    assert (
        rendered.channel
        == "email"
    )

    assert (
        "Test Customer"
        in rendered.body
    )

    assert (
        "INR 100.00"
        in rendered.body
    )

    assert (
        "https://example.test/pay"
        in rendered.body
    )

    print(
        "TEST 1 PASSED: Valid email template "
        "rendered correctly."
    )

    # -------------------------------------------------
    # TEST 2 — VALID SMS RENDER
    # -------------------------------------------------

    rendered = engine.render(
        name="payment_recovery",
        version="1.0",
        channel="sms",
        variables={
            "customer_name": "Test Customer",
            "currency": "INR",
            "amount": "100.00",
            "payment_link": "https://example.test/pay",
            "expiry": "31 Aug 2026",
        },
    )

    assert (
        rendered.channel
        == "sms"
    )

    assert (
        "Test Customer"
        in rendered.body
    )

    print(
        "TEST 2 PASSED: SMS template "
        "rendered correctly."
    )

    # -------------------------------------------------
    # TEST 3 — MISSING VARIABLE REJECTED
    # -------------------------------------------------

    missing_rejected = False

    try:

        engine.render(
            name="payment_recovery",
            version="1.0",
            channel="email",
            variables={
                "customer_name": "Test Customer",
                "currency": "INR",
                "amount": "100.00",
                "payment_link": (
                    "https://example.test/pay"
                ),
            },
        )

    except ValueError as exc:

        missing_rejected = True

        assert (
            "Missing communication variables"
            in str(exc)
        )

    assert missing_rejected

    print(
        "TEST 3 PASSED: Missing variable "
        "rejected safely."
    )

    # -------------------------------------------------
    # TEST 4 — UNKNOWN VARIABLE REJECTED
    # -------------------------------------------------

    unknown_rejected = False

    try:

        engine.render(
            name="payment_recovery",
            version="1.0",
            channel="email",
            variables={
                "customer_name": "Test Customer",
                "currency": "INR",
                "amount": "100.00",
                "payment_link": (
                    "https://example.test/pay"
                ),
                "expiry": "31 Aug 2026",
                "secret_variable": (
                    "should-not-be-accepted"
                ),
            },
        )

    except ValueError as exc:

        unknown_rejected = True

        assert (
            "Unknown communication variables"
            in str(exc)
        )

    assert unknown_rejected

    print(
        "TEST 4 PASSED: Unknown variable "
        "rejected safely."
    )

    # -------------------------------------------------
    # TEST 5 — UNKNOWN TEMPLATE REJECTED
    # -------------------------------------------------

    template_rejected = False

    try:

        engine.render(
            name="does_not_exist",
            version="1.0",
            channel="email",
            variables={},
        )

    except ValueError as exc:

        template_rejected = True

        assert (
            "Communication template not found"
            in str(exc)
        )

    assert template_rejected

    print(
        "TEST 5 PASSED: Unknown template "
        "rejected safely."
    )

    # -------------------------------------------------
    # TEST 6 — TEMPLATE VERSIONING
    # -------------------------------------------------

    template = engine.get_template(
        name="payment_recovery",
        version="1.0",
        channel="email",
    )

    assert (
        template.version
        == "1.0"
    )

    print(
        "TEST 6 PASSED: Template versioning "
        "is explicit."
    )

    print(
        "\n=== PHASE 11.2 TEMPLATE ENGINE "
        "TEST PASSED ==="
    )


if __name__ == "__main__":
    main()