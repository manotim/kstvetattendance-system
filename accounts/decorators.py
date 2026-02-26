# accounts/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def approved_user_required(view_func):
    """Decorator to check if user account is approved"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.account_status != 'approved':
                messages.error(
                    request, 
                    'Your account is pending approval. Please wait for an administrator to approve your account.'
                )
                return redirect('logout')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_or_approved_instructor_required(view_func):
    """Decorator for views that need admin or approved instructor"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.account_status != 'approved':
                messages.error(request, 'Your account needs approval to access this page.')
                return redirect('dashboard')
            
            if request.user.user_type not in ['admin', 'instructor'] and not request.user.is_superuser:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view