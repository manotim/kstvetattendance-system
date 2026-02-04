from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import ReportTemplate, GeneratedReport, DashboardWidget, ReportSchedule

class ReportFilterForm(forms.Form):
    """Base form for report filtering"""
    DATE_RANGE_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'),
        ('last_quarter', 'Last Quarter'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year'),
        ('custom', 'Custom Range'),
    ]
    
    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        initial='this_month',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_date_range'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'id_start_date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'id_end_date'
        })
    )

class AttendanceReportForm(ReportFilterForm):
    """Form for attendance reports"""
    report_type = forms.ChoiceField(
        choices=[
            ('summary', 'Summary Report'),
            ('detailed', 'Detailed Report'),
            ('trends', 'Trend Analysis'),
            ('comparison', 'Comparison Report'),
        ],
        initial='summary',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    group_by = forms.ChoiceField(
        choices=[
            ('day', 'By Day'),
            ('week', 'By Week'),
            ('month', 'By Month'),
            ('class', 'By Class'),
            ('instructor', 'By Instructor'),
            ('student', 'By Student'),
        ],
        initial='day',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    include_charts = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class StudentAttendanceReportForm(ReportFilterForm):
    """Form for student attendance reports"""
    student = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Students",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    class_session = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    include_excuses = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_trends = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from students.models import Student
        from courses.models import Class
        self.fields['student'].queryset = Student.objects.filter(status='active')
        self.fields['class_session'].queryset = Class.objects.filter(is_active=True)

class ClassAttendanceReportForm(ReportFilterForm):
    """Form for class attendance reports"""
    class_session = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    instructor = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Instructors",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    include_comparison = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_student_list = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from courses.models import Class
        from accounts.models import User
        self.fields['class_session'].queryset = Class.objects.filter(is_active=True)
        self.fields['instructor'].queryset = User.objects.filter(user_type='instructor', is_active=True)

class ExportReportForm(forms.Form):
    """Form for exporting reports"""
    FORMAT_CHOICES = [
        ('pdf', 'PDF Document'),
        ('excel', 'Excel Spreadsheet'),
        ('csv', 'CSV File'),
        ('html', 'HTML Report'),
    ]
    
    export_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial='pdf',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    include_charts = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_summary = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class DashboardWidgetForm(forms.ModelForm):
    class Meta:
        model = DashboardWidget
        fields = ['name', 'widget_type', 'chart_type', 'description', 
                 'configuration', 'refresh_interval', 'width', 'height',
                 'is_active', 'display_order', 'user_types']
        widgets = {
            'configuration': forms.Textarea(attrs={'rows': 4, 'placeholder': 'JSON configuration'}),
            'user_types': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

class ReportScheduleForm(forms.ModelForm):
    class Meta:
        model = ReportSchedule
        fields = ['name', 'report_template', 'frequency', 'day_of_week', 
                 'day_of_month', 'hour', 'minute', 'email_recipients',
                 'notify_users', 'output_formats', 'is_active']
        widgets = {
            'email_recipients': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter emails separated by commas'}),
            'notify_users': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'output_formats': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['report_template'].queryset = ReportTemplate.objects.filter(is_active=True)