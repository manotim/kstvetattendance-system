# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'System Administrator'),
        ('instructor', 'Instructor/Lecturer'),
        ('student', 'Student'),
        ('registrar', 'Registrar'),
        ('hod', 'Head of Department'),
    )
    
    ACCOUNT_STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    # Approval fields
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_users')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"
    
    def approve(self, admin_user):
        """Approve this user account"""
        self.account_status = 'approved'
        self.approved_by = admin_user
        self.approved_at = timezone.now()
        self.is_active = True
        self.save()
    
    def reject(self, admin_user, reason):
        """Reject this user account"""
        self.account_status = 'rejected'
        self.approved_by = admin_user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.is_active = False
        self.save()
    
    def suspend(self, admin_user, reason):
        """Suspend this user account"""
        self.account_status = 'suspended'
        self.approved_by = admin_user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.is_active = False
        self.save()
    
    @property
    def needs_approval(self):
        """Check if user needs approval"""
        return self.account_status == 'pending' and self.user_type in ['admin', 'instructor', 'registrar', 'hod']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        permissions = [
            ('approve_users', 'Can approve user accounts'),
            ('manage_users', 'Can manage all users'),
        ]