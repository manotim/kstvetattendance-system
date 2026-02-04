from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class AttendanceSession(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    ATTENDANCE_METHOD_CHOICES = (
        ('qr_code', 'QR Code'),
        ('manual', 'Manual Entry'),
        ('biometric', 'Biometric'),
        ('mobile', 'Mobile App'),
    )
    
    class_session = models.ForeignKey('courses.Class', on_delete=models.CASCADE, related_name='attendance_sessions')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                   limit_choices_to={'user_type': 'instructor'})
    session_date = models.DateField(default=timezone.now)
    start_time = models.TimeField()
    end_time = models.TimeField()
    topic_covered = models.CharField(max_length=200)
    venue = models.CharField(max_length=100)
    
    # Attendance settings
    attendance_method = models.CharField(max_length=20, choices=ATTENDANCE_METHOD_CHOICES, default='manual')
    qr_code_data = models.CharField(max_length=255, blank=True, null=True)
    qr_code_expiry = models.DateTimeField(blank=True, null=True)
    
    # Session management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    total_late = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.class_session.class_code} - {self.session_date} {self.start_time}"
    
    class Meta:
        ordering = ['-session_date', '-start_time']
        unique_together = ['class_session', 'session_date', 'start_time']
    
    def save(self, *args, **kwargs):
        # Generate QR code data if using QR attendance
        if self.attendance_method == 'qr_code' and not self.qr_code_data:
            import secrets
            self.qr_code_data = f"ATTENDANCE_{self.class_session.id}_{secrets.token_hex(16)}"
            self.qr_code_expiry = timezone.now() + timezone.timedelta(hours=2)
        
        super().save(*args, **kwargs)
    
    def calculate_stats(self):
        """Calculate attendance statistics for this session"""
        records = self.attendance_records.all()
        self.total_present = records.filter(status='present').count()
        self.total_absent = records.filter(status='absent').count()
        self.total_late = records.filter(status='late').count()
        self.save()
    
    def is_active(self):
        """Check if attendance session is currently active"""
        if self.status != 'ongoing':
            return False
        
        now = timezone.now()
        session_datetime = timezone.make_aware(
            timezone.datetime.combine(self.session_date, self.end_time)
        )
        return now <= session_datetime
    
    def close_session(self):
        """Close the attendance session"""
        self.status = 'completed'
        self.closed_at = timezone.now()
        self.calculate_stats()
        self.save()

class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('half_day', 'Half Day'),
    )
    
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_records')
    
    # Attendance details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    mark_time = models.DateTimeField(auto_now_add=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, related_name='marked_attendances')
    
    # Additional information
    is_excused = models.BooleanField(default=False)
    excuse_reason = models.TextField(blank=True)
    excuse_document = models.FileField(upload_to='excuse_documents/', blank=True, null=True)
    remarks = models.TextField(blank=True)
    
    # For late arrivals
    late_minutes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-mark_time']
        unique_together = ['session', 'student']
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.session} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Update student's last attendance date
        if self.status == 'present' and self.check_in_time:
            self.student.last_attendance_date = self.check_in_time.date()
            self.student.save()
        
        # Calculate late minutes if status is late
        if self.status == 'late' and self.check_in_time and self.session.start_time:
            from datetime import datetime, date
            session_start = datetime.combine(self.session.session_date, self.session.start_time)
            check_in = self.check_in_time
            if check_in.tzinfo:
                session_start = timezone.make_aware(session_start)
            self.late_minutes = max(0, int((check_in - session_start).total_seconds() / 60))
        
        super().save(*args, **kwargs)
        
        # Update session statistics
        self.session.calculate_stats()

class AttendanceSummary(models.Model):
    """Monthly/Weekly attendance summary for reporting"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_summaries')
    class_session = models.ForeignKey('courses.Class', on_delete=models.CASCADE, related_name='attendance_summaries')
    
    # Period
    period_type = models.CharField(max_length=20, choices=[('weekly', 'Weekly'), ('monthly', 'Monthly')])
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Statistics
    total_sessions = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    excused_count = models.IntegerField(default=0)
    
    # Calculated fields
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,
                                         validators=[MinValueValidator(0), MaxValueValidator(100)])
    punctuality_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,
                                          validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Trends
    previous_period_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    trend = models.CharField(max_length=10, choices=[('up', 'Improving'), ('down', 'Declining'), ('stable', 'Stable')])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_end', '-period_start']
        unique_together = ['student', 'class_session', 'period_type', 'period_start']
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.period_type} {self.period_start}"
    
    def calculate_rates(self):
        """Calculate attendance and punctuality rates"""
        if self.total_sessions > 0:
            self.attendance_rate = (self.present_count / self.total_sessions) * 100
            if self.present_count > 0:
                self.punctuality_rate = ((self.present_count - self.late_count) / self.present_count) * 100
            else:
                self.punctuality_rate = 0
        self.save()

class ExcuseApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='excuse_applications')
    class_session = models.ForeignKey('courses.Class', on_delete=models.CASCADE, related_name='excuse_applications')
    attendance_session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, 
                                          related_name='excuse_applications', null=True, blank=True)
    
    # Excuse details
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    supporting_document = models.FileField(upload_to='excuse_applications/', blank=True, null=True)
    
    # Review process
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='reviewed_excuses')
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.start_date} to {self.end_date}"
    
    def approve(self, reviewer, notes=''):
        """Approve the excuse application"""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()
        
        # Update attendance records for the period
        from django.db.models import Q
        records = AttendanceRecord.objects.filter(
            student=self.student,
            session__class_session=self.class_session,
            session__session_date__range=[self.start_date, self.end_date]
        )
        
        for record in records:
            record.is_excused = True
            record.excuse_reason = self.reason
            record.save()
    
    def reject(self, reviewer, notes=''):
        """Reject the excuse application"""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()