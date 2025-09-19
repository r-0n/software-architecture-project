# ADR-003: Cart Storage Strategy

## Status
**Accepted**

## Context

The retail management system requires a shopping cart functionality that supports both authenticated users and anonymous visitors. The cart needs to handle:

- Product addition, removal, and quantity updates
- Stock validation and inventory checking
- Price calculations and totals
- Persistence across browser sessions
- Seamless transition from anonymous to authenticated state
- Real-time inventory validation

Key requirements include:
- Support for anonymous users (no account required)
- Persistent cart for authenticated users
- Stock validation to prevent overselling
- Session management for anonymous users
- Database persistence for authenticated users
- Cart migration when users log in

## Decision

We chose a **Hybrid Session/Database Storage Strategy** for cart management.

### Technical Implementation
- **Anonymous Users**: Cart data stored in Django session
- **Authenticated Users**: Cart data stored in database (`CartItem` model)
- **Seamless Transition**: Automatic migration from session to database on login
- **Unified Interface**: Single `Cart` class handles both storage methods transparently

### Implementation Details
```python
class Cart:
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
        if self.user:
            # Authenticated user - use database storage
            try:
                cart_item = CartItem.objects.get(product=product, user=self.user)
                cart_item.quantity += quantity
                cart_item.save()
            except CartItem.DoesNotExist:
                CartItem.objects.create(product=product, user=self.user, quantity=quantity)
        else:
            # Anonymous user - use session storage
            product_id = str(product.id)
            if product_id in self.cart:
                self.cart[product_id]['quantity'] += quantity
            else:
                self.cart[product_id] = {
                    'quantity': quantity,
                    'price': str(product.price)
                }
            self.save()
```

### Database Model
```python
class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'session_key', 'user']
```

## Consequences

### Positive Consequences
- **User Experience**: Seamless cart experience for both anonymous and authenticated users
- **Flexibility**: Supports both user types without requiring account creation
- **Persistence**: Authenticated users retain cart across sessions and devices
- **Performance**: Session storage is fast for anonymous users
- **Data Integrity**: Database storage provides ACID compliance for authenticated users
- **Migration Support**: Automatic cart migration when users log in
- **Stock Validation**: Real-time inventory checking for both storage types
- **Unified Interface**: Single API for cart operations regardless of user state

### Negative Consequences
- **Complexity**: Dual storage logic increases code complexity
- **Data Consistency**: Potential for session/database inconsistencies
- **Storage Overhead**: Both session and database storage required
- **Migration Complexity**: Cart migration logic adds complexity
- **Testing Complexity**: Need to test both storage paths
- **Session Limitations**: Session storage has size and persistence limitations

### Trade-offs
- **User Experience vs. Complexity**: Prioritized user experience over implementation simplicity
- **Flexibility vs. Performance**: Chose flexibility over single-storage optimization
- **Persistence vs. Overhead**: Accepted storage overhead for better user experience

## Alternatives Considered

### Database-Only Storage
- **Pros**: Consistent storage, ACID compliance, persistent across sessions
- **Cons**: Requires user registration, no anonymous cart support, slower for simple operations
- **Decision**: Rejected due to poor user experience for anonymous users

### Session-Only Storage
- **Pros**: Simple implementation, fast performance, no database overhead
- **Cons**: No persistence across sessions, limited storage size, no multi-device support
- **Decision**: Rejected due to poor user experience for authenticated users

### Cookie-Based Storage
- **Pros**: Client-side storage, no server overhead, works across sessions
- **Cons**: Size limitations, security concerns, no server-side validation
- **Decision**: Rejected due to security and size limitations

### External Cache (Redis)
- **Pros**: Fast performance, flexible storage, session-like behavior
- **Cons**: Additional infrastructure, complexity, cost
- **Decision**: Rejected due to infrastructure complexity and cost

### Hybrid with Cart Migration
- **Pros**: Best user experience, supports both user types, automatic migration
- **Cons**: Implementation complexity, dual storage overhead
- **Decision**: Accepted despite complexity due to superior user experience

## Implementation Examples

### Anonymous User Cart
```python
# Session-based storage for anonymous users
cart = Cart(request)
cart.add(product, quantity=2)
# Data stored in: request.session['cart'] = {'1': {'quantity': 2, 'price': '10.00'}}
```

### Authenticated User Cart
```python
# Database storage for authenticated users
cart = Cart(request)
cart.add(product, quantity=2)
# Data stored in: CartItem.objects.create(product=product, user=user, quantity=2)
```

### Cart Migration
```python
# Automatic migration when user logs in
def login_user(request, user):
    # Migrate session cart to database
    session_cart = request.session.get('cart', {})
    for product_id, item_data in session_cart.items():
        product = Product.objects.get(id=product_id)
        CartItem.objects.create(
            product=product,
            user=user,
            quantity=item_data['quantity']
        )
    request.session['cart'] = {}  # Clear session cart
```