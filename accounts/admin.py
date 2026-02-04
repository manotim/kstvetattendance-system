from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['username', 'email', 'user_type', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['user_type', 'is_staff', 'is_active', 'department']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        ('Role Info', {'fields': ('user_type', 'department')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'password1', 'password2', 'first_name', 
                      'last_name', 'phone_number', 'department', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']

admin.site.register(User, CustomUserAdmin)