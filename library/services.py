from rest_framework.exceptions import ValidationError


def send_loan_reminder(loan):
    if loan.returned_at is not None:
        raise ValidationError(
            {"detail": "Cannot send a reminder for a returned loan."}
        )

    # Stub implementation until a real notification channel is wired in.
    return {
        "detail": "Reminder sending is not configured yet.",
        "loan_id": loan.id,
    }
