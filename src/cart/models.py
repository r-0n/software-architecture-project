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
    """Shopping cart utility class for session-based cart management"""
    
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
        """Add product to cart"""
        product_id = str(product.id)
        
        if product_id in self.cart:
            self.cart[product_id]['quantity'] += quantity
        else:
            self.cart[product_id] = {
                'quantity': quantity,
                'price': str(product.price)
            }
        
        self.save()

    def remove(self, product):
        """Remove product from cart"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def update(self, product, quantity):
        """Update product quantity in cart"""
        product_id = str(product.id)
        if product_id in self.cart:
            if quantity <= 0:
                self.remove(product)
            else:
                self.cart[product_id]['quantity'] = quantity
                self.save()

    def clear(self):
        """Clear entire cart"""
        self.cart = {}
        self.save()

    def save(self):
        """Save cart to session"""
        self.session['cart'] = self.cart
        self.session.modified = True

    def __iter__(self):
        """Iterate over cart items"""
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
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calculate total price of all items in cart"""
        return sum(
            float(item['price']) * item['quantity'] 
            for item in self.cart.values()
        )

    def get_total_items(self):
        """Get total number of items in cart"""
        return sum(item['quantity'] for item in self.cart.values())
