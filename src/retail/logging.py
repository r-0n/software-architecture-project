"""
Enhanced observability and logging for flash sale system.
Includes timing instrumentation and comprehensive event logging.
"""
import logging
import time
from django.utils import timezone
from typing import List, Optional

logger = logging.getLogger(__name__)


class FlashSaleTimer:
    """Context manager for timing flash sale operations"""
    
    def __init__(self, operation_name: str, user_id: str, product_ids: List[int] = None):
        self.operation_name = operation_name
        self.user_id = user_id
        self.product_ids = product_ids or []
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.monotonic()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.monotonic()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        logger.info(f"flash_sale.timing.{self.operation_name}", extra={
            'event': f'{self.operation_name}_timing',
            'user_id': self.user_id,
            'product_ids': self.product_ids,
            'duration_ms': round(duration_ms, 2),
            'timestamp': timezone.now().isoformat()
        })


def log_checkout_requested(user_id: str, product_ids: List[int], total_amount: float, 
                          idempotency_key: str = None):
    """Log when a flash sale checkout is requested"""
    logger.info("flash_sale.checkout.requested", extra={
        'event': 'checkout_requested',
        'user_id': user_id,
        'product_ids': product_ids,
        'total_amount': total_amount,
        'idempotency_key': idempotency_key,
        'timestamp': timezone.now().isoformat()
    })


def log_checkout_throttled(user_id: str, reason: str, retry_after: int, product_id: int = None):
    """Log when a checkout request is throttled"""
    logger.warning("flash_sale.checkout.throttled", extra={
        'event': 'checkout_throttled',
        'user_id': user_id,
        'reason': reason,
        'retry_after_seconds': retry_after,
        'product_id': product_id,
        'timestamp': timezone.now().isoformat()
    })


def log_checkout_stock_conflict(user_id: str, product_id: int, product_name: str, 
                               requested_quantity: int, remaining_stock: int):
    """Log when a stock conflict occurs during checkout"""
    logger.error("flash_sale.checkout.stock_conflict", extra={
        'event': 'checkout_stock_conflict',
        'user_id': user_id,
        'product_id': product_id,
        'product_name': product_name,
        'requested_quantity': requested_quantity,
        'remaining_stock': remaining_stock,
        'timestamp': timezone.now().isoformat()
    })


def log_checkout_queued(user_id: str, sale_id: int, job_id: int, duration_ms: float):
    """Log when a checkout is successfully queued"""
    logger.info("flash_sale.checkout.queued", extra={
        'event': 'checkout_queued',
        'user_id': user_id,
        'sale_id': sale_id,
        'job_id': job_id,
        'sync_duration_ms': duration_ms,
        'timestamp': timezone.now().isoformat()
    })


def log_checkout_finalized(user_id: str, sale_id: int, payment_status: str, 
                          processing_duration_ms: float):
    """Log when a checkout is finalized"""
    logger.info("flash_sale.checkout.finalized", extra={
        'event': 'checkout_finalized',
        'user_id': user_id,
        'sale_id': sale_id,
        'payment_status': payment_status,
        'processing_duration_ms': processing_duration_ms,
        'timestamp': timezone.now().isoformat()
    })


def log_reservation_created(user_id: str, sale_id: int, product_id: int, 
                          quantity: int, ttl_minutes: int):
    """Log when a stock reservation is created"""
    logger.info("flash_sale.reservation.created", extra={
        'event': 'reservation_created',
        'user_id': user_id,
        'sale_id': sale_id,
        'product_id': product_id,
        'quantity': quantity,
        'ttl_minutes': ttl_minutes,
        'timestamp': timezone.now().isoformat()
    })


def log_reservation_released(user_id: str, sale_id: int, product_id: int, 
                           quantity: int, reason: str):
    """Log when a stock reservation is released"""
    logger.info("flash_sale.reservation.released", extra={
        'event': 'reservation_released',
        'user_id': user_id,
        'sale_id': sale_id,
        'product_id': product_id,
        'quantity': quantity,
        'reason': reason,  # 'payment_success', 'payment_failed', 'ttl_expired'
        'timestamp': timezone.now().isoformat()
    })


def log_price_validation(user_id: str, product_id: int, add_to_cart_price: float, 
                        checkout_price: float, is_consistent: bool):
    """Log price validation between add-to-cart and checkout"""
    level = logging.INFO if is_consistent else logging.WARNING
    logger.log(level, "flash_sale.price_validation", extra={
        'event': 'price_validation',
        'user_id': user_id,
        'product_id': product_id,
        'add_to_cart_price': add_to_cart_price,
        'checkout_price': checkout_price,
        'is_consistent': is_consistent,
        'timestamp': timezone.now().isoformat()
    })


def log_idempotency_check(user_id: str, idempotency_key: str, is_duplicate: bool, 
                         existing_sale_id: int = None):
    """Log idempotency key validation"""
    logger.info("flash_sale.idempotency_check", extra={
        'event': 'idempotency_check',
        'user_id': user_id,
        'idempotency_key': idempotency_key,
        'is_duplicate': is_duplicate,
        'existing_sale_id': existing_sale_id,
        'timestamp': timezone.now().isoformat()
    })


# Payment Resilience Logging Functions

def log_payment_attempt(order_id: int, attempt_no: int, latency_ms: int, 
                        breaker_state: str, outcome: str, error: str = None):
    """Log payment attempt with resilience metrics"""
    extra_data = {
        'event': 'payment_attempt',
        'order_id': order_id,
        'attempt_no': attempt_no,
        'latency_ms': latency_ms,
        'breaker_state': breaker_state,
        'outcome': outcome,
        'timestamp': timezone.now().isoformat()
    }
    
    if error:
        extra_data['error'] = error
    
    if outcome == 'success':
        logger.info("payments.attempt", extra=extra_data)
    elif outcome == 'failure':
        logger.warning("payments.attempt", extra=extra_data)
    elif outcome == 'circuit_open':
        logger.error("payments.attempt", extra=extra_data)
    else:
        logger.info("payments.attempt", extra=extra_data)


def log_breaker_transition(circuit_name: str, from_state: str, to_state: str):
    """Log circuit breaker state transition"""
    logger.info("payments.breaker_transition", extra={
        'event': 'breaker_transition',
        'circuit_name': circuit_name,
        'from_state': from_state,
        'to_state': to_state,
        'timestamp': timezone.now().isoformat()
    })


def log_checkout_rollback(order_id: int, reason: str, circuit_state: str = None, 
                         attempts: int = None, error: str = None):
    """Log checkout atomic rollback"""
    extra_data = {
        'event': 'checkout_rollback',
        'order_id': order_id,
        'reason': reason,
        'timestamp': timezone.now().isoformat()
    }
    
    if circuit_state:
        extra_data['circuit_state'] = circuit_state
    if attempts:
        extra_data['attempts'] = attempts
    if error:
        extra_data['error'] = error
    
    logger.warning("checkout.atomic.rollback", extra=extra_data)


def log_checkout_commit(order_id: int, provider_ref: str, attempts: int, latency_ms: int):
    """Log successful checkout commit"""
    logger.info("checkout.atomic.commit", extra={
        'event': 'checkout_commit',
        'order_id': order_id,
        'provider_ref': provider_ref,
        'attempts': attempts,
        'latency_ms': latency_ms,
        'timestamp': timezone.now().isoformat()
    })