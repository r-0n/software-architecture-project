"""
Enhanced test suite for flash sale pricing logic.
Tests active vs inactive windows, invalid configurations, and price consistency.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from products.models import Product, Category
from products.services import is_flash_sale_active, current_effective_price, validate_price_consistency


class FlashPricingTestCase(TestCase):
    """Test flash sale pricing logic"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="Test Category",
            description="Test category for flash sales"
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            description="Test product for flash sales",
            sku="TEST-001",
            price=Decimal('100.00'),
            category=self.category,
            stock_quantity=10,
            is_active=True
        )
        
        self.now = timezone.now()
        self.start_time = self.now - timedelta(hours=1)
        self.end_time = self.now + timedelta(hours=1)
    
    def test_flash_sale_inactive_when_disabled(self):
        """Test that flash sale is inactive when disabled"""
        self.product.flash_sale_enabled = False
        self.product.save()
        
        self.assertFalse(is_flash_sale_active(self.product))
        self.assertEqual(current_effective_price(self.product), Decimal('100.00'))
    
    def test_flash_sale_inactive_when_no_price(self):
        """Test that flash sale is inactive when no flash price set"""
        self.product.flash_sale_enabled = True
        self.product.flash_sale_price = None
        self.product.flash_sale_starts_at = self.start_time
        self.product.flash_sale_ends_at = self.end_time
        self.product.save()
        
        self.assertFalse(is_flash_sale_active(self.product))
        self.assertEqual(current_effective_price(self.product), Decimal('100.00'))
    
    def test_flash_sale_inactive_before_window(self):
        """Test that flash sale is inactive before start time"""
        self.product.flash_sale_enabled = True
        self.product.flash_sale_price = Decimal('50.00')
        self.product.flash_sale_starts_at = self.now + timedelta(hours=1)
        self.product.flash_sale_ends_at = self.now + timedelta(hours=2)
        self.product.save()
        
        self.assertFalse(is_flash_sale_active(self.product))
        self.assertEqual(current_effective_price(self.product), Decimal('100.00'))
    
    def test_flash_sale_inactive_after_window(self):
        """Test that flash sale is inactive after end time"""
        self.product.flash_sale_enabled = True
        self.product.flash_sale_price = Decimal('50.00')
        self.product.flash_sale_starts_at = self.now - timedelta(hours=2)
        self.product.flash_sale_ends_at = self.now - timedelta(hours=1)
        self.product.save()
        
        self.assertFalse(is_flash_sale_active(self.product))
        self.assertEqual(current_effective_price(self.product), Decimal('100.00'))
    
    def test_flash_sale_active_during_window(self):
        """Test that flash sale is active during window"""
        self.product.flash_sale_enabled = True
        self.product.flash_sale_price = Decimal('50.00')
        self.product.flash_sale_starts_at = self.start_time
        self.product.flash_sale_ends_at = self.end_time
        self.product.save()
        
        self.assertTrue(is_flash_sale_active(self.product))
        self.assertEqual(current_effective_price(self.product), Decimal('50.00'))
    
    def test_price_consistency_validation(self):
        """Test price consistency validation between add-to-cart and checkout"""
        self.product.flash_sale_enabled = True
        self.product.flash_sale_price = Decimal('50.00')
        self.product.flash_sale_starts_at = self.start_time
        self.product.flash_sale_ends_at = self.end_time
        self.product.save()
        
        add_to_cart_time = self.now
        checkout_time = self.now + timedelta(minutes=5)
        expected_price = Decimal('50.00')
        
        # Should be consistent during flash sale window
        self.assertTrue(validate_price_consistency(
            self.product, add_to_cart_time, checkout_time, expected_price
        ))
        
        # Should be inconsistent if price changes
        self.assertFalse(validate_price_consistency(
            self.product, add_to_cart_time, checkout_time, Decimal('100.00')
        ))
    
    def test_model_validation_flash_sale_enabled(self):
        """Test model validation when flash sale is enabled"""
        self.product.flash_sale_enabled = True
        self.product.flash_sale_price = None  # Missing price
        self.product.flash_sale_starts_at = self.start_time
        self.product.flash_sale_ends_at = self.end_time
        
        with self.assertRaises(Exception):  # ValidationError
            self.product.full_clean()
    
    def test_model_validation_time_order(self):
        """Test model validation for time order"""
        self.product.flash_sale_enabled = True
        self.product.flash_sale_price = Decimal('50.00')
        self.product.flash_sale_starts_at = self.end_time  # Start after end
        self.product.flash_sale_ends_at = self.start_time
        
        with self.assertRaises(Exception):  # ValidationError
            self.product.full_clean()
    
    def test_conditional_constraint_allows_partial_config(self):
        """Test that conditional constraint allows partial configuration when disabled"""
        self.product.flash_sale_enabled = False
        self.product.flash_sale_price = None
        self.product.flash_sale_starts_at = None
        self.product.flash_sale_ends_at = None
        
        # Should not raise validation error
        self.product.full_clean()
        self.product.save()
        
        # Should still work
        self.assertFalse(is_flash_sale_active(self.product))
        self.assertEqual(current_effective_price(self.product), Decimal('100.00'))
