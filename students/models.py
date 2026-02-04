from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('graduated', 'Graduated'),
        ('dropped', 'Dropped Out'),
    )
    
    # Link to User model
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Personal Information
    admission_number = models.CharField(max_length=20, unique=True)
    national_id = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    county = models.CharField(max_length=50, default='Kitui')
    sub_county = models.CharField(max_length=50)
    ward = models.CharField(max_length=50, blank=True)
    phone_number_alternative = models.CharField(max_length=15, blank=True)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=15)
    emergency_contact_relationship = models.CharField(max_length=50)
    
    # Academic Information
    year_of_admission = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )
    current_class = models.ForeignKey('courses.Class', on_delete=models.SET_NULL, 
                                      null=True, blank=True, related_name='students')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, 
                               null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_boarding = models.BooleanField(default=False)
    has_special_needs = models.BooleanField(default=False)
    special_needs_description = models.TextField(blank=True)
    
    # Guardian/Parent Information
    parent_name = models.CharField(max_length=100, blank=True)
    parent_phone = models.CharField(max_length=15, blank=True)
    parent_email = models.EmailField(blank=True)
    parent_occupation = models.CharField(max_length=100, blank=True)
    
    # Documents
    profile_picture = models.ImageField(upload_to='student_profiles/', blank=True, null=True)
    id_copy = models.FileField(upload_to='student_documents/id_cards/', blank=True, null=True)
    birth_certificate = models.FileField(upload_to='student_documents/birth_certs/', blank=True, null=True)
    kcpe_certificate = models.FileField(upload_to='student_documents/kcpe/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_attendance_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.admission_number} - {self.user.get_full_name() or self.user.username}"
    
    class Meta:
        ordering = ['admission_number']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
    
    def save(self, *args, **kwargs):
        # Auto-generate admission number if not provided
        if not self.admission_number:
            from django.utils import timezone
            year = timezone.now().year
            last_student = Student.objects.filter(
                admission_number__startswith=f'TVET{year}'
            ).order_by('admission_number').last()
            
            if last_student:
                last_num = int(last_student.admission_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.admission_number = f'TVET{year}{new_num:04d}'
        
        super().save(*args, **kwargs)

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    class_enrolled = models.ForeignKey('courses.Class', on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    enrollment_type = models.CharField(max_length=20, choices=[
        ('regular', 'Regular'),
        ('evening', 'Evening'),
        ('weekend', 'Weekend'),
        ('distance', 'Distance Learning'),
    ], default='regular')
    is_active = models.BooleanField(default=True)
    completion_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.class_enrolled.class_code}"
    
    class Meta:
        ordering = ['-enrollment_date']
        unique_together = ['student', 'class_enrolled']

class AcademicRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='academic_records')
    module_code = models.CharField(max_length=20)
    module_name = models.CharField(max_length=200)
    grade = models.CharField(max_length=2, choices=[
        ('A', 'A - Excellent'),
        ('B', 'B - Good'),
        ('C', 'C - Average'),
        ('D', 'D - Below Average'),
        ('E', 'E - Poor'),
        ('F', 'F - Fail'),
    ])
    score = models.DecimalField(max_digits=5, decimal_places=2, 
                                validators=[MinValueValidator(0), MaxValueValidator(100)])
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    academic_year = models.CharField(max_length=20)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.module_code}: {self.grade}"
    
    class Meta:
        ordering = ['-academic_year', 'semester', 'module_code']