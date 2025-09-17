"""
Business rules for cart operations in the retail management system.
These functions implement core business logic that can be tested and reused.
"""

from decimal import Decimal


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
    Calculate total price for cart items.
    
    Args:
        items (list): List of items with 'price' and 'quantity' keys
        
    Returns:
        Decimal: Total price
    """
    return sum(Decimal(str(item['price'])) * item['quantity'] for item in items)


def calculate_item_total(price, quantity):
    """
    Calculate total price for a single cart item.
    
    Args:
        price (Decimal): Unit price
        quantity (int): Quantity
        
    Returns:
        Decimal: Total price for the item
    """
    return price * quantity
