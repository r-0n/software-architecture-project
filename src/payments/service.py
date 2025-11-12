"""
Payment Service with Resilience Patterns

Orchestrates payment processing with retry, circuit breaker, and timeout handling.
"""
import time
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache

from .client import PaymentGateway
from .policy import RetryPolicy, CircuitBreaker
from retail.logging import log_payment_attempt, log_breaker_transition


logger = logging.getLogger(__name__)


def charge_with_resilience(order, amount: Decimal, *, timeout_s: float = 2.0) -> Dict[str, Any]:
    """
    Process payment with resilience patterns (retry, circuit breaker, timeout).
    
    Args:
        order: Order instance
        amount: Payment amount
        timeout_s: Request timeout in seconds
        
    Returns:
        Dict with payment result and metadata
    """
    # Initialize components
    gateway = PaymentGateway()
    retry_policy = RetryPolicy()
    
    # Get circuit breaker configuration from settings
    cb_config = getattr(settings, 'CIRCUIT_BREAKER', {}).get('payment_gateway', {})
    circuit_breaker = CircuitBreaker(
        name="payment_gateway",
        threshold=cb_config.get('threshold', 5),
        window_s=cb_config.get('window_s', 60),
        cool_off_s=cb_config.get('cool_off_s', 60)
    )
    
    # Check circuit breaker state
    if not circuit_breaker.can_execute():
        # Calculate retry delay (remaining cool-off time, capped at 5s for UX)
        retry_delay_s = 0
        if circuit_breaker.get_state().value == "open":
            # Access last failure timestamp using the circuit breaker's cache key pattern
            last_failure_key = f"cb:payment_gateway:last_failure"
            last_failure = cache.get(last_failure_key)
            if last_failure:
                elapsed = time.time() - last_failure
                remaining = max(0, circuit_breaker.cool_off_s - elapsed)
                # Cap retry delay at 5 seconds for user-facing messages
                retry_delay_s = min(remaining, 5.0)
            else:
                retry_delay_s = min(circuit_breaker.cool_off_s, 5.0)
        
        logger.warning("payments.attempt", extra={
            "order_id": order.id,
            "attempt_no": 0,
            "latency_ms": 0,
            "breaker_state": circuit_breaker.get_state().value,
            "outcome": "circuit_open",
            "retry_delay_s": retry_delay_s
        })
        
        return {
            "status": "unavailable",
            "error": "circuit_open",
            "circuit_breaker_state": circuit_breaker.get_state().value,
            "retry_delay_s": retry_delay_s
        }
    
    # Attempt payment with retry policy
    last_exception = None
    
    for attempt in range(1, retry_policy.attempts + 1):
        start_time = time.time()
        
        try:
            # Execute payment
            result = gateway.charge(order.id, amount, timeout_s)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Record success
            circuit_breaker.on_success()
            
            logger.info("payments.attempt", extra={
                "order_id": order.id,
                "attempt_no": attempt,
                "latency_ms": latency_ms,
                "breaker_state": circuit_breaker.get_state().value,
                "outcome": "success"
            })
            
            return {
                "status": "ok",
                "provider_ref": result["provider_ref"],
                "attempts": attempt,
                "latency_ms": latency_ms,
                "circuit_breaker_state": circuit_breaker.get_state().value
            }
            
        except Exception as e:
            last_exception = e
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Record failure
            circuit_breaker.on_failure()
            
            logger.warning("payments.attempt", extra={
                "order_id": order.id,
                "attempt_no": attempt,
                "latency_ms": latency_ms,
                "breaker_state": circuit_breaker.get_state().value,
                "outcome": "failure",
                "error": str(e)
            })
            
            # Check if we should retry
            if not retry_policy.should_retry(e, attempt):
                break
            
            # Calculate delay and wait
            delay = retry_policy.get_delay(attempt)
            if delay > 0:
                time.sleep(delay)
    
    # All attempts failed
    logger.error("payments.attempt", extra={
        "order_id": order.id,
        "attempt_no": retry_policy.attempts,
        "latency_ms": 0,
        "breaker_state": circuit_breaker.get_state().value,
        "outcome": "exhausted",
        "error": str(last_exception) if last_exception else "unknown"
    })
    
    return {
        "status": "failed",
        "error": "gateway_failure",
        "attempts": retry_policy.attempts,
        "circuit_breaker_state": circuit_breaker.get_state().value,
        "last_error": str(last_exception) if last_exception else "unknown"
    }


def void_with_resilience(provider_ref: str, *, timeout_s: float = 2.0) -> Dict[str, Any]:
    """
    Void a payment with resilience patterns.
    
    Args:
        provider_ref: Provider transaction reference
        timeout_s: Request timeout in seconds
        
    Returns:
        Dict with void result
    """
    gateway = PaymentGateway()
    retry_policy = RetryPolicy()
    
    # Get circuit breaker configuration
    cb_config = getattr(settings, 'CIRCUIT_BREAKER', {}).get('payment_gateway', {})
    circuit_breaker = CircuitBreaker(
        name="payment_gateway",
        threshold=cb_config.get('threshold', 5),
        window_s=cb_config.get('window_s', 60),
        cool_off_s=cb_config.get('cool_off_s', 60)
    )
    
    # Check circuit breaker
    if not circuit_breaker.can_execute():
        return {
            "status": "unavailable",
            "error": "circuit_open"
        }
    
    # Attempt void with retry
    last_exception = None
    
    for attempt in range(1, retry_policy.attempts + 1):
        start_time = time.time()
        
        try:
            result = gateway.void(provider_ref, timeout_s)
            circuit_breaker.on_success()
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            logger.info("payments.void_attempt", extra={
                "provider_ref": provider_ref,
                "attempt_no": attempt,
                "latency_ms": latency_ms,
                "breaker_state": circuit_breaker.get_state().value,
                "outcome": "success"
            })
            
            return {
                "status": "ok",
                "provider_ref": provider_ref,
                "attempts": attempt,
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            last_exception = e
            latency_ms = int((time.time() - start_time) * 1000)
            
            circuit_breaker.on_failure()
            
            logger.warning("payments.void_attempt", extra={
                "provider_ref": provider_ref,
                "attempt_no": attempt,
                "latency_ms": latency_ms,
                "breaker_state": circuit_breaker.get_state().value,
                "outcome": "failure",
                "error": str(e)
            })
            
            if not retry_policy.should_retry(e, attempt):
                break
            
            delay = retry_policy.get_delay(attempt)
            if delay > 0:
                time.sleep(delay)
    
    return {
        "status": "failed",
        "error": "gateway_failure",
        "attempts": retry_policy.attempts,
        "last_error": str(last_exception) if last_exception else "unknown"
    }
