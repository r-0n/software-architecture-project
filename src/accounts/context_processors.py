def user_admin_status(request):
    """
    Add user admin status to template context
    """
    if request.user.is_authenticated:
        # Superusers automatically have admin access
        if request.user.is_superuser:
            return {'user_is_admin': True}
        
        # Check if user has profile and is admin
        if hasattr(request.user, 'profile'):
            return {'user_is_admin': request.user.profile.is_admin}
    
    return {'user_is_admin': False}


def cart_context(request):
    """
    Add cart information to template context
    """
    if request.user.is_authenticated:
        from cart.models import Cart
        cart = Cart(request)
        return {
            'cart_total_items': cart.get_total_items(),
            'cart_total_price': cart.get_total_price(),
        }
    
    return {
        'cart_total_items': 0,
        'cart_total_price': 0,
    }