# src/retail/payment.py
import random

def process_payment(method: str, amount: float) -> dict:
    """Simulate payment gateway approval."""
    if method == "CASH":
        return {"status": "approved", "reference": "CASH-LOCAL"}
    if method == "CARD":
        if random.random() < 0.9:
            return {"status": "approved", "reference": f"CARD-{random.randint(1000,9999)}"}
        return {"status": "declined", "reference": None}
    return {"status": "failed", "reference": None}
