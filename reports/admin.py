from django.contrib import admin
from django.utils.html import format_html
from .models import ReportTemplate, GeneratedReport, DashboardWidget, ReportSchedule

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['report_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'report_type', 'description')
        }),
        ('Configuration', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_by')
        }),
    )

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['report_name', 'report_type', 'file_format', 'generated_by', 
                   'generated_at', 'is_ready', 'file_size_display']
    list_filter = ['report_type', 'file_format', 'is_ready', 'generated_at']
    search_fields = ['report_name', 'description']
    readonly_fields = ['generated_at', 'file_size']
    list_per_page = 20
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_name', 'report_type', 'description', 'template')
        }),
        ('Parameters', {
            'fields': ('parameters', 'start_date', 'end_date'),
            'classes': ('collapse',)
        }),
        ('Generated Data', {
            'fields': ('data', 'summary'),
            'classes': ('collapse',)
        }),
        ('File Information', {
            'fields': ('file_format', 'file_path', 'file_size')
        }),
        ('Status', {
            'fields': ('is_ready', 'is_archived', 'generated_by', 'generated_at')
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'File Size'

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'widget_type', 'chart_type', 'is_active', 'display_order', 'width']
    list_filter = ['widget_type', 'is_active']
    search_fields = ['name', 'description']
    list_per_page = 20
    
    fieldsets = (
        ('Widget Information', {
            'fields': ('name', 'widget_type', 'chart_type', 'description')
        }),
        ('Configuration', {
            'fields': ('configuration', 'refresh_interval', 'width', 'height')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order', 'user_types')
        }),
    )

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_template', 'frequency', 'is_active', 'last_run', 'next_run']
    list_filter = ['frequency', 'is_active']
    search_fields = ['name']
    list_per_page = 20
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('name', 'report_template', 'frequency')
        }),
        ('Schedule Details', {
            'fields': ('day_of_week', 'day_of_month', 'hour', 'minute')
        }),
        ('Recipients', {
            'fields': ('email_recipients', 'notify_users')
        }),
        ('Output Settings', {
            'fields': ('output_formats',)
        }),
        ('Status', {
            'fields': ('is_active', 'last_run', 'next_run', 'created_by')
        }),
    )