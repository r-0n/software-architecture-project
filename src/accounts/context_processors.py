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
