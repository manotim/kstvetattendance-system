from django.db import models
from django.conf import settings

class Course(models.Model):
    LEVEL_CHOICES = (
        ('certificate', 'Certificate'),
        ('diploma', 'Diploma'),
        ('artisan', 'Artisan'),
        ('craft', 'Craft'),
    )
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='certificate')
    duration_months = models.IntegerField(default=12)
    department = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        ordering = ['code']

class Class(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes')
    class_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, limit_choices_to={'user_type': 'instructor'})
    academic_year = models.CharField(max_length=20)
    semester = models.IntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    meeting_days = models.CharField(max_length=100, help_text="e.g., Monday, Wednesday, Friday")
    meeting_time = models.CharField(max_length=50, help_text="e.g., 10:00 AM - 12:00 PM")
    venue = models.CharField(max_length=100)
    max_students = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.class_code} - {self.name}"
    
    class Meta:
        verbose_name_plural = 'Classes'
        ordering = ['-academic_year', 'semester', 'class_code']