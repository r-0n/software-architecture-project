"""
Enhanced test suite for flash sale checkout with concurrency, throttling, and latency.
Tests concurrent checkouts, throttling limits, and synchronous response times.
"""
import pytest
import json
import time
import threading
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from products.models import Product, Category
from orders.models import Sale, SaleItem, Payment
from worker.queue import QueuedJob


class FlashCheckoutTestCase(TransactionTestCase):
    """Test flash sale checkout with database transactions"""
    
    def setUp(self):
        """Set up test data"""
        # Clear cache before each test
        cache.clear()
        
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name="Test Category",
            description="Test category for flash sales"
        )
        
        # Create test product with flash sale
        self.now = timezone.now()
        self.start_time = self.now - timedelta(hours=1)
        self.end_time = self.now + timedelta(hours=1)
        
        self.product = Product.objects.create(
            name="Flash Sale Product",
            description="Product for flash sale testing",
            sku="FLASH-001",
            price=Decimal('100.00'),
            category=self.category,
            stock_quantity=2,  # Limited stock for concurrency testing
            is_active=True,
            flash_sale_enabled=True,
            flash_sale_price=Decimal('50.00'),
            flash_sale_starts_at=self.start_time,
            flash_sale_ends_at=self.end_time
        )
        
        # Login user
        self.client.force_login(self.user)
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    def test_concurrent_checkouts_same_product(self):
        """Test that concurrent checkouts on same product result in exactly one success"""
        results = []
        errors = []
        
        def checkout_request():
            try:
                # Add product to cart
                self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
                
                # Attempt checkout
                response = self.client.post('/cart/flash-checkout/', 
                    data=json.dumps({
                        'address': '123 Test St',
                        'payment_method': 'CARD',
                        'card_number': '1234567890123456'
                    }),
                    content_type='application/json',
                    HTTP_X_IDEMPOTENCY_KEY='test-key-' + str(time.time())
                )
                
                results.append({
                    'status_code': response.status_code,
                    'data': response.json() if response.status_code != 500 else None
                })
            except Exception as e:
                errors.append(str(e))
        
        # Start two concurrent checkout threads
        thread1 = threading.Thread(target=checkout_request)
        thread2 = threading.Thread(target=checkout_request)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")
        self.assertEqual(len(results), 2)
        
        # Exactly one should succeed (200/queued), one should fail (409/stock conflict)
        success_count = sum(1 for r in results if r['status_code'] in [200, 201])
        conflict_count = sum(1 for r in results if r['status_code'] == 409)
        
        self.assertEqual(success_count, 1, f"Expected 1 success, got {success_count}. Results: {results}")
        self.assertEqual(conflict_count, 1, f"Expected 1 conflict, got {conflict_count}. Results: {results}")
        
        # Verify final stock is correct (should be 0, not negative)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 0)
    
    def test_throttling_per_user_product(self):
        """Test granular throttling by user + product"""
        # Add product to cart
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        
        # Make requests up to the limit
        for i in range(6):  # Limit is 5, so 6th should be throttled
            response = self.client.post('/cart/flash-checkout/', 
                data=json.dumps({
                    'address': '123 Test St',
                    'payment_method': 'CARD',
                    'card_number': '1234567890123456'
                }),
                content_type='application/json',
                HTTP_X_IDEMPOTENCY_KEY=f'test-key-{i}'
            )
            
            if i < 5:
                # First 5 should succeed or fail for other reasons (like stock)
                self.assertIn(response.status_code, [200, 201, 409])
            else:
                # 6th should be throttled
                self.assertEqual(response.status_code, 429)
                self.assertIn('Retry-After', response)
                data = response.json()
                self.assertEqual(data['status'], 'throttled')
    
    def test_idempotency_key_prevention(self):
        """Test that idempotency keys prevent duplicate processing"""
        # Add product to cart
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        
        idempotency_key = 'test-idempotency-key'
        
        # First request
        response1 = self.client.post('/cart/flash-checkout/', 
            data=json.dumps({
                'address': '123 Test St',
                'payment_method': 'CARD',
                'card_number': '1234567890123456'
            }),
            content_type='application/json',
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key
        )
        
        # Second request with same idempotency key
        response2 = self.client.post('/cart/flash-checkout/', 
            data=json.dumps({
                'address': '123 Test St',
                'payment_method': 'CARD',
                'card_number': '1234567890123456'
            }),
            content_type='application/json',
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key
        )
        
        # Both should return the same result
        self.assertEqual(response1.status_code, response2.status_code)
        if response1.status_code == 200:
            self.assertEqual(response1.json(), response2.json())
    
    def test_synchronous_latency_bounded(self):
        """Test that synchronous response is under 1 second"""
        # Mock the queue enqueue to avoid actual async processing
        with patch('worker.queue.enqueue_job') as mock_enqueue:
            mock_job = MagicMock()
            mock_job.id = 123
            mock_enqueue.return_value = mock_job
            
            # Add product to cart
            self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
            
            # Measure checkout time
            start_time = time.time()
            response = self.client.post('/cart/flash-checkout/', 
                data=json.dumps({
                    'address': '123 Test St',
                    'payment_method': 'CARD',
                    'card_number': '1234567890123456'
                }),
                content_type='application/json',
                HTTP_X_IDEMPOTENCY_KEY='latency-test-key'
            )
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            
            # Should complete quickly
            self.assertLess(duration_ms, 1000, f"Response took {duration_ms}ms, expected < 1000ms")
            
            # Should return queued status
            if response.status_code == 200:
                data = response.json()
                self.assertEqual(data['status'], 'queued')
                self.assertIn('sync_duration_ms', data)
                self.assertLess(data['sync_duration_ms'], 1000)
    
    def test_stock_conflict_detailed_logging(self):
        """Test that stock conflicts are logged with detailed information"""
        # Set up product with limited stock
        self.product.stock_quantity = 1
        self.product.save()
        
        # Add product to cart for two users
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        
        # First checkout should succeed
        response1 = self.client.post('/cart/flash-checkout/', 
            data=json.dumps({
                'address': '123 Test St',
                'payment_method': 'CARD',
                'card_number': '1234567890123456'
            }),
            content_type='application/json',
            HTTP_X_IDEMPOTENCY_KEY='first-checkout'
        )
        
        # Second checkout should fail with stock conflict
        response2 = self.client.post('/cart/flash-checkout/', 
            data=json.dumps({
                'address': '456 Test St',
                'payment_method': 'CARD',
                'card_number': '1234567890123456'
            }),
            content_type='application/json',
            HTTP_X_IDEMPOTENCY_KEY='second-checkout'
        )
        
        # Verify one success, one conflict
        success_count = sum(1 for r in [response1, response2] if r.status_code in [200, 201])
        conflict_count = sum(1 for r in [response1, response2] if r.status_code == 409)
        
        self.assertEqual(success_count, 1)
        self.assertEqual(conflict_count, 1)
        
        # Verify conflict response has helpful message
        if response2.status_code == 409:
            data = response2.json()
            self.assertIn('another customer just purchased', data['message'])
    
    def test_flash_sale_disabled_returns_error(self):
        """Test that checkout fails when flash sale is globally disabled"""
        with patch('django.conf.settings.FLASH_SALE_ENABLED', False):
            # Add product to cart
            self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
            
            response = self.client.post('/cart/flash-checkout/', 
                data=json.dumps({
                    'address': '123 Test St',
                    'payment_method': 'CARD',
                    'card_number': '1234567890123456'
                }),
                content_type='application/json',
                HTTP_X_IDEMPOTENCY_KEY='disabled-test'
            )
            
            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertEqual(data['status'], 'error')
            self.assertIn('not currently enabled', data['message'])
    
    def test_no_flash_items_returns_error(self):
        """Test that checkout fails when cart has no flash sale items"""
        # Create a regular product (no flash sale)
        regular_product = Product.objects.create(
            name="Regular Product",
            description="Regular product without flash sale",
            sku="REG-001",
            price=Decimal('100.00'),
            category=self.category,
            stock_quantity=10,
            is_active=True,
            flash_sale_enabled=False
        )
        
        # Add regular product to cart
        self.client.post(f'/cart/add/{regular_product.id}/', {'quantity': 1})
        
        response = self.client.post('/cart/flash-checkout/', 
            data=json.dumps({
                'address': '123 Test St',
                'payment_method': 'CARD',
                'card_number': '1234567890123456'
            }),
            content_type='application/json',
            HTTP_X_IDEMPOTENCY_KEY='no-flash-test'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('No flash sale items', data['message'])
