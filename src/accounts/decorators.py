from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Decorator that requires the user to be an admin.
    Redirects to dashboard with error message if user is not an admin.
    Superusers automatically have admin access.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('accounts:login')
        
        # Superusers automatically have admin access
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Check if user has profile and is admin
        if not hasattr(request.user, 'profile') or not request.user.profile.is_admin:
            messages.error(request, 'You do not have permission to access this page. Admin access required.')
            return redirect('products:product_list')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
