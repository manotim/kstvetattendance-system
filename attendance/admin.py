from django.contrib import admin
from django.utils.html import format_html
from .models import AttendanceSession, AttendanceRecord, AttendanceSummary, ExcuseApplication

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'class_session', 'session_date', 'start_time', 'instructor', 
                   'attendance_method', 'status', 'total_present', 'total_absent']
    list_filter = ['status', 'attendance_method', 'session_date', 'class_session', 'instructor']
    search_fields = ['class_session__class_code', 'topic_covered', 'venue']
    readonly_fields = ['total_present', 'total_absent', 'total_late', 'created_at', 'updated_at', 'closed_at']
    list_per_page = 20
    
    fieldsets = (
        ('Session Details', {
            'fields': ('class_session', 'instructor', 'session_date', 'start_time', 'end_time')
        }),
        ('Session Information', {
            'fields': ('topic_covered', 'venue', 'attendance_method')
        }),
        ('QR Code Settings', {
            'fields': ('qr_code_data', 'qr_code_expiry'),
            'classes': ('collapse',)
        }),
        ('Status Management', {
            'fields': ('status', 'closed_at')
        }),
        ('Statistics', {
            'fields': ('total_present', 'total_absent', 'total_late'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def view_qr_code(self, obj):
        if obj.qr_code_data:
            return format_html('<a href="/attendance/qr/{}/" target="_blank">View QR Code</a>', obj.id)
        return "No QR Code"
    view_qr_code.short_description = 'QR Code'

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status', 'check_in_time', 'marked_by', 'is_excused']
    list_filter = ['status', 'is_excused', 'session__session_date', 'session__class_session']
    search_fields = ['student__admission_number', 'student__user__first_name', 
                     'student__user__last_name', 'session__class_session__class_code']
    readonly_fields = ['created_at', 'updated_at', 'mark_time']
    list_per_page = 30
    
    fieldsets = (
        ('Attendance Details', {
            'fields': ('session', 'student', 'status', 'marked_by')
        }),
        ('Time Tracking', {
            'fields': ('check_in_time', 'check_out_time', 'late_minutes')
        }),
        ('Excuse Information', {
            'fields': ('is_excused', 'excuse_reason', 'excuse_document')
        }),
        ('Additional Information', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'mark_time'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_session', 'period_type', 'period_start', 
                   'period_end', 'attendance_rate', 'punctuality_rate', 'trend']
    list_filter = ['period_type', 'trend', 'class_session', 'period_start']
    search_fields = ['student__admission_number', 'student__user__first_name', 
                     'student__user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20

@admin.register(ExcuseApplication)
class ExcuseApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_session', 'start_date', 'end_date', 'status', 'applied_at']
    list_filter = ['status', 'class_session', 'start_date']
    search_fields = ['student__admission_number', 'reason']
    readonly_fields = ['applied_at', 'updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('Application Details', {
            'fields': ('student', 'class_session', 'attendance_session')
        }),
        ('Excuse Period', {
            'fields': ('start_date', 'end_date', 'reason')
        }),
        ('Supporting Document', {
            'fields': ('supporting_document',),
            'classes': ('collapse',)
        }),
        ('Review Process', {
            'fields': ('status', 'reviewed_by', 'review_notes', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_applications', 'reject_applications']
    
    def approve_applications(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.approve(request.user, 'Bulk approved via admin')
        self.message_user(request, f"{queryset.count()} applications approved.")
    
    def reject_applications(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.reject(request.user, 'Bulk rejected via admin')
        self.message_user(request, f"{queryset.count()} applications rejected.")
    
    approve_applications.short_description = "Approve selected applications"
    reject_applications.short_description = "Reject selected applications"