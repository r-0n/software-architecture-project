# src/orders/payment.py
import random

def process_payment(method: str, amount: float, card_number: str | None = None) -> dict:
    """
    Mock payment processing.
    - CASH: always approved
    - CARD: requires a card_number, approves 80% of the time
    """
    if method == "CASH":
        return {"status": "approved", "reference": "CASH-LOCAL"}

    if method == "CARD":
        if not card_number:
            return {"status": "failed", "reference": None}

        # fake card validation
        if len(card_number) < 12:
            return {"status": "failed", "reference": None}

        if random.random() < 0.8:
            return {"status": "approved", "reference": f"CARD-{random.randint(1000,9999)}"}
        return {"status": "declined", "reference": None}

    return {"status": "failed", "reference": None}
