# students/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def instructor_required(view_func):
    """
    Decorator to allow access only to instructors and admins
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Allow superusers, admins, and instructors
        if request.user.is_superuser or request.user.user_type in ['admin', 'instructor']:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "You don't have permission to access this page.")
        raise PermissionDenied
    
    return _wrapped_view

def instructor_can_manage_class(view_func):
    """
    Decorator to check if instructor can manage a specific class
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Allow superusers and admins
        if request.user.is_superuser or request.user.user_type == 'admin':
            return view_func(request, *args, **kwargs)
        
        # For instructors, check if they are assigned to this class
        if request.user.user_type == 'instructor':
            class_id = kwargs.get('class_id')
            if class_id:
                # Check if instructor is assigned to this class
                from courses.models import Class
                try:
                    class_obj = Class.objects.get(pk=class_id)
                    # Assuming you have a relationship between instructor and class
                    # This could be through a many-to-many field or foreign key
                    if class_obj.instructor == request.user or request.user in class_obj.instructors.all():
                        return view_func(request, *args, **kwargs)
                except Class.DoesNotExist:
                    pass
            
            messages.error(request, "You don't have permission to manage this class.")
            raise PermissionDenied
        
        raise PermissionDenied
    
    return _wrapped_view