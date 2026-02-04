from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Enrollment, AcademicRecord

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'full_name', 'course', 'status', 'county', 'created_at']
    list_filter = ['status', 'gender', 'course', 'county', 'year_of_admission']
    search_fields = ['admission_number', 'user__first_name', 'user__last_name', 
                     'user__username', 'national_id']
    readonly_fields = ['admission_number', 'created_at', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'admission_number', 'national_id', 
                      'date_of_birth', 'gender', 'profile_picture')
        }),
        ('Contact Information', {
            'fields': ('address', 'county', 'sub_county', 'ward', 
                      'phone_number_alternative')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 
                      'emergency_contact_relationship')
        }),
        ('Parent/Guardian Information', {
            'fields': ('parent_name', 'parent_phone', 'parent_email', 'parent_occupation')
        }),
        ('Academic Information', {
            'fields': ('year_of_admission', 'course', 'current_class')
        }),
        ('Status & Additional Info', {
            'fields': ('status', 'is_boarding', 'has_special_needs', 
                      'special_needs_description')
        }),
        ('Documents', {
            'fields': ('id_copy', 'birth_certificate', 'kcpe_certificate'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_attendance_date'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = 'Full Name'
    
    list_per_page = 20

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'class_enrolled', 'enrollment_date', 'is_active']
    list_filter = ['is_active', 'enrollment_type', 'enrollment_date', 'course']
    search_fields = ['student__admission_number', 'student__user__first_name', 
                     'student__user__last_name', 'class_enrolled__class_code']
    autocomplete_fields = ['student', 'course', 'class_enrolled']
    list_per_page = 20

@admin.register(AcademicRecord)
class AcademicRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'module_code', 'module_name', 'grade', 'score', 'semester', 'academic_year']
    list_filter = ['academic_year', 'semester', 'grade']
    search_fields = ['student__admission_number', 'module_code', 'module_name']
    autocomplete_fields = ['student']
    list_per_page = 20