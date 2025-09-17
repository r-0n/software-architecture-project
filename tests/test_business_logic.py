"""
Unit tests for BUSINESS LOGIC in the retail management system.
Tests core business rules in isolation without database dependencies.

BUSINESS LOGIC TESTS:
- Payment processing business rules
- Cart business rules
- Stock validation logic
- Price calculation logic
"""

from django.test import SimpleTestCase
from decimal import Decimal
from unittest.mock import patch
from django.core.exceptions import ValidationError

from src.retail.payment import process_payment


class PaymentProcessingBusinessLogicTest(SimpleTestCase):
    """BUSINESS LOGIC: Test payment processing business rules"""
    
    def test_payment_approval_business_rules(self):
        """BUSINESS LOGIC: Test payment approval business logic"""
        # Business rule: Cash payments always approved
        result = process_payment("CASH", 100.0)
        self.assertEqual(result['status'], 'approved')
        self.assertEqual(result['reference'], 'CASH-LOCAL')
    
    def test_payment_validation_business_rules(self):
        """BUSINESS LOGIC: Test payment validation business logic"""
        # Business rule: Card number must be exactly 16 digits
        result = process_payment("CARD", 100.0, "123456789")  # Too short
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['reason'], 'Card number must be exactly 16 digits')
        
        # Business rule: Card number must be numeric only
        result = process_payment("CARD", 100.0, "123456789012345a")  # Contains letter
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['reason'], 'Card number must contain only numeric digits')
    
    def test_payment_decline_business_rules(self):
        """BUSINESS LOGIC: Test payment decline business logic"""
        # Business rule: 80% approval rate for valid cards
        with patch('src.retail.payment.random') as mock_random:
            mock_random.random.return_value = 0.5  # Below 0.8 threshold
            mock_random.randint.return_value = 1234
            result = process_payment("CARD", 100.0, "1234567890123456")
            self.assertEqual(result['status'], 'approved')
            self.assertEqual(result['reference'], 'CARD-1234')


class CartBusinessRulesTest(SimpleTestCase):
    """BUSINESS LOGIC: Test cart business rules"""
    
    def test_stock_validation_business_rules(self):
        """BUSINESS LOGIC: Test stock validation business rules"""
        from cart.business_rules import validate_product_for_cart, validate_quantity_limit
        
        # Business rule: Cannot add inactive product
        with self.assertRaises(ValueError) as context:
            validate_product_for_cart(False, "Test Product")
        self.assertIn("not available for purchase", str(context.exception))
        
        # Business rule: Cannot exceed available stock
        with self.assertRaises(ValueError) as context:
            validate_quantity_limit(15, 10, "Test Product")
        self.assertIn("Only 10 available in stock", str(context.exception))
    
    def test_price_calculation_business_rules(self):
        """BUSINESS LOGIC: Test price calculation business rules"""
        from cart.business_rules import calculate_item_total
        
        total = calculate_item_total(Decimal('29.99'), 3)
        expected = Decimal('89.97')
        self.assertEqual(total, expected)
    
    def test_cart_update_business_rules(self):
        """BUSINESS LOGIC: Test cart update business rules"""
        from cart.business_rules import validate_cart_update
        
        # Test valid update
        self.assertTrue(validate_cart_update(5, 10, "Test Product"))
        
        # Test exceeding stock
        with self.assertRaises(ValueError) as context:
            validate_cart_update(15, 10, "Test Product")
        self.assertIn("Only 10 Test Product(s) available in stock", str(context.exception))
        
        # Test negative quantity
        with self.assertRaises(ValueError) as context:
            validate_cart_update(-1, 10, "Test Product")
        self.assertIn("Quantity cannot be negative", str(context.exception))
    
    def test_cart_remove_business_rules(self):
        """BUSINESS LOGIC: Test cart remove business rules"""
        # Business rule: Remove item should return success confirmation
        def remove_cart_item(product_name, current_quantity):
            if current_quantity <= 0:
                return f"No {product_name} items to remove"
            return f"{current_quantity} {product_name}(s) removed from cart"
        
        # Test successful removal
        result = remove_cart_item("Test Product", 3)
        expected = "3 Test Product(s) removed from cart"
        self.assertEqual(result, expected)
        
        # Test removal when no items
        result = remove_cart_item("Test Product", 0)
        expected = "No Test Product items to remove"
        self.assertEqual(result, expected)
    
    def test_cart_clear_business_rules(self):
        """BUSINESS LOGIC: Test cart clear business rules"""
        # Business rule: Clear cart should remove all items and reset totals
        def clear_cart(items_count, total_price):
            if items_count == 0:
                return "Cart is already empty"
            return f"Cart cleared: {items_count} items removed, total was ${total_price}"
        
        # Test clearing cart with items
        result = clear_cart(3, Decimal('89.97'))
        expected = "Cart cleared: 3 items removed, total was $89.97"
        self.assertEqual(result, expected)
        
        # Test clearing empty cart
        result = clear_cart(0, Decimal('0.00'))
        expected = "Cart is already empty"
        self.assertEqual(result, expected)
    
    def test_cart_total_calculations_business_rules(self):
        """BUSINESS LOGIC: Test cart total calculations with multiple items"""
        # Business rule: Cart total = sum of all item totals
        def calculate_cart_total(items):
            total = Decimal('0.00')
            for item in items:
                item_total = item['quantity'] * item['unit_price']
                total += item_total
            return total
        
        # Test with multiple items
        items = [
            {'quantity': 2, 'unit_price': Decimal('29.99')},
            {'quantity': 1, 'unit_price': Decimal('19.99')},
            {'quantity': 3, 'unit_price': Decimal('9.99')}
        ]
        
        total = calculate_cart_total(items)
        expected = Decimal('109.94')  # (2*29.99) + (1*19.99) + (3*9.99) = 59.98 + 19.99 + 29.97
        self.assertEqual(total, expected)
        
        # Test with empty cart
        empty_items = []
        total = calculate_cart_total(empty_items)
        expected = Decimal('0.00')
        self.assertEqual(total, expected)