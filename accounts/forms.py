# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """
    Public registration form - only allows student registration
    Students are auto-approved
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow students to self-register
        self.fields['user_type'] = forms.CharField(widget=forms.HiddenInput(), initial='student')
        
        # Style password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Add help text
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['email'].help_text = 'Required. Enter a valid email address.'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.user_type = 'student'  # Force student type
        user.account_status = 'approved'  # Students are auto-approved
        user.is_active = True  # Students are active immediately
        
        if commit:
            user.save()
        return user


class InstructorRegistrationForm(UserCreationForm):
    """
    Admin-only form to create instructor accounts
    Instructors are auto-approved when created by admin
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'department', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'] = forms.CharField(widget=forms.HiddenInput(), initial='instructor')
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Add help text
        self.fields['username'].help_text = 'Required. 150 characters or fewer.'
        self.fields['department'].help_text = 'Optional: Department the instructor belongs to.'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.department = self.cleaned_data.get('department', '')
        user.user_type = 'instructor'
        user.account_status = 'approved'  # Auto-approved when created by admin
        user.is_active = True
        
        if commit:
            user.save()
        return user


class AdminRegistrationForm(UserCreationForm):
    """
    Superuser-only form to create admin accounts
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'] = forms.CharField(widget=forms.HiddenInput(), initial='admin')
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 'admin'
        user.account_status = 'approved'
        user.is_active = True
        user.is_staff = True  # Give staff access for admin panel
        
        if commit:
            user.save()
        return user


class HodRegistrationForm(UserCreationForm):
    """
    Admin-only form to create HOD accounts
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'department', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'] = forms.CharField(widget=forms.HiddenInput(), initial='hod')
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['department'].help_text = 'Required. Department the HOD manages.'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.department = self.cleaned_data.get('department', '')
        user.user_type = 'hod'
        user.account_status = 'approved'
        user.is_active = True
        
        if commit:
            user.save()
        return user


class RegistrarRegistrationForm(UserCreationForm):
    """
    Admin-only form to create Registrar accounts
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'] = forms.CharField(widget=forms.HiddenInput(), initial='registrar')
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.user_type = 'registrar'
        user.account_status = 'approved'
        user.is_active = True
        
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Form for editing existing users (admin use)
    """
    password = None  # Remove password field from change form
    
    class Meta:
        model = User
        fields = ('username', 'email', 'user_type', 'first_name', 'last_name',
                  'phone_number', 'department', 'profile_picture', 'account_status',
                  'is_active', 'is_staff')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'account_status': forms.Select(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserApprovalForm(forms.ModelForm):
    """
    Form for approving/rejecting pending users
    """
    class Meta:
        model = User
        fields = ['account_status', 'rejection_reason']
        widgets = {
            'account_status': forms.Select(attrs={'class': 'form-control'}),
            'rejection_reason': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Reason for rejection (required if rejecting)'
            }),
        }
        labels = {
            'account_status': 'Decision',
            'rejection_reason': 'Rejection Reason (if applicable)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit status choices to approval-related ones
        self.fields['account_status'].choices = [
            ('approved', 'Approve Account'),
            ('rejected', 'Reject Account'),
        ]
        self.fields['rejection_reason'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('account_status')
        reason = cleaned_data.get('rejection_reason')
        
        if status == 'rejected' and not reason:
            self.add_error('rejection_reason', 'Rejection reason is required when rejecting an account.')
        
        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for users to update their own profile
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class UserSearchForm(forms.Form):
    """
    Form for searching/filtering users in admin views
    """
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Search by username, email, or name...'
    }))
    user_type = forms.ChoiceField(required=False, choices=[('', 'All Types')] + list(User.USER_TYPE_CHOICES), 
                                  widget=forms.Select(attrs={'class': 'form-control'}))
    account_status = forms.ChoiceField(required=False, 
                                       choices=[('', 'All Status')] + list(User.ACCOUNT_STATUS_CHOICES),
                                       widget=forms.Select(attrs={'class': 'form-control'}))