"""
Enhanced throttling system for flash sales.
Implements granular throttling by user+product to prevent SKU-specific abuse.
"""
from django.core.cache import cache
from django.conf import settings
import time
from typing import Tuple


def allow_checkout(user_or_ip: str, product_id: int = None) -> Tuple[bool, str, int]:
    """
    Check if checkout is allowed for a user/IP and optionally a specific product.
    Implements granular throttling to prevent single user from draining one SKU.
    
    Args:
        user_or_ip: User ID (if authenticated) or IP address
        product_id: Optional product ID for granular throttling
    
    Returns:
        Tuple[bool, str, int]: (allowed, reason, retry_after_seconds)
    """
    now = time.time()
    
    # Per-user/IP global throttle
    user_key = f'throttle_user_{user_or_ip}'
    user_requests = cache.get(user_key, [])
    user_requests = [t for t in user_requests if t > now - settings.FLASH_ORDER_THROTTLE_PER_USER_SECONDS]
    
    if len(user_requests) >= settings.FLASH_ORDER_THROTTLE_PER_USER:
        retry_after = int(settings.FLASH_ORDER_THROTTLE_PER_USER_SECONDS - (now - user_requests[0]))
        return False, f"Too many requests. Please try again in {retry_after} seconds.", retry_after
    
    # Per-user+product throttle (if product_id provided)
    if product_id:
        product_key = f'throttle_user_product_{user_or_ip}_{product_id}'
        product_requests = cache.get(product_key, [])
        product_requests = [t for t in product_requests if t > now - settings.FLASH_ORDER_THROTTLE_PER_USER_SECONDS]
        
        if len(product_requests) >= settings.FLASH_ORDER_THROTTLE_PER_USER:
            retry_after = int(settings.FLASH_ORDER_THROTTLE_PER_USER_SECONDS - (now - product_requests[0]))
            return False, f"Too many requests for this product. Please try again in {retry_after} seconds.", retry_after
        
        product_requests.append(now)
        cache.set(product_key, product_requests, settings.FLASH_ORDER_THROTTLE_PER_USER_SECONDS)
    
    # Global system throttle
    global_key = 'throttle_global'
    global_requests = cache.get(global_key, [])
    global_requests = [t for t in global_requests if t > now - settings.FLASH_ORDER_THROTTLE_GLOBAL_SECONDS]
    
    if len(global_requests) >= settings.FLASH_ORDER_THROTTLE_GLOBAL:
        retry_after = int(settings.FLASH_ORDER_THROTTLE_GLOBAL_SECONDS - (now - global_requests[0]))
        return False, f"System is under heavy load. Please try again in {retry_after} seconds.", retry_after
    
    # Record the requests
    user_requests.append(now)
    cache.set(user_key, user_requests, settings.FLASH_ORDER_THROTTLE_PER_USER_SECONDS)
    
    global_requests.append(now)
    cache.set(global_key, global_requests, settings.FLASH_ORDER_THROTTLE_GLOBAL_SECONDS)
    
    return True, "Allowed", 0


def get_throttle_status(user_or_ip: str, product_id: int = None) -> dict:
    """
    Get current throttle status for debugging/monitoring.
    
    Args:
        user_or_ip: User ID or IP address
        product_id: Optional product ID
    
    Returns:
        dict: Throttle status information
    """
    now = time.time()
    
    # User throttle status
    user_key = f'throttle_user_{user_or_ip}'
    user_requests = cache.get(user_key, [])
    user_requests = [t for t in user_requests if t > now - settings.FLASH_ORDER_THROTTLE_PER_USER_SECONDS]
    
    status = {
        'user_requests': len(user_requests),
        'user_limit': settings.FLASH_ORDER_THROTTLE_PER_USER,
        'user_remaining': max(0, settings.FLASH_ORDER_THROTTLE_PER_USER - len(user_requests)),
    }
    
    # Product-specific throttle status
    if product_id:
        product_key = f'throttle_user_product_{user_or_ip}_{product_id}'
        product_requests = cache.get(product_key, [])
        product_requests = [t for t in product_requests if t > now - settings.FLASH_ORDER_THROTTLE_PER_USER_SECONDS]
        
        status.update({
            'product_requests': len(product_requests),
            'product_limit': settings.FLASH_ORDER_THROTTLE_PER_USER,
            'product_remaining': max(0, settings.FLASH_ORDER_THROTTLE_PER_USER - len(product_requests)),
        })
    
    # Global throttle status
    global_key = 'throttle_global'
    global_requests = cache.get(global_key, [])
    global_requests = [t for t in global_requests if t > now - settings.FLASH_ORDER_THROTTLE_GLOBAL_SECONDS]
    
    status.update({
        'global_requests': len(global_requests),
        'global_limit': settings.FLASH_ORDER_THROTTLE_GLOBAL,
        'global_remaining': max(0, settings.FLASH_ORDER_THROTTLE_GLOBAL - len(global_requests)),
    })
    
    return status


def clear_throttle(user_or_ip: str, product_id: int = None):
    """
    Clear throttle for a user/IP (useful for testing or admin override).
    
    Args:
        user_or_ip: User ID or IP address
        product_id: Optional product ID to clear specific product throttle
    """
    user_key = f'throttle_user_{user_or_ip}'
    cache.delete(user_key)
    
    if product_id:
        product_key = f'throttle_user_product_{user_or_ip}_{product_id}'
        cache.delete(product_key)
