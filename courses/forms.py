from django import forms
from .models import Course, Class
from accounts.models import User

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'description', 'level', 'duration_months', 'department', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['course', 'class_code', 'name', 'instructor', 'academic_year', 
                 'semester', 'start_date', 'end_date', 'meeting_days', 
                 'meeting_time', 'venue', 'max_students', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'meeting_days': forms.TextInput(attrs={'placeholder': 'e.g., Monday, Wednesday, Friday'}),
            'meeting_time': forms.TextInput(attrs={'placeholder': 'e.g., 10:00 AM - 12:00 PM'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active courses
        self.fields['course'].queryset = Course.objects.filter(is_active=True)
        # Only show instructors as choices for instructor field
        self.fields['instructor'].queryset = User.objects.filter(user_type='instructor', is_active=True)

class ClassEnrollmentForm(forms.Form):
    """Form for enrolling students in a class"""
    students = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        class_obj = kwargs.pop('class_obj', None)
        super().__init__(*args, **kwargs)
        
        if class_obj:
            # Get students not already enrolled in this class
            from students.models import Student
            enrolled_student_ids = class_obj.enrollments.filter(is_active=True).values_list('student_id', flat=True)
            self.fields['students'].queryset = Student.objects.filter(
                status='active',
                course=class_obj.course
            ).exclude(id__in=enrolled_student_ids)