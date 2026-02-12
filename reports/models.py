# reports/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class ReportTemplate(models.Model):
    """Predefined report templates"""
    REPORT_TYPE_CHOICES = (
        ('attendance_summary', 'Attendance Summary'),
        ('student_attendance', 'Student Attendance Report'),
        ('class_attendance', 'Class Attendance Report'),
        ('instructor_report', 'Instructor Report'),
        ('department_report', 'Department Report'),
        ('monthly_summary', 'Monthly Summary'),
        ('custom', 'Custom Report'),
    )
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, help_text="JSON configuration for report parameters")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class GeneratedReport(models.Model):
    """Store generated reports"""
    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    )
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    report_type = models.CharField(max_length=50, choices=ReportTemplate.REPORT_TYPE_CHOICES)
    report_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Report parameters
    parameters = models.JSONField(default=dict)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Generated data
    data = models.JSONField(default=dict, help_text="Report data in JSON format")
    summary = models.JSONField(default=dict, help_text="Summary statistics")
    
    # File information
    file_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    file_path = models.FileField(upload_to='reports/', null=True, blank=True)
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    
    # Generation info
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Status
    is_ready = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.report_name} - {self.generated_at.date()}"

class DashboardWidget(models.Model):
    """Dashboard widgets configuration"""
    WIDGET_TYPE_CHOICES = (
        ('attendance_chart', 'Attendance Chart'),
        ('student_stats', 'Student Statistics'),
        ('class_stats', 'Class Statistics'),
        ('instructor_stats', 'Instructor Statistics'),
        ('recent_activity', 'Recent Activity'),
        ('calendar', 'Calendar'),
        ('quick_links', 'Quick Links'),
    )
    
    CHART_TYPE_CHOICES = (
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('radar', 'Radar Chart'),
    )
    
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=50, choices=WIDGET_TYPE_CHOICES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPE_CHOICES, blank=True, null=True)
    description = models.TextField(blank=True)
    
    # Configuration
    configuration = models.JSONField(default=dict)
    refresh_interval = models.IntegerField(default=60, help_text="Refresh interval in minutes")
    width = models.IntegerField(default=6, validators=[MinValueValidator(1), MaxValueValidator(12)])
    height = models.IntegerField(default=300, help_text="Height in pixels")
    
    # Display settings
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Permissions
    user_types = models.JSONField(default=list, help_text="List of user types that can see this widget")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"

class ReportSchedule(models.Model):
    """Schedule automated report generation"""
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    )
    
    DAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    name = models.CharField(max_length=100)
    report_template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # Schedule details
    day_of_week = models.IntegerField(choices=DAY_CHOICES, null=True, blank=True)
    day_of_month = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(31)])
    hour = models.IntegerField(default=9, validators=[MinValueValidator(0), MaxValueValidator(23)])
    minute = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(59)])
    
    # Recipients
    email_recipients = models.JSONField(default=list, help_text="List of email addresses")
    notify_users = models.JSONField(default=list, help_text="List of user IDs to notify")
    
    # Output settings
    output_formats = models.JSONField(default=list, help_text="List of output formats")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.frequency})"