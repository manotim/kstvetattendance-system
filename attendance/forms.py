# attendance/forms.py
from django import forms
from django.utils import timezone
from .models import AttendanceSession, AttendanceRecord, ExcuseApplication
from students.models import Student
from courses.models import Class

class AttendanceSessionForm(forms.ModelForm):
    class Meta:
        model = AttendanceSession
        fields = ['class_session', 'session_date', 'start_time', 'end_time', 
                  'topic_covered', 'venue', 'attendance_method']
        widgets = {
            'session_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'topic_covered': forms.TextInput(attrs={'placeholder': 'Topic covered in this session'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.user_type == 'instructor':
            # Only show classes taught by this instructor
            self.fields['class_session'].queryset = Class.objects.filter(
                instructor=user,
                is_active=True
            )


class ManualAttendanceForm(forms.Form):
    """Form for manual attendance marking"""
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    status = forms.ChoiceField(
        choices=AttendanceRecord.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional remarks'})
    )
    is_excused = forms.BooleanField(required=False, label='Mark as excused')

class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance marking"""
    attendance_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

class QRAttendanceForm(forms.Form):
    """Form for QR code attendance"""
    qr_code = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Scan QR code or enter code manually'})
    )
    student_id = forms.CharField(
        max_length=20,
        widget=forms.HiddenInput(),
        required=False
    )

class ExcuseApplicationForm(forms.ModelForm):
    class Meta:
        model = ExcuseApplication
        fields = ['class_session', 'reason', 'start_date', 'end_date', 'supporting_document']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Provide detailed reason for absence'}),
        }
    
    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        if student:
            # Only show classes the student is enrolled in
            self.fields['class_session'].queryset = Class.objects.filter(
                enrollments__student=student,
                enrollments__is_active=True,
                is_active=True
            )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError('End date must be after start date.')
            
            if start_date < timezone.now().date():
                raise forms.ValidationError('Start date cannot be in the past for excuse applications.')
        
        return cleaned_data

class AttendanceReportFilterForm(forms.Form):
    """Form for filtering attendance reports"""
    DATE_RANGE_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('custom', 'Custom Range'),
    ]
    
    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        initial='this_week',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class_session = forms.ModelChoiceField(
        queryset=Class.objects.filter(is_active=True),
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(status='active'),
        required=False,
        empty_label="All Students",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(AttendanceRecord.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )