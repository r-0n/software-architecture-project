from django.db import models
from products.models import Product


class CartItem(models.Model):
    """Individual item in the shopping cart"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'session_key', 'user']
        ordering = ['created_at']

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        return self.product.price * self.quantity


class Cart:
    """Shopping cart utility class for session and database-based cart management"""
    
    def __init__(self, request):
        self.session = request.session
        self.user = request.user if request.user.is_authenticated else None
        self.session_key = request.session.session_key
        
        # Get or create cart in session
        cart = self.session.get('cart', {})
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        """Add product to cart with stock validation"""
        # Check if product is active and has stock
        if not product.is_active:
            raise ValueError(f"Product {product.name} is not available for purchase")
        
        if product.stock_quantity <= 0:
            raise ValueError(f"Product {product.name} is out of stock")
        
        if self.user:
            # User is logged in - use database storage
            cart_item, created = CartItem.objects.get_or_create(
                product=product,
                user=self.user,
                defaults={'quantity': quantity}
            )
            if not created:
                new_quantity = cart_item.quantity + quantity
                if new_quantity > product.stock_quantity:
                    raise ValueError(f"Cannot add {quantity} more {product.name}(s). Only {product.stock_quantity} available in stock.")
                cart_item.quantity = new_quantity
                cart_item.save()
            else:
                if quantity > product.stock_quantity:
                    raise ValueError(f"Cannot add {quantity} {product.name}(s). Only {product.stock_quantity} available in stock.")
        else:
            # Anonymous user - use session storage
            product_id = str(product.id)
            
            if product_id in self.cart:
                new_quantity = self.cart[product_id]['quantity'] + quantity
                if new_quantity > product.stock_quantity:
                    raise ValueError(f"Cannot add {quantity} more {product.name}(s). Only {product.stock_quantity} available in stock.")
                self.cart[product_id]['quantity'] = new_quantity
            else:
                if quantity > product.stock_quantity:
                    raise ValueError(f"Cannot add {quantity} {product.name}(s). Only {product.stock_quantity} available in stock.")
                self.cart[product_id] = {
                    'quantity': quantity,
                    'price': str(product.price)
                }
            
            self.save()

    def remove(self, product):
        """Remove product from cart"""
        if self.user:
            # User is logged in - use database storage
            try:
                cart_item = CartItem.objects.get(product=product, user=self.user)
                cart_item.delete()
            except CartItem.DoesNotExist:
                pass
        else:
            # Anonymous user - use session storage
            product_id = str(product.id)
            if product_id in self.cart:
                del self.cart[product_id]
                self.save()

    def update(self, product, quantity):
        """Update product quantity in cart with stock validation"""
        # Check if product is active and has stock
        if not product.is_active:
            raise ValueError(f"Product {product.name} is not available for purchase")
        
        if product.stock_quantity <= 0:
            raise ValueError(f"Product {product.name} is out of stock")
        
        if quantity > product.stock_quantity:
            raise ValueError(f"Cannot update quantity to {quantity}. Only {product.stock_quantity} {product.name}(s) available in stock.")
        
        if self.user:
            # User is logged in - use database storage
            try:
                cart_item = CartItem.objects.get(product=product, user=self.user)
                if quantity <= 0:
                    cart_item.delete()
                else:
                    cart_item.quantity = quantity
                    cart_item.save()
            except CartItem.DoesNotExist:
                if quantity > 0:
                    CartItem.objects.create(product=product, user=self.user, quantity=quantity)
        else:
            # Anonymous user - use session storage
            product_id = str(product.id)
            if product_id in self.cart:
                if quantity <= 0:
                    self.remove(product)
                else:
                    self.cart[product_id]['quantity'] = quantity
                    self.save()

    def clear(self):
        """Clear entire cart"""
        if self.user:
            # User is logged in - clear database storage
            CartItem.objects.filter(user=self.user).delete()
        else:
            # Anonymous user - clear session storage
            self.cart = {}
            self.save()

    def save(self):
        """Save cart to session (for anonymous users only)"""
        self.session['cart'] = self.cart
        self.session.modified = True

    def __iter__(self):
        """Iterate over cart items"""
        if self.user:
            # User is logged in - iterate over database items
            cart_items = CartItem.objects.filter(user=self.user)
            for cart_item in cart_items:
                yield {
                    'product': cart_item.product,
                    'quantity': cart_item.quantity,
                    'price': str(cart_item.product.price),
                    'total_price': cart_item.total_price
                }
        else:
            # Anonymous user - iterate over session items
            product_ids = self.cart.keys()
            products = Product.objects.filter(id__in=product_ids)
            
            for product in products:
                self.cart[str(product.id)]['product'] = product
            
            for item in self.cart.values():
                # Calculate total price for this item
                item['total_price'] = float(item['price']) * item['quantity']
                yield item

    def __len__(self):
        """Return total number of items in cart"""
        if self.user:
            # User is logged in - count database items
            return sum(item.quantity for item in CartItem.objects.filter(user=self.user))
        else:
            # Anonymous user - count session items
            return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calculate total price of all items in cart"""
        if self.user:
            # User is logged in - calculate from database
            return sum(item.total_price for item in CartItem.objects.filter(user=self.user))
        else:
            # Anonymous user - calculate from session
            return sum(
                float(item['price']) * item['quantity'] 
                for item in self.cart.values()
            )

    def get_total_items(self):
        """Get total number of items in cart"""
        return self.__len__()
