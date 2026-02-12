# students/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from .models import Student, Enrollment, AcademicRecord

class StudentRegistrationForm(UserCreationForm):
    # User fields
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    # Student fields
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    gender = forms.ChoiceField(
        choices=Student.GENDER_CHOICES,
        widget=forms.RadioSelect
    )
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    county = forms.CharField(initial='Kitui')
    sub_county = forms.CharField(required=True)
    national_id = forms.CharField(required=False)
    
    # Emergency Contact
    emergency_contact_name = forms.CharField(required=True)
    emergency_contact_phone = forms.CharField(required=True)
    emergency_contact_relationship = forms.CharField(required=True)
    
    # Academic Info
    course = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=True
    )
    year_of_admission = forms.IntegerField(
        min_value=2000,
        max_value=2100,
        initial=2024
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                  'date_of_birth', 'gender', 'address', 'county', 'sub_county', 'national_id',
                  'emergency_contact_name', 'emergency_contact_phone', 
                  'emergency_contact_relationship', 'course', 'year_of_admission')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from courses.models import Course
        self.fields['course'].queryset = Course.objects.filter(is_active=True)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            # Create Student profile
            student = Student.objects.create(
                user=user,
                date_of_birth=self.cleaned_data['date_of_birth'],
                gender=self.cleaned_data['gender'],
                address=self.cleaned_data['address'],
                county=self.cleaned_data['county'],
                sub_county=self.cleaned_data['sub_county'],
                national_id=self.cleaned_data['national_id'],
                emergency_contact_name=self.cleaned_data['emergency_contact_name'],
                emergency_contact_phone=self.cleaned_data['emergency_contact_phone'],
                emergency_contact_relationship=self.cleaned_data['emergency_contact_relationship'],
                course=self.cleaned_data['course'],
                year_of_admission=self.cleaned_data['year_of_admission']
            )
        
        return user

class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'national_id', 'date_of_birth', 'gender', 'address', 
            'county', 'sub_county', 'ward', 'phone_number_alternative',
            'emergency_contact_name', 'emergency_contact_phone', 
            'emergency_contact_relationship',
            'parent_name', 'parent_phone', 'parent_email', 'parent_occupation',
            'is_boarding', 'has_special_needs', 'special_needs_description',
            'status', 'profile_picture'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'special_needs_description': forms.Textarea(attrs={'rows': 3}),
        }

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['course', 'class_enrolled', 'enrollment_type', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        if student:
            self.fields['class_enrolled'].queryset = self.fields['class_enrolled'].queryset.filter(
                course=student.course
        )

class BulkStudentImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with student data. Required columns: first_name,last_name,email,date_of_birth,gender,address'
    )