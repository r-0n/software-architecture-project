"""
Payment Gateway Client

A minimal payment gateway stub for testing resilience patterns.
Simulates external payment service with configurable failures.
"""
import time
import random
from decimal import Decimal
from typing import Dict, Any


class PaymentGateway:
    """
    Mock payment gateway that simulates external service behavior.
    Supports configurable failures for testing resilience patterns.
    """
    
    def __init__(self, failure_rate: float = 0.0, timeout_rate: float = 0.0):
        """
        Initialize payment gateway with configurable failure rates.
        
        Args:
            failure_rate: Probability of RuntimeError (0.0-1.0)
            timeout_rate: Probability of TimeoutError (0.0-1.0)
        """
        self.failure_rate = failure_rate
        self.timeout_rate = timeout_rate
        self._call_count = 0
    
    def charge(self, order_id: int, amount: Decimal, timeout_s: float) -> Dict[str, Any]:
        """
        Process a payment charge.
        
        Args:
            order_id: Unique order identifier
            amount: Payment amount
            timeout_s: Request timeout in seconds
            
        Returns:
            Dict with status, provider_ref, and optional error details
            
        Raises:
            TimeoutError: If simulated timeout occurs
            RuntimeError: If simulated service failure occurs
        """
        self._call_count += 1
        
        # Simulate network latency
        time.sleep(random.uniform(0.01, 0.1))
        
        # Simulate timeout
        if random.random() < self.timeout_rate:
            raise TimeoutError(f"Payment gateway timeout after {timeout_s}s")
        
        # Simulate service failure
        if random.random() < self.failure_rate:
            error_code = random.choice(["500", "502", "503", "504"])
            raise RuntimeError(f"Payment gateway error: HTTP {error_code}")
        
        # Successful payment
        provider_ref = f"txn_{order_id}_{self._call_count}_{int(time.time())}"
        return {
            "status": "approved",
            "provider_ref": provider_ref,
            "amount": str(amount),
            "order_id": order_id
        }
    
    def void(self, provider_ref: str, timeout_s: float) -> Dict[str, Any]:
        """
        Void a previously processed payment.
        
        Args:
            provider_ref: Provider transaction reference
            timeout_s: Request timeout in seconds
            
        Returns:
            Dict with void status and details
            
        Raises:
            TimeoutError: If simulated timeout occurs
            RuntimeError: If simulated service failure occurs
        """
        # Simulate network latency
        time.sleep(random.uniform(0.01, 0.05))
        
        # Simulate timeout
        if random.random() < self.timeout_rate:
            raise TimeoutError(f"Payment gateway timeout after {timeout_s}s")
        
        # Simulate service failure
        if random.random() < self.failure_rate:
            error_code = random.choice(["500", "502", "503", "504"])
            raise RuntimeError(f"Payment gateway error: HTTP {error_code}")
        
        # Successful void
        return {
            "status": "voided",
            "provider_ref": provider_ref,
            "voided_at": int(time.time())
        }
    
    def reset_failure_rates(self, failure_rate: float = 0.0, timeout_rate: float = 0.0):
        """Reset failure rates for testing."""
        self.failure_rate = failure_rate
        self.timeout_rate = timeout_rate
        self._call_count = 0
