"""
Unit tests for CART DATABASE INTEGRATION in the retail management system.
Tests cart operations that integrate with the database layer.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from unittest.mock import Mock


class CartItemDatabaseTest(TestCase):
    """Test CartItem model database operations"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Store test data for creating objects in each test
        self.category_data = {
            'name': 'Test Category',
            'description': 'Test category description'
        }
        
        self.product_data = {
            'name': 'Test Product',
            'description': 'Test product description',
            'sku': 'TEST001',
            'price': Decimal('29.99'),
            'stock_quantity': 10,
            'is_active': True
        }

    def test_cart_item_creation_with_database(self):
        """DATABASE INTEGRATION: Test creating CartItem with database storage"""
        from products.models import Category, Product
        from cart.models import CartItem
        
        # Create test category and product
        category = Category.objects.create(**self.category_data)
        product = Product.objects.create(category=category, **self.product_data)
        
        cart_item = CartItem.objects.create(
            product=product,
            quantity=3,
            user=self.user
        )
        
        # Verify database storage
        self.assertEqual(cart_item.product, product)
        self.assertEqual(cart_item.quantity, 3)
        self.assertEqual(cart_item.user, self.user)
        self.assertTrue(cart_item.created_at)
        self.assertTrue(cart_item.updated_at)
        
        # Verify it exists in database
        self.assertTrue(CartItem.objects.filter(
            product=product,
            user=self.user
        ).exists())

    def test_cart_item_total_price_calculation_with_database(self):
        """DATABASE INTEGRATION: Test total_price property with database values"""
        from products.models import Category, Product
        from cart.models import CartItem
        
        # Create test category and product
        category = Category.objects.create(**self.category_data)
        product = Product.objects.create(category=category, **self.product_data)
        
        cart_item = CartItem.objects.create(
            product=product,
            quantity=2,
            user=self.user
        )
        
        # Test total_price calculation
        expected_total = product.price * 2
        self.assertEqual(cart_item.total_price, expected_total)
        self.assertEqual(cart_item.total_price, Decimal('59.98'))

    def test_cart_item_unique_constraint_with_database(self):
        """DATABASE INTEGRATION: Test unique constraint on product + session_key + user combination"""
        from products.models import Category, Product
        from cart.models import CartItem
        from django.db import IntegrityError
        
        # Create test category and product
        category = Category.objects.create(**self.category_data)
        product = Product.objects.create(category=category, **self.product_data)
        
        # Create first cart item with session_key
        CartItem.objects.create(
            product=product,
            quantity=1,
            user=self.user,
            session_key='test_session_123'
        )
        
        # Try to create duplicate with same product, user, and session_key - should raise IntegrityError
        with self.assertRaises(IntegrityError):
            CartItem.objects.create(
                product=product,
                quantity=2,
                user=self.user,
                session_key='test_session_123'  # Same session_key
            )

    def test_cart_item_string_representation_with_database(self):
        """DATABASE INTEGRATION: Test string representation of CartItem"""
        from products.models import Category, Product
        from cart.models import CartItem
        
        # Create test category and product
        category = Category.objects.create(**self.category_data)
        product = Product.objects.create(category=category, **self.product_data)
        
        cart_item = CartItem.objects.create(
            product=product,
            quantity=5,
            user=self.user
        )
        
        expected_str = f"5 x {product.name}"
        self.assertEqual(str(cart_item), expected_str)


class CartDatabaseIntegrationTest(TestCase):
    """Test Cart class database integration for logged-in users"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Store test data for creating objects in each test
        self.category_data = {
            'name': 'Test Category',
            'description': 'Test category description'
        }
        
        self.product1_data = {
            'name': 'Product 1',
            'description': 'Test product 1',
            'sku': 'PROD001',
            'price': Decimal('19.99'),
            'stock_quantity': 5,
            'is_active': True
        }
        
        self.product2_data = {
            'name': 'Product 2',
            'description': 'Test product 2',
            'sku': 'PROD002',
            'price': Decimal('39.99'),
            'stock_quantity': 3,
            'is_active': True
        }
        
        # Create mock request with user
        self.request = Mock()
        self.request.user = self.user
        
        # Create a proper mock session that behaves like Django session
        self.request.session = Mock()
        self.request.session.session_key = 'test_session_key'
        self.request.session.get = Mock(return_value={})
        self.request.session.modified = False
        self.request.session.__setitem__ = Mock()  # Support session['cart'] = {}
        self.request.session.__getitem__ = Mock(return_value={})  # Support session['cart']

    def test_cart_add_with_database_storage(self):
        """DATABASE INTEGRATION: Test adding products to cart with database storage"""
        from products.models import Category, Product
        from cart.models import Cart, CartItem
        
        # Create test category and products
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        product2 = Product.objects.create(category=category, **self.product2_data)
        
        cart = Cart(self.request)
        
        # Add first product
        cart.add(product1, quantity=2)
        
        # Verify database storage
        cart_item = CartItem.objects.get(product=product1, user=self.user)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.user, self.user)
        
        # Add second product
        cart.add(product2, quantity=1)
        
        # Verify both items in database
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 2)
        
        # Verify quantities
        item1 = CartItem.objects.get(product=product1, user=self.user)
        item2 = CartItem.objects.get(product=product2, user=self.user)
        self.assertEqual(item1.quantity, 2)
        self.assertEqual(item2.quantity, 1)

    def test_cart_update_with_database_storage(self):
        """DATABASE INTEGRATION: Test updating cart quantities with database storage"""
        from products.models import Category, Product
        from cart.models import Cart, CartItem
        
        # Create test category and product
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        
        cart = Cart(self.request)
        
        # Add product
        cart.add(product1, quantity=2)
        
        # Update quantity
        cart.update(product1, quantity=4)
        
        # Verify database update
        cart_item = CartItem.objects.get(product=product1, user=self.user)
        self.assertEqual(cart_item.quantity, 4)
        
        # Update to 0 (should remove from database)
        cart.update(product1, quantity=0)
        
        # Verify removal from database
        self.assertFalse(CartItem.objects.filter(
            product=product1,
            user=self.user
        ).exists())

    def test_cart_remove_with_database_storage(self):
        """DATABASE INTEGRATION: Test removing products from cart with database storage"""
        from products.models import Category, Product
        from cart.models import Cart, CartItem
        
        # Create test category and products
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        product2 = Product.objects.create(category=category, **self.product2_data)
        
        cart = Cart(self.request)
        
        # Add products
        cart.add(product1, quantity=2)
        cart.add(product2, quantity=1)
        
        # Verify both in database
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 2)
        
        # Remove first product
        cart.remove(product1)
        
        # Verify removal from database
        self.assertFalse(CartItem.objects.filter(
            product=product1,
            user=self.user
        ).exists())
        
        # Verify second product still exists
        self.assertTrue(CartItem.objects.filter(
            product=product2,
            user=self.user
        ).exists())

    def test_cart_clear_with_database_storage(self):
        """DATABASE INTEGRATION: Test clearing cart with database storage"""
        from products.models import Category, Product
        from cart.models import Cart, CartItem
        
        # Create test category and products
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        product2 = Product.objects.create(category=category, **self.product2_data)
        
        cart = Cart(self.request)
        
        # Add multiple products
        cart.add(product1, quantity=2)
        cart.add(product2, quantity=1)
        
        # Verify items in database
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 2)
        
        # Clear cart
        cart.clear()
        
        # Verify all items removed from database
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

    def test_cart_iteration_with_database_storage(self):
        """DATABASE INTEGRATION: Test cart iteration with database storage"""
        from products.models import Category, Product
        from cart.models import Cart
        
        # Create test category and products
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        product2 = Product.objects.create(category=category, **self.product2_data)
        
        cart = Cart(self.request)
        
        # Add products
        cart.add(product1, quantity=2)
        cart.add(product2, quantity=1)
        
        # Test iteration
        items = list(cart)
        self.assertEqual(len(items), 2)
        
        # Verify item structure
        for item in items:
            self.assertIn('product', item)
            self.assertIn('quantity', item)
            self.assertIn('price', item)
            self.assertIn('total_price', item)
        
        # Verify specific values
        product1_item = next(item for item in items if item['product'] == product1)
        self.assertEqual(product1_item['quantity'], 2)
        self.assertEqual(product1_item['total_price'], Decimal('39.98'))

    def test_cart_length_with_database_storage(self):
        """DATABASE INTEGRATION: Test cart length calculation with database storage"""
        from products.models import Category, Product
        from cart.models import Cart
        
        # Create test category and products
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        product2 = Product.objects.create(category=category, **self.product2_data)
        
        cart = Cart(self.request)
        
        # Initially empty
        self.assertEqual(len(cart), 0)
        
        # Add products
        cart.add(product1, quantity=2)
        cart.add(product2, quantity=3)
        
        # Test length
        self.assertEqual(len(cart), 5)  # 2 + 3 = 5 total items

    def test_cart_total_price_with_database_storage(self):
        """DATABASE INTEGRATION: Test cart total price calculation with database storage"""
        from products.models import Category, Product
        from cart.models import Cart
        
        # Create test category and products
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        product2 = Product.objects.create(category=category, **self.product2_data)
        
        cart = Cart(self.request)
        
        # Initially zero
        self.assertEqual(cart.get_total_price(), 0)
        
        # Add products
        cart.add(product1, quantity=2)  # 2 * 19.99 = 39.98
        cart.add(product2, quantity=1)  # 1 * 39.99 = 39.99
        
        # Test total price
        expected_total = Decimal('39.98') + Decimal('39.99')
        self.assertEqual(cart.get_total_price(), expected_total)
        self.assertEqual(cart.get_total_price(), Decimal('79.97'))

    def test_cart_stock_validation_with_database(self):
        """DATABASE INTEGRATION: Test stock validation with database queries"""
        from products.models import Category, Product
        from cart.models import Cart, CartItem
        
        # Create test category and product
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        
        cart = Cart(self.request)
        
        # Try to add more than available stock
        with self.assertRaises(ValueError) as context:
            cart.add(product1, quantity=10)  # Only 5 available
        
        self.assertIn("Only 5 available in stock", str(context.exception))
        
        # Verify no item was created in database (stock validation happens before creation)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)
        
        # Add valid quantity
        cart.add(product1, quantity=3)
        
        # Verify item created in database
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 1)
        cart_item = CartItem.objects.get(product=product1, user=self.user)
        self.assertEqual(cart_item.quantity, 3)

    def test_cart_inactive_product_validation_with_database(self):
        """DATABASE INTEGRATION: Test validation for inactive products with database"""
        from products.models import Category, Product
        from cart.models import Cart, CartItem
        
        # Create test category and product
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        
        cart = Cart(self.request)
        
        # Make product inactive
        product1.is_active = False
        product1.save()
        
        # Try to add inactive product
        with self.assertRaises(ValueError) as context:
            cart.add(product1, quantity=1)
        
        self.assertIn("not available for purchase", str(context.exception))
        
        # Verify no item was created in database
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

    def test_checkout_purchase_happy_path_with_database(self):
        """DATABASE INTEGRATION: Test complete checkout/purchase flow with atomic operations"""
        from products.models import Category, Product
        from cart.models import Cart, CartItem
        from orders.models import Sale, SaleItem, Payment
        from retail.payment import process_payment
        
        # Create test category and products
        category = Category.objects.create(**self.category_data)
        product1 = Product.objects.create(category=category, **self.product1_data)
        product2 = Product.objects.create(category=category, **self.product2_data)
        
        # Record initial stock levels
        initial_stock1 = product1.stock_quantity
        initial_stock2 = product2.stock_quantity
        
        cart = Cart(self.request)
        
        # Add products to cart
        cart.add(product1, quantity=2)  # 2 * 19.99 = 39.98
        cart.add(product2, quantity=1)  # 1 * 39.99 = 39.99
        total_cart_value = Decimal('79.97')
        
        # Verify cart has items
        self.assertEqual(len(cart), 3)
        self.assertEqual(cart.get_total_price(), total_cart_value)
        
        # Simulate checkout process (atomic transaction)
        from django.db import transaction
        
        with transaction.atomic():
            # Create sale record
            sale = Sale.objects.create(
                user=self.user,
                address="123 Test Street, Test City",
                total=total_cart_value,
                status="COMPLETED"
            )
            
            # Create sale items and decrement stock atomically
            for cart_item in CartItem.objects.filter(user=self.user):
                SaleItem.objects.create(
                    sale=sale,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.product.price
                )
                
                # Decrement stock atomically
                cart_item.product.stock_quantity -= cart_item.quantity
                cart_item.product.save()
            
            # Process payment (mock)
            payment_result = process_payment("CARD", float(total_cart_value), "1234567890123456")
            
            # Create payment record
            Payment.objects.create(
                sale=sale,
                method="CARD",
                reference=payment_result.get("reference", "TXN123456"),
                amount=total_cart_value,
                status="COMPLETED" if payment_result["status"] == "approved" else "FAILED"
            )
            
            # Clear cart after successful checkout
            cart.clear()
        
        # Verify sale was persisted
        self.assertTrue(Sale.objects.filter(user=self.user).exists())
        sale = Sale.objects.get(user=self.user)
        self.assertEqual(sale.total, total_cart_value)
        self.assertEqual(sale.status, "COMPLETED")
        
        # Verify sale items were created
        sale_items = SaleItem.objects.filter(sale=sale)
        self.assertEqual(sale_items.count(), 2)
        
        # Verify stock was decremented atomically
        product1.refresh_from_db()
        product2.refresh_from_db()
        self.assertEqual(product1.stock_quantity, initial_stock1 - 2)  # 5 - 2 = 3
        self.assertEqual(product2.stock_quantity, initial_stock2 - 1)  # 3 - 1 = 2
        
        # Verify payment was recorded
        payment = Payment.objects.get(sale=sale)
        self.assertEqual(payment.amount, total_cart_value)
        self.assertEqual(payment.method, "CARD")
        
        # Verify cart was cleared
        self.assertEqual(len(cart), 0)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)
        
        # Verify sale item calculations
        total_sale_value = sum(item.subtotal() for item in sale_items)
        self.assertEqual(total_sale_value, total_cart_value)