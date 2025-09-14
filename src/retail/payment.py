# src/orders/payment.py
import random

def process_payment(method: str, amount: float, card_number: str | None = None) -> dict:
    """
    Mock payment processing with detailed failure handling for A4.
    - CASH: always approved (address validation handled in form)
    - CARD: requires a card_number, approves 80% of the time
    """
    if method == "CASH":
        return {"status": "approved", "reference": "CASH-LOCAL"}

    if method == "CARD":
        if not card_number:
            return {"status": "failed", "reference": None, "reason": "No card number provided"}

        # Enhanced card validation - exactly 16 digits
        card_number = card_number.strip()
        if len(card_number) != 16:
            return {"status": "failed", "reference": None, "reason": "Card number must be exactly 16 digits"}
        
        if not card_number.isdigit():
            return {"status": "failed", "reference": None, "reason": "Card number must contain only numeric digits"}

        # Simulate various card decline scenarios
        random_factor = random.random()
        if random_factor < 0.8:
            return {"status": "approved", "reference": f"CARD-{random.randint(1000,9999)}"}
        elif random_factor < 0.9:
            return {"status": "declined", "reference": None, "reason": "Insufficient funds"}
        elif random_factor < 0.95:
            return {"status": "declined", "reference": None, "reason": "Card expired"}
        else:
            return {"status": "declined", "reference": None, "reason": "Card blocked"}

    return {"status": "failed", "reference": None, "reason": "Invalid payment method"}
