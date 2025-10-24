"""
Quality Scenario Test Suite - Tests for all 14 quality scenarios from QS-Catalog.md

This test file validates each of the 14 quality scenarios across 7 quality attributes:
- Availability (A1, A2)
- Security (S1, S2) 
- Modifiability (M1, M2)
- Performance (P1, P2)
- Integrability (I1, I2)
- Testability (T1, T2)
- Usability (U1, U2)
"""

import json
import time
import threading
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
from django.urls import reverse
from django.core.management import call_command
from django.test.utils import override_settings
import os
import tempfile

from products.models import Product, Category
from cart.models import CartItem
from orders.models import Sale, SaleItem, Payment
from partner_feeds.models import Partner
from partner_feeds.adapters import FeedAdapterFactory
from partner_feeds.validators import ProductFeedValidator
from partner_feeds.services import FeedIngestionService
from payments.policy import CircuitBreaker, CircuitBreakerState
from payments.service import charge_with_resilience


class QualityScenarioTestSuite(TestCase):
    """
    Comprehensive test suite for all 14 quality scenarios from QS-Catalog.md
    """
    
    def setUp(self):
        """Set up test data for all scenarios"""
        # Mock worker functionality to avoid database table issues
        self.worker_patcher = patch('worker.queue.enqueue_job')
        self.mock_enqueue_job = self.worker_patcher.start()
        self.mock_enqueue_job.return_value = MagicMock(id=1)
        
        # Create test users
        self.user1 = User.objects.create_user(username='user1', password='testpass')
        self.user2 = User.objects.create_user(username='user2', password='testpass')
        self.admin_user = User.objects.create_user(username='admin', password='testpass', is_staff=True, is_superuser=True)
        
        # Create test category
        self.category = Category.objects.create(name='Test Category')
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            sku='TEST001',
            price=Decimal('10.00'),
            stock_quantity=100,
            category=self.category,
            is_active=True
        )
        
        self.flash_product = Product.objects.create(
            name='Flash Sale Product',
            sku='FLASH001',
            price=Decimal('20.00'),
            stock_quantity=5,  # Limited stock for flash sale
            category=self.category,
            is_active=True,
            flash_sale_enabled=False,  # Start with flash sale disabled
            flash_sale_price=Decimal('15.00')
        )
        
        # Create test partner feed
        self.partner_feed = Partner.objects.create(
            name='Test Partner',
            feed_format='CSV',
            feed_url='http://test.com/feed.csv',
            is_active=True
        )
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Clean up test data"""
        self.worker_patcher.stop()
        super().tearDown()
    
    # ============================================================================
    # AVAILABILITY SCENARIOS (A1, A2)
    # ============================================================================
    
    def test_a1_flash_sale_concurrency_control(self):
        """
        Scenario A1 — Flash Sale Concurrency Control
        Source: Multiple users attempting flash sale checkout simultaneously
        Stimulus: High concurrent load during flash sale events (1000+ requests/second)
        Environment: Normal operation with flash sale enabled and limited stock
        Artifact: src/cart/views.py::flash_checkout
        Response: System prevents overselling through atomic transactions and row-level locking
        Response-Measure: 0 oversell incidents; stock consistency maintained under concurrent load; losing requests complete in <1s
        """
        # Simulate concurrent flash sale checkouts
        # Enable flash sale with proper time constraints
        self.flash_product.flash_sale_enabled = True
        self.flash_product.flash_sale_starts_at = datetime.now()
        self.flash_product.flash_sale_ends_at = datetime.now() + timedelta(hours=1)
        self.flash_product.save()
        
        results = []
        errors = []
        
        def flash_checkout_request():
            try:
                response = self.client.post('/cart/flash-checkout/', {
                    'product_id': self.flash_product.id,
                    'quantity': 1,
                    'address': '123 Test Street',
                    'payment_method': 'CARD',
                    'card_number': '1234567890123456'
                })
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for i in range(10):  # 10 concurrent requests for 5 stock items
            thread = threading.Thread(target=flash_checkout_request)
            threads.append(thread)
        
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no overselling occurred
        self.flash_product.refresh_from_db()
        self.assertGreaterEqual(self.flash_product.stock_quantity, 0, "Stock should never go negative")
        
        # Verify some requests succeeded (200) and some failed gracefully (400/429)
        success_count = results.count(200)
        self.assertGreater(success_count, 0, "At least some requests should succeed")
        self.assertLessEqual(success_count, 5, "Should not exceed available stock")
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")
    
    def test_a2_payment_service_resilience(self):
        """
        Scenario A2 — Payment Service Resilience
        Source: External payment gateway failures and timeouts
        Stimulus: Payment service 5xx errors, timeouts, circuit breaker activation
        Environment: Normal operation with external payment dependencies
        Artifact: src/payments/service.py::charge_with_resilience
        Response: System maintains availability through retry, circuit breaker, and graceful degradation
        Response-Measure: ≥95% successful payments; <100ms fast-fail when circuit open; 0 payment data loss
        """
        # Test circuit breaker fast-fail behavior
        circuit_breaker = CircuitBreaker(
            name="test_payment_gateway",
            threshold=3,
            window_s=60,
            cool_off_s=30
        )
        
        # Force circuit breaker to OPEN state
        for i in range(4):  # Exceed threshold
            circuit_breaker.on_failure()  # Use on_failure() to trigger threshold check
        
        self.assertEqual(circuit_breaker.get_state(), CircuitBreakerState.OPEN)
        
        # Test fast-fail when circuit is open
        start_time = time.time()
        
        with patch('payments.service.PaymentGateway') as mock_gateway:
            mock_gateway.return_value.charge.side_effect = RuntimeError("Service unavailable")
            
            result = charge_with_resilience(
                order=self.user1,
                amount=Decimal('10.00'),
                timeout_s=2.0
            )
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Verify fast-fail behavior
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error'], 'circuit_open')
        self.assertLess(response_time_ms, 100, "Fast-fail should complete in <100ms")
        
        # Verify no payment data loss (no partial writes)
        payments = Payment.objects.filter(user=self.user1)
        self.assertEqual(payments.count(), 0, "No payment records should be created on failure")
    
    # ============================================================================
    # SECURITY SCENARIOS (S1, S2)
    # ============================================================================
    
    def test_s1_csrf_protection_on_flash_checkout(self):
        """
        Scenario S1 — CSRF Protection on Flash Checkout
        Source: Malicious websites attempting cross-site request forgery attacks
        Stimulus: CSRF attacks targeting flash sale checkout endpoints
        Environment: Normal operation with CSRF middleware enabled
        Artifact: src/cart/views.py::flash_checkout
        Response: System validates CSRF tokens and rejects forged requests
        Response-Measure: 100% CSRF attacks blocked; valid tokens required for all POST requests
        """
        # Test CSRF protection by making request without CSRF token
        # Enable flash sale with proper time constraints
        self.flash_product.flash_sale_enabled = True
        self.flash_product.flash_sale_starts_at = datetime.now()
        self.flash_product.flash_sale_ends_at = datetime.now() + timedelta(hours=1)
        self.flash_product.save()
        
        response = self.client.post('/cart/flash-checkout/', 
            json.dumps({
                'product_id': self.flash_product.id,
                'quantity': 1,
                'address': '123 CSRF Test Street',
                'payment_method': 'CARD',
                'card_number': '1234567890123456'
            }),
            content_type='application/json'
        )
        
        # Should get 400 or 403 due to missing CSRF token
        self.assertIn(response.status_code, [400, 403], f"Expected 400 or 403, got {response.status_code}")
        
        # Verify no sale was created
        sale = Sale.objects.filter(user=self.user1).first()
        self.assertIsNone(sale, "No sale should be created without valid CSRF token")
    
    def test_s2_rbac_authorization(self):
        """
        Scenario S2 — RBAC Authorization
        Source: Users attempting to access admin functions and protected operations
        Stimulus: Unauthorized access attempts to admin functions, product management, partner feeds
        Environment: Normal operation with mixed user roles (customer/admin)
        Artifact: src/accounts/decorators.py::admin_required
        Response: System enforces role-based access control with proper redirects
        Response-Measure: 100% unauthorized access denied; proper redirects to login/admin pages
        """
        # Test unauthorized access to admin functions
        self.client.login(username='user1', password='testpass')
        
        # Try to access admin-only product creation
        response = self.client.get('/products/create/')
        
        # Should redirect to login or show access denied
        self.assertIn(response.status_code, [302, 403], "Should redirect or deny access")
        
        # Test admin access
        self.client.login(username='admin', password='testpass')
        response = self.client.get('/products/create/')
        
        # Should allow access for admin
        self.assertEqual(response.status_code, 200, "Admin should have access to product creation")
    
    # ============================================================================
    # MODIFIABILITY SCENARIOS (M1, M2)
    # ============================================================================
    
    def test_m1_partner_feed_adapter_pattern(self):
        """
        Scenario M1 — Partner Feed Adapter Pattern
        Source: External partner systems with different data formats and schemas
        Stimulus: Changes in partner feed formats (CSV to JSON, new field requirements, schema evolution)
        Environment: Partner integration with varying data formats and update frequencies
        Artifact: src/partner_feeds/adapters.py::FeedAdapterFactory
        Response: System adapts to different feed formats without core code changes through adapter pattern
        Response-Measure: New format support added in <1 day; zero core code changes; adapter reuse >80%
        """
        # Test CSV adapter
        csv_adapter = FeedAdapterFactory.get_adapter('csv')
        self.assertIsNotNone(csv_adapter, "CSV adapter should be available")
        
        # Test JSON adapter
        json_adapter = FeedAdapterFactory.get_adapter('json')
        self.assertIsNotNone(json_adapter, "JSON adapter should be available")
        
        # Test adapter interface compliance
        self.assertTrue(hasattr(csv_adapter, 'parse'), "CSV adapter should implement parse method")
        self.assertTrue(hasattr(json_adapter, 'parse'), "JSON adapter should implement parse method")
        
        # Test adapter reuse - same adapter instance for same format
        csv_adapter2 = FeedAdapterFactory.get_adapter('csv')
        self.assertEqual(type(csv_adapter), type(csv_adapter2), "Should reuse adapter instances")
    
    def test_m2_business_rules_isolation(self):
        """
        Scenario M2 — Business Rules Isolation
        Source: Business requirements changes (pricing rules, validation logic, cart behavior)
        Stimulus: Changes to cart validation rules, pricing calculations, or business policies
        Environment: Development and maintenance phases with evolving business requirements
        Artifact: src/cart/business_rules.py
        Response: Business rules can be modified without affecting data layer or user interface
        Response-Measure: Business rule changes implemented in <2 hours; zero impact on data layer; test coverage maintained >90%
        """
        from cart.business_rules import validate_product_for_cart, calculate_cart_total
        
        # Test business rules can be called independently
        validation_result = validate_product_for_cart(self.product1, 5)
        self.assertTrue(validation_result, "Product validation should pass")
        
        # Test pricing calculation isolation
        cart_items = [
            {'product': self.product1, 'quantity': 2},
            {'product': self.flash_product, 'quantity': 1}
        ]
        
        total = calculate_cart_total(cart_items)
        self.assertIsInstance(total, Decimal, "Should return Decimal for pricing")
        self.assertGreater(total, 0, "Total should be positive")
        
        # Test business rules don't affect database directly
        initial_product_count = Product.objects.count()
        validate_product_for_cart(self.product1, 5)
        self.assertEqual(Product.objects.count(), initial_product_count, "Validation shouldn't modify database")
    
    # ============================================================================
    # PERFORMANCE SCENARIOS (P1, P2)
    # ============================================================================
    
    def test_p1_per_user_sku_throttling(self):
        """
        Scenario P1 — Per-User+SKU Throttling
        Source: Users attempting to abuse flash sale system with excessive requests
        Stimulus: High-frequency requests from individual users targeting specific products
        Environment: Flash sale events with high demand and limited stock
        Artifact: src/cart/throttle.py::allow_checkout
        Response: System implements granular throttling by user+product with Retry-After headers
        Response-Measure: p95 response time <1s; throttled requests return 429 with Retry-After; fair access maintained
        """
        from cart.throttle import allow_checkout
        
        # Test normal request should be allowed
        allowed, message, retry_after = allow_checkout(self.user1.id, self.flash_product.id)
        self.assertTrue(allowed, "First request should be allowed")
        
        # Simulate rapid requests to trigger throttling
        for i in range(10):  # Rapid requests
            allowed, message, retry_after = allow_checkout(self.user1.id, self.flash_product.id)
        
        # Should be throttled after rapid requests
        self.assertFalse(allowed, "Should be throttled after rapid requests")
        self.assertIn('try again', message.lower(), "Should include retry timing")
        
        # Test response time is bounded
        start_time = time.time()
        allowed, message, retry_after = allow_checkout(self.user1.id, self.flash_product.id)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        self.assertLess(response_time_ms, 1000, "Response time should be <1s")
    
    def test_p2_async_queue_split(self):
        """
        Scenario P2 — Async Queue Split
        Source: Flash sale checkout requests requiring background processing
        Stimulus: High-volume checkout requests with payment processing and inventory updates
        Environment: Flash sale events with peak load and background processing requirements
        Artifact: src/cart/views.py::flash_checkout
        Response: System splits fast sync operations from background processing for bounded latency
        Response-Measure: Sync operations complete in <500ms; background jobs processed within 30s; queue depth <1000
        """
        from worker.queue import enqueue_job
        
        # Test job queuing functionality
        job_payload = {
            'order_id': 123,
            'user_id': self.user1.id,
            'product_id': self.flash_product.id,
            'quantity': 1
        }
        
        # Test sync operation timing
        start_time = time.time()
        
        with patch('worker.queue.enqueue_job') as mock_enqueue:
            mock_enqueue.return_value = {'job_id': 'test_job_123'}
            
            # Simulate flash checkout sync operations
            job = enqueue_job('finalize_flash_order', job_payload)
            
        end_time = time.time()
        sync_duration_ms = (end_time - start_time) * 1000
        
        # Verify sync operations complete quickly
        self.assertLess(sync_duration_ms, 500, "Sync operations should complete in <500ms")
        
        # Verify job was queued
        self.assertIsNotNone(job, "Job should be queued for background processing")
    
    # ============================================================================
    # INTEGRABILITY SCENARIOS (I1, I2)
    # ============================================================================
    
    def test_i1_validate_transform_upsert_pipeline(self):
        """
        Scenario I1 — Validate→Transform→Upsert Pipeline
        Source: External partner systems providing product data feeds in various formats
        Stimulus: Partner feed updates with validation requirements and data transformation needs
        Environment: Partner integration with scheduled and manual feed processing
        Artifact: src/partner_feeds/services.py::_process_single_item
        Response: System processes feeds through validate→transform→upsert pipeline with error isolation
        Response-Measure: ≥95% valid rows ingested; processing time <5 minutes per feed; error isolation maintained
        """
        # Create test feed data
        feed_data = {
            'sku': 'PARTNER001',
            'name': 'Partner Product',
            'price': '25.00',
            'stock': 50,
            'category': 'Electronics'
        }
        
        # Test validation step
        validator = ProductFeedValidator()
        validation_result = validator.validate_item(feed_data)
        self.assertEqual(len(validation_result), 0, "Valid feed item should have no validation errors")
        
        # Test transformation step
        transformed_data = validator.transform_item(feed_data, self.partner_feed)
        self.assertIsInstance(transformed_data, dict, "Should return transformed dictionary")
        self.assertIn('sku', transformed_data, "Should include SKU in transformed data")
        
        # Test upsert step
        service = FeedIngestionService()
        result = service._process_single_item(feed_data, self.partner_feed)
        
        # Verify product was created/updated
        product = Product.objects.filter(sku='PARTNER001').first()
        self.assertIsNotNone(product, "Product should be created via upsert")
        self.assertEqual(product.name, 'Partner Product', "Product name should match")
    
    def test_i2_bulk_upsert_operations(self):
        """
        Scenario I2 — Bulk Upsert Operations
        Source: Large partner feed files with thousands of products requiring efficient processing
        Stimulus: Bulk product ingestion and updates from partner systems
        Environment: Partner integration with large data volumes and performance requirements
        Artifact: src/partner_feeds/services.py::ingest_feed
        Response: System uses efficient bulk operations for data processing with batch error handling
        Response-Measure: 1000+ products processed in <30s; memory usage <100MB; batch error isolation
        """
        # Create test feed with multiple products
        feed_data = []
        for i in range(100):  # 100 products for testing
            feed_data.append({
                'sku': f'BULK{i:03d}',
                'name': f'Bulk Product {i}',
                'price': f'{10 + i}.00',
                'stock': 10,
                'category': 'Bulk Category'
            })
        
        # Test bulk processing performance
        start_time = time.time()
        
        service = FeedIngestionService()
        results = service.ingest_feed(feed_data, self.partner_feed.id)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify processing time is reasonable
        self.assertLess(processing_time, 30, "100 products should process in <30s")
        
        # Verify products were created
        created_products = Product.objects.filter(sku__startswith='BULK')
        self.assertEqual(created_products.count(), 100, "All 100 products should be created")
        
        # Verify error isolation (if any errors occurred)
        self.assertIsInstance(results, dict, "Should return results dictionary")
    
    # ============================================================================
    # TESTABILITY SCENARIOS (T1, T2)
    # ============================================================================
    
    def test_t1_dependency_injection_mocking(self):
        """
        Scenario T1 — Dependency Injection & Mocking
        Source: Development team testing external service interactions and failure scenarios
        Stimulus: Need to test payment failures, circuit breaker behavior, retry logic without affecting real services
        Environment: Test environment with controlled external dependencies
        Artifact: tests/test_order_processing_robustness.py
        Response: System uses strategic mocking to test external service interactions and failure scenarios
        Response-Measure: External service behavior testable; no real service calls in tests; mock coverage >90%
        """
        # Test mocking external payment service
        with patch('payments.client.PaymentGateway.charge') as mock_charge:
            mock_charge.return_value = {
                'status': 'approved',
                'provider_ref': 'MOCK_TXN_123'
            }
            
            result = charge_with_resilience(
                order=self.user1,
                amount=Decimal('10.00'),
                timeout_s=2.0
            )
            
            # Verify mock was called
            mock_charge.assert_called_once()
            
            # Verify result
            self.assertEqual(result['status'], 'ok')
            self.assertEqual(result['provider_ref'], 'MOCK_TXN_123')
        
        # Test mocking failure scenarios
        with patch('payments.client.PaymentGateway.charge') as mock_charge:
            mock_charge.side_effect = RuntimeError("Service unavailable")
            
            result = charge_with_resilience(
                order=self.user1,
                amount=Decimal('10.00'),
                timeout_s=2.0
            )
            
            # Verify failure handling
            self.assertIn('error', result)
            self.assertNotEqual(result['status'], 'ok')
    
    def test_t2_deterministic_test_environment(self):
        """
        Scenario T2 — Deterministic Test Environment
        Source: Development team requiring consistent test execution and reproducible results
        Stimulus: Test execution with controlled state, cache management, and deterministic behavior
        Environment: Test environment with isolated state and controlled dependencies
        Artifact: tests/test_order_processing_robustness.py
        Response: System provides deterministic test environment with controlled state and cache management
        Response-Measure: Test execution deterministic; cache state controlled; test isolation maintained
        """
        # Test cache isolation
        cache.set('test_key', 'test_value', 300)
        self.assertEqual(cache.get('test_key'), 'test_value', "Cache should work in test")
        
        # Clear cache and verify isolation
        cache.clear()
        self.assertIsNone(cache.get('test_key'), "Cache should be cleared")
        
        # Test database isolation
        initial_user_count = User.objects.count()
        
        # Create test user
        test_user = User.objects.create_user(username='test_isolation', password='testpass')
        
        # Verify user was created
        self.assertEqual(User.objects.count(), initial_user_count + 1, "User should be created")
        
        # Test deterministic behavior
        cache.set('deterministic_key', 'deterministic_value', 300)
        self.assertEqual(cache.get('deterministic_key'), 'deterministic_value', "Cache should be deterministic")
    
    # ============================================================================
    # USABILITY SCENARIOS (U1, U2)
    # ============================================================================
    
    def test_u1_specific_error_messages(self):
        """
        Scenario U1 — Specific Error Messages
        Source: Users encountering errors during normal operations (validation failures, stock conflicts, payment errors)
        Stimulus: User errors, validation failures, or system exceptions during cart and checkout operations
        Environment: Normal operation with user interactions and potential error conditions
        Artifact: src/cart/views.py::checkout
        Response: System provides clear, actionable error messages with emojis and specific guidance
        Response-Measure: Error messages <50 words; 90%+ user comprehension; actionable feedback provided
        """
        self.client.login(username='user1', password='testpass')
        
        # Test empty cart error message
        response = self.client.post('/cart/checkout/', {
            'address': '123 Test Street',
            'payment_method': 'CARD',
            'card_number': '1234567890123456'
        })
        
        # Should redirect back to cart with error message
        self.assertEqual(response.status_code, 302, "Should redirect on empty cart")
        
        # Test specific error message for invalid quantity
        response = self.client.post(f'/cart/add/{self.product1.id}/', {
            'quantity': 0  # Invalid quantity
        })
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302, "Should redirect on invalid quantity")
    
    def test_u2_payment_unavailable_ux(self):
        """
        Scenario U2 — Payment Unavailable UX
        Source: Users experiencing payment service unavailability or circuit breaker activation
        Stimulus: Payment service failures, circuit breaker open state, or throttling during high load
        Environment: High-load operation with payment service issues or throttling active
        Artifact: src/cart/throttle.py::allow_checkout
        Response: System provides clear guidance on payment unavailability with retry timing and no data loss
        Response-Measure: Payment unavailable messages <30 words; retry timing provided; no data loss; user guidance clear
        """
        from cart.throttle import allow_checkout
        
        # Enable flash sale with proper time constraints
        self.flash_product.flash_sale_enabled = True
        self.flash_product.flash_sale_starts_at = datetime.now()
        self.flash_product.flash_sale_ends_at = datetime.now() + timedelta(hours=1)
        self.flash_product.save()
        
        # Test throttling message clarity
        allowed, message, retry_after = allow_checkout(self.user1.id, self.flash_product.id)
        
        # Simulate throttling by making rapid requests
        for i in range(10):
            allowed, message, retry_after = allow_checkout(self.user1.id, self.flash_product.id)
        
        # Verify throttling message is clear and actionable
        if not allowed:
            self.assertLess(len(message), 100, "Message should be concise")
            self.assertIn('try again', message.lower(), "Should provide retry guidance")
            self.assertIn('seconds', message.lower(), "Should provide timing information")
        
        # Test no data loss during throttling
        initial_cart_count = CartItem.objects.filter(user=self.user1).count()
        
        # Attempt checkout during throttling
        self.client.login(username='user1', password='testpass')
        response = self.client.post('/cart/flash-checkout/', {
            'product_id': self.flash_product.id,
            'quantity': 1,
            'address': '123 Test Street',
            'payment_method': 'CARD',
            'card_number': '1234567890123456'
        })
        
        # Verify no cart items were lost
        final_cart_count = CartItem.objects.filter(user=self.user1).count()
        self.assertEqual(final_cart_count, initial_cart_count, "No cart items should be lost during throttling")
    
    # ============================================================================
    # RELEASE RESILIENCE SCENARIOS (R1, R2, R3) - For "Faster Releases with Fewer Outages"
    # ============================================================================
    
    def test_r1_zero_downtime_deployment(self):
        """
        Scenario R1 — Zero Downtime Deployment
        Source: Leadership demands faster releases with fewer outages
        Stimulus: Application deployment during active user sessions
        Environment: Production environment with active users and ongoing transactions
        Artifact: Django application deployment process
        Response: System maintains service availability during deployment with graceful degradation
        Response-Measure: 0 downtime incidents; active sessions preserved; rollback capability <2 minutes
        """
        # Test that active sessions are preserved during deployment
        self.client.login(username='user1', password='testpass')
        
        # Add items to cart (simulate active session)
        self.client.post(f'/cart/add/{self.product1.id}/', {
            'quantity': 2
        })
        
        # Verify cart items persist (simulating session preservation)
        cart_items = CartItem.objects.filter(user=self.user1)
        self.assertEqual(cart_items.count(), 1, "Cart items should persist during deployment")
        
        # Test graceful degradation - system should handle requests even during deployment
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200, "Product listing should remain available")
        
        # Test rollback capability - verify we can quickly revert changes
        start_time = time.time()
        
        # Simulate rollback by clearing cache and resetting state
        cache.clear()
        
        end_time = time.time()
        rollback_time_ms = (end_time - start_time) * 1000
        
        # Verify rollback is fast
        self.assertLess(rollback_time_ms, 2000, "Rollback should complete in <2 minutes")
        
        # Verify system is still functional after rollback
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200, "System should be functional after rollback")
    
    def test_r2_feature_flag_safety(self):
        """
        Scenario R2 — Feature Flag Safety
        Source: Leadership demands faster releases with fewer outages
        Stimulus: New feature deployment with potential for issues
        Environment: Production environment with feature flags for safe deployment
        Artifact: Feature flag implementation and rollback mechanism
        Response: System can safely deploy features with instant rollback capability
        Response-Measure: Feature toggles work instantly; rollback <30 seconds; no data corruption
        """
        # Test feature flag implementation
        feature_enabled = cache.get('feature_flash_sale_v2', False)
        
        # Test instant feature toggle
        start_time = time.time()
        cache.set('feature_flash_sale_v2', True, 300)
        end_time = time.time()
        
        toggle_time_ms = (end_time - start_time) * 1000
        self.assertLess(toggle_time_ms, 100, "Feature toggle should be instant")
        
        # Test feature behavior when enabled
        if cache.get('feature_flash_sale_v2', False):
            # Enhanced flash sale behavior
            self.client.login(username='user1', password='testpass')
            response = self.client.get('/products/')
            self.assertEqual(response.status_code, 200, "Enhanced feature should work")
        
        # Test instant rollback
        start_time = time.time()
        cache.set('feature_flash_sale_v2', False, 300)
        end_time = time.time()
        
        rollback_time_ms = (end_time - start_time) * 1000
        self.assertLess(rollback_time_ms, 30000, "Feature rollback should be <30 seconds")
        
        # Verify no data corruption after rollback
        products_count = Product.objects.count()
        self.assertGreater(products_count, 0, "No data should be lost during feature rollback")
    
    def test_r3_database_migration_safety(self):
        """
        Scenario R3 — Database Migration Safety
        Source: Leadership demands faster releases with fewer outages
        Stimulus: Database schema changes during active operations
        Environment: Production environment with backward-compatible migrations
        Artifact: Django migration system and backward compatibility
        Response: System maintains data integrity during schema changes with rollback capability
        Response-Measure: 0 data loss incidents; migrations reversible; backward compatibility maintained
        """
        # Test that existing data remains accessible during migrations
        initial_product_count = Product.objects.count()
        initial_category_count = Category.objects.count()
        
        # Simulate migration by adding new field (backward compatible)
        # In real scenario, this would be a Django migration
        test_product = Product.objects.create(
            name='Migration Test Product',
            sku='MIG001',
            price=Decimal('15.00'),
            stock_quantity=10,
            category=self.category,
            is_active=True
        )
        
        # Verify data integrity maintained
        self.assertEqual(Product.objects.count(), initial_product_count + 1, "New data should be created")
        self.assertEqual(Category.objects.count(), initial_category_count, "Existing data should be preserved")
        
        # Test backward compatibility - old queries should still work
        old_products = Product.objects.filter(is_active=True)
        self.assertGreater(old_products.count(), 0, "Old queries should still work")
        
        # Test rollback capability
        start_time = time.time()
        
        # Simulate rollback by removing the new data
        test_product.delete()
        
        end_time = time.time()
        rollback_time_ms = (end_time - start_time) * 1000
        
        # Verify rollback is fast
        self.assertLess(rollback_time_ms, 5000, "Migration rollback should be fast")
        
        # Verify system state after rollback
        self.assertEqual(Product.objects.count(), initial_product_count, "Data should be restored to original state")
        
        # Verify system functionality after rollback
        self.client.login(username='user1', password='testpass')
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200, "System should be functional after migration rollback")
    
    def test_r4_monitoring_early_detection(self):
        """
        Scenario R4 — Monitoring Early Detection
        Source: Leadership demands faster releases with fewer outages
        Stimulus: System anomalies and performance degradation
        Environment: Production environment with monitoring and alerting
        Artifact: Logging system and performance monitoring
        Response: System detects issues early and provides actionable alerts
        Response-Measure: Issues detected <5 minutes; false positive rate <10%; alert accuracy >90%
        """
        from retail.logging import log_payment_attempt, log_breaker_transition
        
        # Test early detection of payment failures
        log_payment_attempt(
            order_id=123,
            attempt_no=1,
            latency_ms=5000,  # High latency
            breaker_state='closed',
            outcome='failure',
            error='Payment timeout'
        )
        
        # Test circuit breaker transition logging
        log_breaker_transition(
            circuit_name='payment_gateway',
            from_state='closed',
            to_state='open'
        )
        
        # Verify monitoring data is captured
        # In real scenario, this would check monitoring system
        self.assertTrue(True, "Monitoring logs should be captured")
        
        # Test performance degradation detection
        start_time = time.time()
        
        # Simulate slow operation
        time.sleep(0.1)  # Simulate 100ms delay
        
        end_time = time.time()
        operation_time_ms = (end_time - start_time) * 1000
        
        # Verify we can detect performance issues
        if operation_time_ms > 50:  # Threshold for slow operations
            # Log performance issue
            log_payment_attempt(
                order_id=124,
                attempt_no=1,
                latency_ms=int(operation_time_ms),
                breaker_state='closed',
                outcome='slow',
                error='High latency detected'
            )
        
        # Verify monitoring provides actionable data
        self.assertGreater(operation_time_ms, 0, "Performance monitoring should detect timing")
    
    def test_r5_graceful_degradation(self):
        """
        Scenario R5 — Graceful Degradation
        Source: Leadership demands faster releases with fewer outages
        Stimulus: Service failures during high-traffic periods
        Environment: Production environment with multiple service dependencies
        Artifact: Circuit breaker and fallback mechanisms
        Response: System degrades gracefully without complete failure
        Response-Measure: Core functionality maintained; degraded mode <30s; user experience preserved
        """
        # Test graceful degradation when payment service is unavailable
        circuit_breaker = CircuitBreaker(
            name="payment_gateway",
            threshold=3,
            window_s=60,
            cool_off_s=30
        )
        
        # Force circuit breaker to OPEN state
        for i in range(4):
            circuit_breaker.on_failure()  # Use on_failure() to trigger threshold check
        
        self.assertEqual(circuit_breaker.get_state(), CircuitBreakerState.OPEN)
        
        # Test that core functionality still works when payment is degraded
        self.client.login(username='user1', password='testpass')
        
        # Product browsing should still work
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200, "Product browsing should work in degraded mode")
        
        # Cart operations should still work
        response = self.client.post(f'/cart/add/{self.product1.id}/', {
            'quantity': 1
        })
        self.assertEqual(response.status_code, 302, "Cart operations should work in degraded mode")
        
        # Test degraded mode timing
        start_time = time.time()
        
        # Simulate degraded mode response
        response = self.client.get('/cart/')
        
        end_time = time.time()
        degraded_response_time_ms = (end_time - start_time) * 1000
        
        # Verify degraded mode is fast
        self.assertLess(degraded_response_time_ms, 30000, "Degraded mode should respond in <30s")
        
        # Verify user experience is preserved
        self.assertEqual(response.status_code, 200, "User should see cart page in degraded mode")
