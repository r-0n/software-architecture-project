"""
Enhanced async processing system for flash sales.
Includes reservation TTL and automatic stock release.
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
import json
import time
from retail.logging import log_checkout_finalized, log_reservation_released


class QueuedJob(models.Model):
    """DB-backed queue for async processing"""
    JOB_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    job_type = models.CharField(max_length=100)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['job_type', 'status']),
        ]

    def __str__(self):
        return f"{self.job_type} - {self.status} ({self.id})"


class StockReservation(models.Model):
    """Track stock reservations with TTL for automatic release"""
    sale_id = models.IntegerField()
    product_id = models.IntegerField()
    quantity = models.PositiveIntegerField()
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('RELEASED', 'Released'),
        ('COMMITTED', 'Committed'),
    ], default='ACTIVE')
    
    class Meta:
        indexes = [
            models.Index(fields=['expires_at', 'status']),
            models.Index(fields=['sale_id']),
            models.Index(fields=['product_id']),
        ]

    def __str__(self):
        return f"Reservation {self.id}: {self.quantity} of product {self.product_id}"


def enqueue_job(job_type: str, payload: dict) -> QueuedJob:
    """Enqueue a job for async processing"""
    return QueuedJob.objects.create(
        job_type=job_type,
        payload=payload
    )


def create_stock_reservation(sale_id: int, product_id: int, quantity: int) -> StockReservation:
    """Create a stock reservation with TTL"""
    from django.utils import timezone
    from datetime import timedelta
    
    expires_at = timezone.now() + timedelta(minutes=settings.FLASH_ORDER_RESERVATION_TTL_MINUTES)
    
    return StockReservation.objects.create(
        sale_id=sale_id,
        product_id=product_id,
        quantity=quantity,
        expires_at=expires_at
    )


def release_stock_reservation(sale_id: int, reason: str = 'payment_failed'):
    """Release stock reservations for a sale"""
    from products.models import Product
    from retail.logging import log_reservation_released
    
    reservations = StockReservation.objects.filter(
        sale_id=sale_id, 
        status='ACTIVE'
    )
    
    for reservation in reservations:
        # Release the stock back to the product
        try:
            product = Product.objects.get(id=reservation.product_id)
            product.stock_quantity += reservation.quantity
            product.save()
            
            # Mark reservation as released
            reservation.status = 'RELEASED'
            reservation.save()
            
            log_reservation_released(
                user_id='system',
                sale_id=sale_id,
                product_id=reservation.product_id,
                quantity=reservation.quantity,
                reason=reason
            )
        except Product.DoesNotExist:
            # Product was deleted, just mark reservation as released
            reservation.status = 'RELEASED'
            reservation.save()


def commit_stock_reservation(sale_id: int):
    """Commit stock reservations (mark as committed, don't release)"""
    reservations = StockReservation.objects.filter(
        sale_id=sale_id, 
        status='ACTIVE'
    )
    
    for reservation in reservations:
        reservation.status = 'COMMITTED'
        reservation.save()


def cleanup_expired_reservations():
    """Clean up expired reservations and release stock"""
    from django.utils import timezone
    
    expired_reservations = StockReservation.objects.filter(
        status='ACTIVE',
        expires_at__lt=timezone.now()
    )
    
    for reservation in expired_reservations:
        release_stock_reservation(reservation.sale_id, 'ttl_expired')


def finalize_flash_order(order_data: dict):
    """Enhanced finalization with reservation management and comprehensive logging"""
    from orders.models import Sale, Payment
    from retail.payment import process_payment
    from retail.logging import log_checkout_finalized
    
    start_time = time.monotonic()
    
    try:
        sale_id = order_data['sale_id']
        payment_method = order_data['payment_method']
        card_number = order_data['card_number']
        amount = order_data['amount']
        
        # Get the sale and payment objects
        sale = Sale.objects.get(id=sale_id)
        payment = Payment.objects.get(sale=sale)
        
        # Process payment
        payment_result = process_payment(
            payment_method=payment_method,
            card_number=card_number,
            amount=amount
        )
        
        # Update payment status
        payment.status = 'COMPLETED' if payment_result['success'] else 'FAILED'
        payment.reference = payment_result.get('reference', '')
        payment.save()
        
        # Update sale status
        sale.status = 'COMPLETED' if payment_result['success'] else 'FAILED'
        sale.save()
        
        # Handle stock reservations based on payment result
        if payment_result['success']:
            commit_stock_reservation(sale_id)
        else:
            release_stock_reservation(sale_id, 'payment_failed')
        
        # Log completion
        processing_duration_ms = (time.monotonic() - start_time) * 1000
        user_id = str(sale.user.id) if sale.user else 'anonymous'
        
        log_checkout_finalized(
            user_id=user_id,
            sale_id=sale_id,
            payment_status=payment.status,
            processing_duration_ms=processing_duration_ms
        )
        
    except Exception as e:
        # Release stock on any error
        try:
            release_stock_reservation(order_data['sale_id'], 'processing_error')
        except:
            pass  # Don't let cleanup errors mask the original error
        
        # Log the error
        processing_duration_ms = (time.monotonic() - start_time) * 1000
        log_checkout_finalized(
            user_id='system',
            sale_id=order_data.get('sale_id', 0),
            payment_status='ERROR',
            processing_duration_ms=processing_duration_ms
        )
        
        raise e
