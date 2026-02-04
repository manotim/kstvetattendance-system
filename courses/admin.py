from django.contrib import admin
from .models import Course, Class

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'level', 'department', 'is_active']
    list_filter = ['level', 'department', 'is_active']
    search_fields = ['code', 'name', 'description']
    list_per_page = 20

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['class_code', 'name', 'course', 'instructor', 'academic_year', 'semester', 'is_active']
    list_filter = ['academic_year', 'semester', 'course', 'is_active']
    search_fields = ['class_code', 'name', 'venue']
    list_per_page = 20
    autocomplete_fields = ['course', 'instructor']