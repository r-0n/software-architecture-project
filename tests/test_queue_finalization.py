"""
Enhanced test suite for queue finalization with reservation TTL and stock release.
Tests async job processing, reservation management, and automatic cleanup.
"""
import pytest
import time
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from products.models import Product, Category
from orders.models import Sale, SaleItem, Payment
from worker.queue import (
    QueuedJob, StockReservation, enqueue_job, finalize_flash_order,
    create_stock_reservation, release_stock_reservation, commit_stock_reservation,
    cleanup_expired_reservations
)


class QueueFinalizationTestCase(TestCase):
    """Test queue finalization and reservation management"""
    
    def setUp(self):
        """Set up test data"""
        # Create test category
        self.category = Category.objects.create(
            name="Test Category",
            description="Test category for queue testing"
        )
        
        # Create test product
        self.product = Product.objects.create(
            name="Queue Test Product",
            description="Product for queue testing",
            sku="QUEUE-001",
            price=Decimal('100.00'),
            category=self.category,
            stock_quantity=10,
            is_active=True
        )
        
        # Create test sale
        self.sale = Sale.objects.create(
            user=None,
            address="123 Test St",
            total=Decimal('100.00'),
            status="PENDING"
        )
        
        # Create test payment
        self.payment = Payment.objects.create(
            sale=self.sale,
            method="CARD",
            reference="",
            amount=Decimal('100.00'),
            status="PENDING"
        )
    
    def test_enqueue_job_creation(self):
        """Test that jobs are properly enqueued"""
        payload = {'sale_id': self.sale.id, 'test': 'data'}
        job = enqueue_job('test_job', payload)
        
        self.assertIsInstance(job, QueuedJob)
        self.assertEqual(job.job_type, 'test_job')
        self.assertEqual(job.payload, payload)
        self.assertEqual(job.status, 'PENDING')
        self.assertIsNotNone(job.created_at)
    
    def test_stock_reservation_creation(self):
        """Test stock reservation creation with TTL"""
        reservation = create_stock_reservation(
            self.sale.id, 
            self.product.id, 
            5
        )
        
        self.assertIsInstance(reservation, StockReservation)
        self.assertEqual(reservation.sale_id, self.sale.id)
        self.assertEqual(reservation.product_id, self.product.id)
        self.assertEqual(reservation.quantity, 5)
        self.assertEqual(reservation.status, 'ACTIVE')
        self.assertIsNotNone(reservation.expires_at)
        
        # Verify TTL is set correctly
        expected_expiry = timezone.now() + timedelta(minutes=5)  # Default TTL
        time_diff = abs((reservation.expires_at - expected_expiry).total_seconds())
        self.assertLess(time_diff, 60)  # Within 1 minute
    
    def test_stock_reservation_release(self):
        """Test stock reservation release"""
        # Create reservation
        reservation = create_stock_reservation(
            self.sale.id, 
            self.product.id, 
            3
        )
        
        # Verify stock was decremented
        self.product.refresh_from_db()
        original_stock = self.product.stock_quantity
        
        # Release reservation
        release_stock_reservation(self.sale.id, 'test_release')
        
        # Verify stock was restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, original_stock + 3)
        
        # Verify reservation status
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'RELEASED')
    
    def test_stock_reservation_commit(self):
        """Test stock reservation commit (no release)"""
        # Create reservation
        reservation = create_stock_reservation(
            self.sale.id, 
            self.product.id, 
            2
        )
        
        # Commit reservation
        commit_stock_reservation(self.sale.id)
        
        # Verify reservation status changed
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'COMMITTED')
        
        # Verify stock was not restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8)  # Original 10 - 2
    
    def test_finalize_flash_order_success(self):
        """Test successful flash order finalization"""
        # Mock payment processing
        with patch('worker.queue.process_payment') as mock_process:
            mock_process.return_value = {
                'success': True,
                'reference': 'PAY-123'
            }
            
            # Create job payload
            job_payload = {
                'sale_id': self.sale.id,
                'payment_method': 'CARD',
                'card_number': '1234567890123456',
                'amount': 100.0
            }
            
            # Create stock reservation
            create_stock_reservation(self.sale.id, self.product.id, 1)
            
            # Finalize order
            finalize_flash_order(job_payload)
            
            # Verify payment was processed
            mock_process.assert_called_once_with(
                payment_method='CARD',
                card_number='1234567890123456',
                amount=100.0
            )
            
            # Verify sale and payment status
            self.sale.refresh_from_db()
            self.payment.refresh_from_db()
            
            self.assertEqual(self.sale.status, 'COMPLETED')
            self.assertEqual(self.payment.status, 'COMPLETED')
            self.assertEqual(self.payment.reference, 'PAY-123')
            
            # Verify reservation was committed
            reservation = StockReservation.objects.get(sale_id=self.sale.id)
            self.assertEqual(reservation.status, 'COMMITTED')
    
    def test_finalize_flash_order_payment_failure(self):
        """Test flash order finalization with payment failure"""
        # Mock payment processing failure
        with patch('worker.queue.process_payment') as mock_process:
            mock_process.return_value = {
                'success': False,
                'reference': 'FAIL-123'
            }
            
            # Create job payload
            job_payload = {
                'sale_id': self.sale.id,
                'payment_method': 'CARD',
                'card_number': '1234567890123456',
                'amount': 100.0
            }
            
            # Create stock reservation
            create_stock_reservation(self.sale.id, self.product.id, 2)
            
            # Finalize order
            finalize_flash_order(job_payload)
            
            # Verify sale and payment status
            self.sale.refresh_from_db()
            self.payment.refresh_from_db()
            
            self.assertEqual(self.sale.status, 'FAILED')
            self.assertEqual(self.payment.status, 'FAILED')
            
            # Verify reservation was released
            reservation = StockReservation.objects.get(sale_id=self.sale.id)
            self.assertEqual(reservation.status, 'RELEASED')
            
            # Verify stock was restored
            self.product.refresh_from_db()
            self.assertEqual(self.product.stock_quantity, 10)  # Original stock restored
    
    def test_finalize_flash_order_processing_error(self):
        """Test flash order finalization with processing error"""
        # Create job payload that will cause an error
        job_payload = {
            'sale_id': 99999,  # Non-existent sale
            'payment_method': 'CARD',
            'card_number': '1234567890123456',
            'amount': 100.0
        }
        
        # Create stock reservation
        create_stock_reservation(99999, self.product.id, 1)
        
        # Finalize order should raise exception
        with self.assertRaises(Exception):
            finalize_flash_order(job_payload)
        
        # Verify reservation was released due to error
        reservation = StockReservation.objects.get(sale_id=99999)
        self.assertEqual(reservation.status, 'RELEASED')
    
    def test_cleanup_expired_reservations(self):
        """Test automatic cleanup of expired reservations"""
        # Create expired reservation
        expired_time = timezone.now() - timedelta(minutes=10)
        reservation = StockReservation.objects.create(
            sale_id=self.sale.id,
            product_id=self.product.id,
            quantity=3,
            expires_at=expired_time,
            status='ACTIVE'
        )
        
        # Create non-expired reservation
        future_time = timezone.now() + timedelta(minutes=10)
        active_reservation = StockReservation.objects.create(
            sale_id=self.sale.id + 1,
            product_id=self.product.id,
            quantity=2,
            expires_at=future_time,
            status='ACTIVE'
        )
        
        # Run cleanup
        cleanup_expired_reservations()
        
        # Verify expired reservation was released
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'RELEASED')
        
        # Verify non-expired reservation is still active
        active_reservation.refresh_from_db()
        self.assertEqual(active_reservation.status, 'ACTIVE')
        
        # Verify stock was restored for expired reservation
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 13)  # Original 10 + 3 restored
    
    def test_multiple_reservations_per_sale(self):
        """Test handling multiple reservations for a single sale"""
        # Create multiple reservations for the same sale
        create_stock_reservation(self.sale.id, self.product.id, 2)
        
        # Create another product
        product2 = Product.objects.create(
            name="Second Product",
            description="Second product for testing",
            sku="QUEUE-002",
            price=Decimal('50.00'),
            category=self.category,
            stock_quantity=5,
            is_active=True
        )
        
        create_stock_reservation(self.sale.id, product2.id, 1)
        
        # Release all reservations
        release_stock_reservation(self.sale.id, 'test_release')
        
        # Verify both reservations were released
        reservations = StockReservation.objects.filter(sale_id=self.sale.id)
        self.assertEqual(reservations.count(), 2)
        
        for reservation in reservations:
            self.assertEqual(reservation.status, 'RELEASED')
        
        # Verify stock was restored for both products
        self.product.refresh_from_db()
        product2.refresh_from_db()
        
        self.assertEqual(self.product.stock_quantity, 10)  # Original restored
        self.assertEqual(product2.stock_quantity, 5)  # Original restored
