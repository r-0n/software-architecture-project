"""
Enhanced pricing services for flash sale system.
Supports dual pricing calls at add-to-cart and checkout for consistency.
"""
from decimal import Decimal
from django.utils import timezone
from .models import Product


def is_flash_sale_active(product: Product, now=None) -> bool:
    """
    Check if a product is currently in an active flash sale window.
    
    Args:
        product: Product instance to check
        now: Optional datetime to use instead of current time (for testing)
    
    Returns:
        bool: True if flash sale is active, False otherwise
    """
    now = now if now is not None else timezone.now()
    
    return (
        product.flash_sale_enabled and
        product.flash_sale_price is not None and
        product.flash_sale_starts_at and
        product.flash_sale_ends_at and
        product.flash_sale_starts_at <= now <= product.flash_sale_ends_at
    )


def current_effective_price(product: Product, now=None) -> Decimal:
    """
    Get the current effective price for a product.
    Returns flash sale price if active, otherwise regular price.
    
    Args:
        product: Product instance
        now: Optional datetime to use instead of current time (for testing)
    
    Returns:
        Decimal: The effective price to charge
    """
    if is_flash_sale_active(product, now):
        return product.flash_sale_price
    return product.price


def get_price_at_time(product: Product, target_time) -> Decimal:
    """
    Get what the price would be at a specific time.
    Useful for validating price consistency between add-to-cart and checkout.
    
    Args:
        product: Product instance
        target_time: datetime to check price for
    
    Returns:
        Decimal: The price that would be effective at the target time
    """
    if (
        product.flash_sale_enabled and
        product.flash_sale_price is not None and
        product.flash_sale_starts_at and
        product.flash_sale_ends_at and
        product.flash_sale_starts_at <= target_time <= product.flash_sale_ends_at
    ):
        return product.flash_sale_price
    return product.price


def validate_price_consistency(product: Product, add_to_cart_time, checkout_time, expected_price: Decimal) -> bool:
    """
    Validate that the price hasn't changed between add-to-cart and checkout.
    This prevents stale pricing issues.
    
    Args:
        product: Product instance
        add_to_cart_time: When the item was added to cart
        checkout_time: When checkout is happening
        expected_price: The price that was shown at add-to-cart
    
    Returns:
        bool: True if price is consistent, False if it changed
    """
    add_to_cart_price = get_price_at_time(product, add_to_cart_time)
    checkout_price = get_price_at_time(product, checkout_time)
    
    return (
        add_to_cart_price == expected_price and
        checkout_price == expected_price
    )
