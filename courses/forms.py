# courses/forms.py
from django import forms
from .models import Course, Class
from accounts.models import User

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'description', 'level', 'duration_months', 'department', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['class_code', 'name', 'course', 'instructor', 'academic_year', 
                 'semester', 'start_date', 'end_date', 'meeting_days', 'meeting_time',
                 'venue', 'max_students', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'meeting_days': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Monday, Wednesday, Friday'
            }),
            'meeting_time': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., 10:00 AM - 12:00 PM'
            }),
            'class_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024-2025'
            }),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show instructors in the dropdown
        self.fields['instructor'].queryset = User.objects.filter(
            user_type='instructor', 
            is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['instructor'].label_from_instance = lambda obj: obj.get_full_name()
        self.fields['instructor'].widget.attrs.update({'class': 'form-control'})
        self.fields['instructor'].required = False
        self.fields['instructor'].help_text = "Leave blank if no instructor assigned yet"
        
        # Add form-control class to remaining fields
        self.fields['course'].widget.attrs.update({'class': 'form-control'})
        
        # Add help text
        self.fields['meeting_days'].help_text = "Days when the class meets"
        self.fields['meeting_time'].help_text = "Time when the class meets"

class ClassEnrollmentForm(forms.Form):
    """Form for enrolling students in a class"""
    students = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2',
            'style': 'width: 100%',
            'data-placeholder': 'Select students to enroll...'
        }),
        required=True,
        help_text="Hold Ctrl/Cmd to select multiple students"
    )
    
    enrollment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        }),
        required=False,
        help_text="Leave blank to use today's date"
    )
    
    def __init__(self, *args, **kwargs):
        class_obj = kwargs.pop('class_obj', None)
        super().__init__(*args, **kwargs)
        
        if class_obj:
            from students.models import Student
            # Get students not already enrolled in this class
            enrolled_student_ids = class_obj.enrollments.filter(
                is_active=True
            ).values_list('student_id', flat=True)
            
            # Get available students (active and with matching course)
            self.fields['students'].queryset = Student.objects.filter(
                status='active',
                course=class_obj.course
            ).exclude(id__in=enrolled_student_ids).select_related('user')
            
            # Custom label for students
            self.fields['students'].label_from_instance = lambda obj: f"{obj.admission_number} - {obj.user.get_full_name()}"
            
            # Set default enrollment date
            from django.utils import timezone
            if not self.initial.get('enrollment_date'):
                self.initial['enrollment_date'] = timezone.now().date()