"""
Enhanced business rules for cart operations with flash sale pricing.
These functions implement core business logic with dual pricing calls for consistency.
"""

from decimal import Decimal
from products.services import current_effective_price


def validate_product_for_cart(product_active, product_name):
    """
    Validate that a product is available for adding to cart.
    
    Args:
        product_active (bool): Whether the product is active
        product_name (str): Name of the product for error messages
        
    Returns:
        bool: True if product is valid for cart
        
    Raises:
        ValueError: If product is not available for purchase
    """
    if not product_active:
        raise ValueError(f"Product {product_name} is not available for purchase")
    return True


def validate_quantity_limit(quantity, available_stock, product_name):
    """
    Validate that the requested quantity doesn't exceed available stock.
    
    Args:
        quantity (int): Requested quantity
        available_stock (int): Available stock quantity
        product_name (str): Name of the product for error messages
        
    Returns:
        bool: True if quantity is valid
        
    Raises:
        ValueError: If quantity exceeds available stock
    """
    if quantity > available_stock:
        raise ValueError(f"Cannot add {quantity} {product_name}(s). Only {available_stock} available in stock.")
    return True


def validate_cart_update(quantity, available_stock, product_name):
    """
    Validate cart update operations.
    
    Args:
        quantity (int): Requested quantity
        available_stock (int): Available stock quantity
        product_name (str): Name of the product for error messages
        
    Returns:
        bool: True if update is valid
        
    Raises:
        ValueError: If update violates business rules
    """
    if quantity > available_stock:
        raise ValueError(f"Cannot update quantity to {quantity}. Only {available_stock} {product_name}(s) available in stock.")
    if quantity < 0:
        raise ValueError(f"Quantity cannot be negative")
    return True


def calculate_cart_total(items):
    """
    Calculate total price for cart items using effective pricing.
    This ensures consistent pricing between add-to-cart and checkout.
    
    Args:
        items (list): List of items with 'product' and 'quantity' keys
        
    Returns:
        Decimal: Total price using effective pricing
    """
    total = Decimal('0.00')
    for item in items:
        product = item['product']
        quantity = item['quantity']
        effective_price = current_effective_price(product)
        total += effective_price * quantity
    return total


def calculate_item_total(product, quantity):
    """
    Calculate total price for a single cart item using effective pricing.
    
    Args:
        product: Product instance
        quantity (int): Quantity
        
    Returns:
        Decimal: Total price for the item using effective pricing
    """
    effective_price = current_effective_price(product)
    return effective_price * quantity
